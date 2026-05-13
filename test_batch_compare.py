"""
批量测试：从 data/xlsx_records.json 读取行号↔图片的正确对应关系，
调用 Agent 分析每张图片，输出结果到 data/comparison_result.json
"""
import asyncio
import base64
import io
import json
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from app.agents.repair_agent import get_agent
from app.core.config import settings

RECORDS_JSON = Path(__file__).parent / "data" / "xlsx_records.json"
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_JSON = DATA_DIR / "comparison_result.json"
MAX_IMAGE_SIZE = settings.MAX_IMAGE_SIZE


def load_xlsx_records() -> list[dict]:
    """从 xlsx_records.json 读取行号、原因、图片路径"""
    with open(RECORDS_JSON, encoding="utf-8") as f:
        return json.load(f)


def encode_image_file(image_path: Path, max_size: int = MAX_IMAGE_SIZE) -> str:
    """将本地图片压缩并编码为 Base64 Data URI"""
    image = Image.open(image_path)
    if image.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    w, h = image.size
    if w > max_size or h > max_size:
        if w > h:
            image = image.resize((max_size, int(h * max_size / w)), Image.Resampling.LANCZOS)
        else:
            image = image.resize((int(w * max_size / h), max_size), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85, optimize=True)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"


async def run():
    records = load_xlsx_records()
    agent = get_agent()
    results = []

    for record in records:
        row_num = record["row_number"]
        reason = record["original_reason"]
        img_file = record.get("image_filename") or ""

        if not img_file:
            print(f"[row={row_num}] 无图片，跳过 (原因: {reason or '无'})")
            continue

        img_path = Path(record["image_path"]) if record.get("image_path") else DATA_DIR / img_file
        if not img_path.exists():
            print(f"[SKIP] 图片文件不存在: {img_file}")
            continue

        print(f"[row={row_num}] {img_file} | 原因: {reason or '(无)'} — 分析中...")
        t0 = time.time()
        try:
            base64_image = encode_image_file(img_path)
            result = await agent.analyze(base64_image)
            ai_reply = result.get("reply", "")
            observation = result.get("observation", "")
        except Exception as e:
            ai_reply = f"ERROR: {e}"
            observation = ""
        elapsed = round(time.time() - t0, 2)

        results.append({
            "row_number": row_num,
            "image": img_file,
            "original_reason": reason,
            "observation": observation,
            "ai_reply": ai_reply,
            "processing_time_s": elapsed,
        })
        print(f"  -> {ai_reply}  ({elapsed}s)")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    errors = sum(1 for r in results if r["ai_reply"].startswith("ERROR"))
    print(f"\n完成！共处理 {len(results)} 条，其中 {errors} 条失败，结果已写入 {OUTPUT_JSON}")


if __name__ == "__main__":
    asyncio.run(run())
