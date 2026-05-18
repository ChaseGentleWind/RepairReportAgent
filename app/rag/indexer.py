"""
离线索引脚本：解析 SOP PDF → 语义分块 → DashScope Embedding → ChromaDB

用法：
    python -m app.rag.indexer              # 增量（跳过已存在的文档）
    python -m app.rag.indexer --rebuild    # 清空重建
"""

import argparse
import os
import re
import time
import httpx
import pdfplumber
from chromadb import PersistentClient

# 需要向量化的 PDF（A 类：含设施巡检标准）
TARGET_PDFS = [
    "QHKC-WI-MT-01 基础设施管理作业指导书  (A1)-20250801.pdf",
    "QHKC-WI-MT-10 集中供冷系统作业指导书  (A1)-20250801.pdf",
    "QHKC-WI-MT-11 电梯管理作业指导书  (A1)-20250801.pdf",
    "QHKC-WI-MT-12 水景系统管理作业指导书  (A1)-20250801.pdf",
]

PDF_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "三级保养类作业指导书"
)

COLLECTION_NAME = "sop_chunks"

# 任意层级编号行：5.4.3 / 4.2 / 3 等
ITEM_RE = re.compile(r"^(\d+(\.\d+){0,3})\s+(\S.{2,})")

# PDF 页眉/页脚特征词，命中则跳过该行
BOILERPLATE_PATTERNS = [
    re.compile(p) for p in [
        r"前海嘉里中心",
        r"文件编号",
        r"版\s*本\s*号",
        r"页\s*码\s*\d+/\d+",
        r"生效日期",
        r"QHKC-WI-MT-\d+",
        r"^\d+/\d+$",          # 纯页码
    ]
]

# 流程图页特征
FLOWCHART_KEYWORDS = ["判断", "开始", "结束", "→", "↓", "↑"]


def _is_boilerplate(line: str) -> bool:
    return any(p.search(line) for p in BOILERPLATE_PATTERNS)


def _is_flowchart_page(text: str) -> bool:
    if not text or len(text.strip()) < 30:
        return True
    return sum(1 for kw in FLOWCHART_KEYWORDS if kw in text) >= 3


def _extract_all_lines(pdf_path: str) -> list[str]:
    """提取所有页的文本行，过滤页眉/页脚和流程图页。"""
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw = page.extract_text() or ""
            if _is_flowchart_page(raw):
                continue
            for line in raw.splitlines():
                line = line.strip()
                if not line or _is_boilerplate(line):
                    continue
                lines.append(line)
    return lines


def extract_chunks(pdf_path: str) -> list[dict]:
    """从单个 PDF 提取语义分块，每个编号条目独立成块。"""
    doc_id = os.path.basename(pdf_path)
    lines = _extract_all_lines(pdf_path)

    chunks: list[dict] = []
    current_num = ""
    current_title = ""
    current_body: list[str] = []

    def flush():
        body = " ".join(current_body).strip()
        full_text = f"{current_title} {body}".strip()
        if len(full_text) > 20:
            fault_kws = ["破损", "污迹", "锈蚀", "故障", "异常", "脱落", "松动", "渗漏", "堵塞", "缺失", "变形"]
            hints = [kw for kw in fault_kws if kw in full_text]
            parts = [f"条款：{current_num}", f"内容：{full_text}"]
            if hints:
                parts.append(f"故障特征：{'、'.join(hints)}")
            parts.append(f"来源：{doc_id}")
            text = "  ".join(parts)
            chunk_id = f"{doc_id}::{current_num}::{current_title[:40]}"
            chunks.append({"id": chunk_id, "text": text, "source": doc_id})
        current_body.clear()

    for line in lines:
        m = ITEM_RE.match(line)
        if m:
            flush()
            current_num = m.group(1)
            current_title = line
            current_body = []
        else:
            current_body.append(line)

    flush()
    return chunks


def _embed_batch(texts: list[str], api_key: str, model: str) -> list[list[float]]:
    """调用 DashScope Embedding API（OpenAI 兼容端点），每批最多 10 条。"""
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    all_vecs: list[list[float]] = []
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = httpx.post(
            f"{base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": batch},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        data.sort(key=lambda e: e["index"])
        all_vecs.extend([e["embedding"] for e in data])
        if i + batch_size < len(texts):
            time.sleep(0.3)
    return all_vecs


def build_index(rebuild: bool = False):
    from app.core.config import settings

    db_path = os.path.abspath(settings.CHROMA_DB_PATH)
    os.makedirs(db_path, exist_ok=True)

    client = PersistentClient(path=db_path)

    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[indexer] 已清空集合 {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    existing_ids: set[str] = set(collection.get(include=[])["ids"])
    print(f"[indexer] 现有文档数：{len(existing_ids)}")

    all_chunks: list[dict] = []
    for pdf_name in TARGET_PDFS:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            print(f"[indexer] 跳过（文件不存在）：{pdf_name}")
            continue
        chunks = extract_chunks(pdf_path)
        new_chunks = [c for c in chunks if c["id"] not in existing_ids]
        print(f"[indexer] {pdf_name}: 提取 {len(chunks)} 块，新增 {len(new_chunks)} 块")
        all_chunks.extend(new_chunks)

    if not all_chunks:
        print("[indexer] 无新增内容，索引已是最新。")
        return

    texts = [c["text"] for c in all_chunks]
    print(f"[indexer] 开始向量化 {len(texts)} 个分块...")
    vectors = _embed_batch(texts, settings.DASHSCOPE_API_KEY, settings.EMBEDDING_MODEL_NAME)

    collection.add(
        ids=[c["id"] for c in all_chunks],
        embeddings=vectors,
        documents=texts,
        metadatas=[{"source": c["source"]} for c in all_chunks],
    )
    print(f"[indexer] 完成！ChromaDB 现有文档总数：{collection.count()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="清空并重建索引")
    args = parser.parse_args()
    build_index(rebuild=args.rebuild)
