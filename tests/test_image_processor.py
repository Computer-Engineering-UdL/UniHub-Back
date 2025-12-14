import io
from unittest.mock import patch

import pytest
from PIL import Image

from app.domains.file.image_processor import ImageProcessor


class TestImageProcessor:
    """Tests for ImageProcessor service."""

    @pytest.fixture
    def large_jpeg_image(self):
        """Create a large JPEG image for testing."""
        img = Image.new("RGB", (3000, 2000), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=100)
        return buffer.getvalue()

    @pytest.fixture
    def small_jpeg_image(self):
        """Create a small JPEG image for testing."""
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=100)
        return buffer.getvalue()

    @pytest.fixture
    def png_with_transparency(self):
        """Create a PNG image with transparency."""
        img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_can_process_jpeg(self):
        """Test that JPEG images can be processed."""
        assert ImageProcessor.can_process("image/jpeg") is True

    def test_can_process_png(self):
        """Test that PNG images can be processed."""
        assert ImageProcessor.can_process("image/png") is True

    def test_can_process_webp(self):
        """Test that WebP images can be processed."""
        assert ImageProcessor.can_process("image/webp") is True

    def test_cannot_process_gif(self):
        """Test that GIF images are skipped (to preserve animation)."""
        assert ImageProcessor.can_process("image/gif") is False
        assert ImageProcessor.should_skip("image/gif") is True

    def test_cannot_process_text(self):
        """Test that text files cannot be processed."""
        assert ImageProcessor.can_process("text/plain") is False

    def test_compression_reduces_size(self, large_jpeg_image):
        """Test that compression reduces file size."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = True

            processed, content_type = ImageProcessor.process_image(large_jpeg_image, "image/jpeg")

            assert len(processed) < len(large_jpeg_image)
            assert content_type == "image/webp"

    def test_resize_large_image(self, large_jpeg_image):
        """Test that large images are resized."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = False

            processed, _ = ImageProcessor.process_image(large_jpeg_image, "image/jpeg")

            # Verify the output image dimensions
            output_img = Image.open(io.BytesIO(processed))
            width, height = output_img.size
            assert width <= 1920
            assert height <= 1080

    def test_small_image_not_resized(self, small_jpeg_image):
        """Test that small images are not resized."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = False

            processed, _ = ImageProcessor.process_image(small_jpeg_image, "image/jpeg")

            output_img = Image.open(io.BytesIO(processed))
            width, height = output_img.size
            assert width == 100
            assert height == 100

    def test_webp_conversion(self, small_jpeg_image):
        """Test conversion to WebP format."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = True

            processed, content_type = ImageProcessor.process_image(small_jpeg_image, "image/jpeg")

            assert content_type == "image/webp"
            # Verify it's actually a WebP image
            output_img = Image.open(io.BytesIO(processed))
            assert output_img.format == "WEBP"

    def test_compression_disabled(self, large_jpeg_image):
        """Test that compression can be disabled."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = False

            processed, content_type = ImageProcessor.process_image(large_jpeg_image, "image/jpeg")

            assert processed == large_jpeg_image
            assert content_type == "image/jpeg"

    def test_preserve_original_format(self, small_jpeg_image):
        """Test preserving original format when WebP conversion disabled."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = False

            processed, content_type = ImageProcessor.process_image(small_jpeg_image, "image/jpeg")

            assert content_type == "image/jpeg"
            output_img = Image.open(io.BytesIO(processed))
            assert output_img.format == "JPEG"

    def test_png_transparency_preserved_in_webp(self, png_with_transparency):
        """Test that PNG transparency is preserved when converting to WebP."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = True

            processed, content_type = ImageProcessor.process_image(png_with_transparency, "image/png")

            assert content_type == "image/webp"
            output_img = Image.open(io.BytesIO(processed))
            # WebP supports transparency
            assert output_img.mode in ("RGBA", "LA", "PA")

    def test_aspect_ratio_preserved(self, large_jpeg_image):
        """Test that aspect ratio is preserved during resize."""
        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = False

            # Original is 3000x2000 (3:2 ratio)
            processed, _ = ImageProcessor.process_image(large_jpeg_image, "image/jpeg")

            output_img = Image.open(io.BytesIO(processed))
            width, height = output_img.size

            # Should maintain 3:2 ratio (1620x1080 after resize to fit 1920x1080)
            original_ratio = 3000 / 2000
            new_ratio = width / height
            assert abs(original_ratio - new_ratio) < 0.01

    def test_gif_passthrough(self):
        """Test that GIF images are passed through unchanged."""
        # Create a simple GIF
        img = Image.new("P", (100, 100), color=1)
        buffer = io.BytesIO()
        img.save(buffer, format="GIF")
        gif_content = buffer.getvalue()

        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True

            processed, content_type = ImageProcessor.process_image(gif_content, "image/gif")

            assert processed == gif_content
            assert content_type == "image/gif"

    def test_invalid_image_passthrough(self):
        """Test that invalid image data is passed through unchanged."""
        invalid_content = b"not an image"

        with patch("app.domains.file.image_processor.settings") as mock_settings:
            mock_settings.IMAGE_COMPRESSION_ENABLED = True
            mock_settings.IMAGE_COMPRESSION_QUALITY = 80
            mock_settings.IMAGE_MAX_WIDTH = 1920
            mock_settings.IMAGE_MAX_HEIGHT = 1080
            mock_settings.IMAGE_CONVERT_TO_WEBP = True

            processed, content_type = ImageProcessor.process_image(invalid_content, "image/jpeg")

            # Should return original on error
            assert processed == invalid_content
            assert content_type == "image/jpeg"
