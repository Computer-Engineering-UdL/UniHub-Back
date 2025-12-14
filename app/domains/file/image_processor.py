import io
from typing import Tuple

from PIL import Image

from app.core.config import settings


class ImageProcessor:
    """
    Service to compress and resize images before storage.
    Reduces file sizes significantly while maintaining acceptable quality.
    """

    PROCESSABLE_TYPES = {"image/jpeg", "image/png", "image/webp"}

    SKIP_TYPES = {"image/gif"}

    @classmethod
    def can_process(cls, content_type: str) -> bool:
        """Check if the content type can be processed."""
        return content_type in cls.PROCESSABLE_TYPES

    @classmethod
    def should_skip(cls, content_type: str) -> bool:
        """Check if the content type should be skipped (e.g., animated GIFs)."""
        return content_type in cls.SKIP_TYPES

    @classmethod
    def process_image(
        cls,
        content: bytes,
        content_type: str,
    ) -> Tuple[bytes, str]:
        """
        Process an image: resize if needed and compress.

        Args:
            content: Original image bytes
            content_type: MIME type of the image

        Returns:
            Tuple of (processed_bytes, new_content_type)
        """
        if not settings.IMAGE_COMPRESSION_ENABLED:
            return content, content_type

        if cls.should_skip(content_type):
            return content, content_type

        if not cls.can_process(content_type):
            return content, content_type

        try:
            image = Image.open(io.BytesIO(content))

            if image.mode in ("RGBA", "P") and settings.IMAGE_CONVERT_TO_WEBP:
                pass
            elif image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            image = cls._resize_if_needed(image)

            output_bytes, output_type = cls._compress(image, content_type)

            return output_bytes, output_type

        except Exception:
            return content, content_type

    @classmethod
    def _resize_if_needed(cls, image: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds maximum dimensions while preserving aspect ratio.
        """
        max_width = settings.IMAGE_MAX_WIDTH
        max_height = settings.IMAGE_MAX_HEIGHT

        width, height = image.size

        if width <= max_width and height <= max_height:
            return image

        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @classmethod
    def _compress(
        cls,
        image: Image.Image,
        original_content_type: str,
    ) -> Tuple[bytes, str]:
        """
        Compress the image with quality settings.

        Returns:
            Tuple of (compressed_bytes, content_type)
        """
        output = io.BytesIO()
        quality = settings.IMAGE_COMPRESSION_QUALITY

        if settings.IMAGE_CONVERT_TO_WEBP:
            if image.mode == "RGBA":
                image.save(output, format="WEBP", quality=quality, method=6)
            else:
                image.save(output, format="WEBP", quality=quality, method=6)
            output_type = "image/webp"
        else:
            if original_content_type == "image/jpeg":
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(output, format="JPEG", quality=quality, optimize=True)
                output_type = "image/jpeg"
            elif original_content_type == "image/png":
                image.save(output, format="PNG", optimize=True)
                output_type = "image/png"
            elif original_content_type == "image/webp":
                image.save(output, format="WEBP", quality=quality, method=6)
                output_type = "image/webp"
            else:
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(output, format="JPEG", quality=quality, optimize=True)
                output_type = "image/jpeg"

        return output.getvalue(), output_type

    @classmethod
    def create_thumbnail(
        cls,
        content: bytes,
        content_type: str,
        max_width: int = 400,
        max_height: int = 300,
    ) -> Tuple[bytes, str]:
        """
        Create a thumbnail from an image for list views.

        Args:
            content: Original image bytes
            content_type: MIME type of the image
            max_width: Maximum thumbnail width (default 400px)
            max_height: Maximum thumbnail height (default 300px)

        Returns:
            Tuple of (thumbnail_bytes, content_type)
        """
        if not cls.can_process(content_type):
            return content, content_type

        try:
            image = Image.open(io.BytesIO(content))

            width, height = image.size
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            if image.mode in ("RGBA", "P"):
                pass
            elif image.mode != "RGB":
                image = image.convert("RGB")

            output = io.BytesIO()
            image.save(output, format="WEBP", quality=70, method=4)
            return output.getvalue(), "image/webp"

        except Exception:
            return content, content_type


image_processor = ImageProcessor()
