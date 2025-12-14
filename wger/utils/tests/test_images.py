# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

# Standard Library
import io
import tempfile
from unittest.mock import (
    MagicMock,
    patch,
)

# Django
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

# Third Party
from PIL import (
    Image,
    UnidentifiedImageError,
)

# wger
from wger.utils.images import (
    MAX_FILE_SIZE_MB,
    validate_image_static_no_animation,
)


class ValidateImageStaticNoAnimationTestCase(TestCase):
    """
    Unit tests for validate_image_static_no_animation validator
    """

    def create_test_image(self, format='JPEG', size=(100, 100), animated=False):
        """Helper to create a test image file"""
        img = Image.new('RGB', size, color='red')
        img_io = io.BytesIO()
        
        if format == 'JPEG':
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            return SimpleUploadedFile(
                'test.jpg',
                img_io.getvalue(),
                content_type='image/jpeg'
            )
        elif format == 'PNG':
            img.save(img_io, format='PNG')
            img_io.seek(0)
            return SimpleUploadedFile(
                'test.png',
                img_io.getvalue(),
                content_type='image/png'
            )
        elif format == 'WEBP':
            img.save(img_io, format='WEBP')
            img_io.seek(0)
            file_obj = SimpleUploadedFile(
                'test.webp',
                img_io.getvalue(),
                content_type='image/webp'
            )
            # Mock is_animated attribute for webp
            if animated:
                # For animated webp, we'll need to mock the PIL Image object
                pass
            return file_obj
        else:
            raise ValueError(f"Unsupported format: {format}")

    def test_valid_jpeg_image(self):
        """Test that valid JPEG images pass validation"""
        image_file = self.create_test_image(format='JPEG')
        try:
            validate_image_static_no_animation(image_file)
        except ValidationError:
            self.fail("validate_image_static_no_animation raised ValidationError for valid JPEG")

    def test_valid_png_image(self):
        """Test that valid PNG images pass validation"""
        image_file = self.create_test_image(format='PNG')
        try:
            validate_image_static_no_animation(image_file)
        except ValidationError:
            self.fail("validate_image_static_no_animation raised ValidationError for valid PNG")

    def test_valid_webp_image(self):
        """Test that valid static WEBP images pass validation"""
        image_file = self.create_test_image(format='WEBP')
        try:
            validate_image_static_no_animation(image_file)
        except ValidationError:
            self.fail("validate_image_static_no_animation raised ValidationError for valid WEBP")

    def test_file_too_large(self):
        """Test that files exceeding MAX_FILE_SIZE_MB raise ValidationError"""
        # Create a mock file that exceeds the size limit
        max_size_bytes = 1024 * 1024 * MAX_FILE_SIZE_MB
        large_file = MagicMock()
        large_file.size = max_size_bytes + 1
        large_file.open.return_value = None

        with self.assertRaises(ValidationError) as context:
            validate_image_static_no_animation(large_file)

        self.assertIn(f'{MAX_FILE_SIZE_MB}MB', str(context.exception))

    def test_file_exactly_at_limit(self):
        """Test that files exactly at the size limit pass validation"""
        image_file = self.create_test_image(format='JPEG')
        # Mock the size to be exactly at the limit
        max_size_bytes = 1024 * 1024 * MAX_FILE_SIZE_MB
        image_file.size = max_size_bytes
        try:
            validate_image_static_no_animation(image_file)
        except ValidationError as e:
            # Should not fail on size, but might fail on other checks
            if 'maximum image file size' in str(e):
                self.fail("File at exact size limit should pass validation")

    def test_invalid_image_file(self):
        """Test that invalid/non-image files raise ValidationError"""
        # Create a file that's not a valid image
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image file',
            content_type='text/plain'
        )

        with self.assertRaises(ValidationError) as context:
            validate_image_static_no_animation(invalid_file)

        self.assertIn('not a valid image', str(context.exception))

    def test_unsupported_format_gif(self):
        """Test that GIF format raises ValidationError"""
        # Create a GIF image (not in allowed formats)
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='GIF')
        img_io.seek(0)
        gif_file = SimpleUploadedFile(
            'test.gif',
            img_io.getvalue(),
            content_type='image/gif'
        )

        with self.assertRaises(ValidationError) as context:
            validate_image_static_no_animation(gif_file)

        self.assertIn('not supported', str(context.exception))
        self.assertIn('jpeg', str(context.exception).lower())

    def test_unsupported_format_bmp(self):
        """Test that BMP format raises ValidationError"""
        # Create a BMP image (not in allowed formats)
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        # PIL might not save BMP directly, so we'll mock it
        bmp_file = MagicMock()
        bmp_file.size = 1024  # Small size
        mock_img = MagicMock()
        mock_img.format = 'BMP'
        bmp_file.open.return_value = None

        with patch('wger.utils.images.Image.open', return_value=mock_img):
            with self.assertRaises(ValidationError) as context:
                validate_image_static_no_animation(bmp_file)

            self.assertIn('not supported', str(context.exception))

    def test_animated_webp_raises_error(self):
        """Test that animated WEBP images raise ValidationError"""
        webp_file = self.create_test_image(format='WEBP')
        webp_file.size = 1024  # Small size

        # Mock PIL Image to simulate animated webp
        mock_img = MagicMock()
        mock_img.format = 'WEBP'
        mock_img.is_animated = True

        with patch('wger.utils.images.Image.open', return_value=mock_img):
            with self.assertRaises(ValidationError) as context:
                validate_image_static_no_animation(webp_file)

            self.assertIn('Animated images are not supported', str(context.exception))

    def test_static_webp_passes(self):
        """Test that static WEBP images pass validation"""
        webp_file = self.create_test_image(format='WEBP')
        webp_file.size = 1024

        # Mock PIL Image to simulate static webp
        mock_img = MagicMock()
        mock_img.format = 'WEBP'
        # is_animated attribute doesn't exist or is False for static webp
        if hasattr(mock_img, 'is_animated'):
            mock_img.is_animated = False

        with patch('wger.utils.images.Image.open', return_value=mock_img):
            try:
                validate_image_static_no_animation(webp_file)
            except ValidationError as e:
                if 'Animated' in str(e):
                    self.fail("Static WEBP should pass validation")

    def test_jpeg_lowercase_format(self):
        """Test that JPEG format is handled correctly (case-insensitive)"""
        image_file = self.create_test_image(format='JPEG')
        image_file.size = 1024

        # Mock PIL Image to return lowercase format
        mock_img = MagicMock()
        mock_img.format = 'jpeg'  # lowercase

        with patch('wger.utils.images.Image.open', return_value=mock_img):
            try:
                validate_image_static_no_animation(image_file)
            except ValidationError as e:
                if 'not supported' in str(e):
                    self.fail("JPEG should be accepted in any case")

    def test_file_open_error(self):
        """Test handling of file open errors"""
        file_obj = MagicMock()
        file_obj.size = 1024
        file_obj.open.side_effect = IOError("Cannot open file")

        with self.assertRaises((ValidationError, IOError)):
            validate_image_static_no_animation(file_obj)

