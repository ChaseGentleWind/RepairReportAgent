import base64
import io
from typing import Tuple
from PIL import Image
from fastapi import UploadFile, HTTPException


async def process_and_encode_image(
    upload_file: UploadFile,
    max_size: int = 1024
) -> str:
    """
    处理上传的图片并转换为 Base64 Data URI

    Args:
        upload_file: FastAPI UploadFile 对象
        max_size: 图片长边最大尺寸（像素）

    Returns:
        Base64 编码的 Data URI 字符串，格式: data:image/jpeg;base64,...

    Raises:
        HTTPException: 图片处理失败时抛出异常
    """
    try:
        # 读取上传的文件内容
        contents = await upload_file.read()

        # 验证文件是否为空
        if not contents:
            raise HTTPException(status_code=400, detail="上传的文件为空")

        # 使用 Pillow 打开图片
        image = Image.open(io.BytesIO(contents))

        # 转换 RGBA 或 P 模式为 RGB（确保兼容性）
        if image.mode in ("RGBA", "P", "LA"):
            # 创建白色背景
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # 等比例压缩图片
        image = resize_image(image, max_size)

        # 将图片转换为 Base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85, optimize=True)
        img_bytes = buffered.getvalue()

        # 编码为 Base64
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        # 构造 Data URI
        data_uri = f"data:image/jpeg;base64,{img_base64}"

        return data_uri

    except Image.UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="无法识别的图片格式，请上传有效的图片文件（JPEG, PNG, WebP等）"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"图片处理失败: {str(e)}"
        )


def resize_image(image: Image.Image, max_size: int) -> Image.Image:
    """
    等比例压缩图片，保持长边不超过 max_size

    Args:
        image: PIL Image 对象
        max_size: 长边最大尺寸

    Returns:
        压缩后的 PIL Image 对象
    """
    width, height = image.size

    # 如果图片已经小于最大尺寸，直接返回
    if width <= max_size and height <= max_size:
        return image

    # 计算缩放比例
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    # 使用高质量的重采样算法
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return resized_image


def validate_image_file(upload_file: UploadFile) -> None:
    """
    验证上传的文件是否为有效的图片格式

    Args:
        upload_file: FastAPI UploadFile 对象

    Raises:
        HTTPException: 文件格式不支持时抛出异常
    """
    # 支持的 MIME 类型
    allowed_mime_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/tiff"
    }

    if upload_file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {upload_file.content_type}。"
                   f"支持的格式: JPEG, PNG, WebP, GIF, BMP, TIFF"
        )


async def get_image_info(upload_file: UploadFile) -> dict:
    """
    获取图片的基本信息（用于调试和日志）

    Args:
        upload_file: FastAPI UploadFile 对象

    Returns:
        包含图片信息的字典
    """
    try:
        contents = await upload_file.read()
        image = Image.open(io.BytesIO(contents))

        # 重置文件指针，以便后续读取
        await upload_file.seek(0)

        return {
            "filename": upload_file.filename,
            "content_type": upload_file.content_type,
            "size": len(contents),
            "width": image.size[0],
            "height": image.size[1],
            "format": image.format,
            "mode": image.mode
        }
    except Exception as e:
        return {
            "filename": upload_file.filename,
            "error": str(e)
        }
