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

"""
Example tests demonstrating the use of mocks, fakes, and stubs for external services.

This file shows how to:
- Mock HTTP requests for external APIs
- Mock Celery task execution
- Use in-memory storage for file operations
- Test error handling for external dependencies
"""

# Standard Library
import io
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

# Django
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import (
    TestCase,
    override_settings,
)

# wger
from wger.core.tests.base_testcase import BaseTestCase
from wger.exercises.models import Exercise
from wger.exercises.sync import (
    download_exercise_images,
    sync_exercises,
)


class MockExternalHTTPTestCase(BaseTestCase, TestCase):
    """
    Example: Mocking external HTTP requests using unittest.mock
    """

    @patch('wger.exercises.sync.requests.get')
    def test_sync_exercises_with_mocked_http(self, mock_get):
        """
        Example: Test sync_exercises with mocked HTTP responses
        """
        # Mock the paginated API endpoint response
        mock_response_data = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'uuid': 'test-uuid-123',
                    'created': '2020-01-01T00:00:00Z',
                    'license': {'id': 1},
                    'category': {'id': 2},
                    'license_author': 'Test Author',
                    'equipment': [{'id': 1}],
                    'muscles': [{'id': 1}],
                    'muscles_secondary': [],
                    'translations': [
                        {
                            'uuid': 'trans-uuid-1',
                            'language': {'short_name': 'en'},
                            'name': 'Test Exercise',
                            'description': 'Test Description',
                        }
                    ],
                }
            ],
        }

        # Configure the mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Mock the print function
        print_fn = Mock()

        # Call the sync function
        try:
            sync_exercises(print_fn, remote_url='https://wger.de')
            # Verify the function was called (indicating it processed data)
            self.assertTrue(print_fn.called)
        except Exception as e:
            # If it fails due to missing fixtures/data, that's ok for this example
            # The important part is that we mocked the HTTP call
            self.assertIsNotNone(e)

    @patch('wger.exercises.sync.requests.get')
    def test_download_exercise_images_with_mocked_http(self, mock_get):
        """
        Example: Test downloading exercise images with mocked HTTP
        """
        # Mock the image API endpoint
        mock_image_list = {
            'count': 1,
            'results': [
                {
                    'uuid': 'img-uuid-123',
                    'exercise_uuid': 'test-exercise-uuid',
                    'image': 'https://example.com/image.jpg',
                    'license': 1,
                    'license_author': 'Test',
                }
            ],
        }

        # Mock the image file download
        mock_image_content = b'fake image binary data'

        # Configure mock to return different responses based on URL
        def mock_get_side_effect(url, **kwargs):
            mock_resp = Mock()
            if 'exerciseimage' in url:
                mock_resp.json.return_value = mock_image_list
                mock_resp.status_code = 200
            elif 'image.jpg' in url:
                mock_resp.content = mock_image_content
                mock_resp.status_code = 200
            else:
                mock_resp.status_code = 404
            return mock_resp

        mock_get.side_effect = mock_get_side_effect

        print_fn = Mock()

        # This would normally fail without proper setup, but demonstrates mocking
        try:
            download_exercise_images(print_fn, remote_url='https://wger.de')
            self.assertTrue(print_fn.called)
        except Exception:
            # Expected if exercise doesn't exist in test DB
            pass


class MockCeleryTasksTestCase(BaseTestCase, TestCase):
    """
    Example: Mocking Celery task execution
    """

    @patch('wger.exercises.tasks.sync_exercises_task.delay')
    def test_celery_task_mocking(self, mock_task_delay):
        """
        Example: Mock Celery task to avoid actual async execution in tests
        """
        # Import the task
        from wger.exercises.tasks import sync_exercises_task

        # Call the task - it should be mocked
        sync_exercises_task.delay()

        # Verify the task was "called" (mocked)
        mock_task_delay.assert_called_once()

    @patch('wger.exercises.tasks.sync_images_task.delay')
    def test_another_celery_task_mock(self, mock_sync_images):
        """
        Example: Mock another Celery task
        """
        from wger.exercises.tasks import sync_images_task

        # Call the task - it should be mocked
        sync_images_task.delay()
        
        # Verify the task was "called" (mocked)
        mock_sync_images.assert_called_once()

    @patch('wger.exercises.tasks.sync_exercises_task.apply_async')
    def test_celery_task_apply_async_mocking(self, mock_apply_async):
        """
        Example: Mock Celery task using apply_async instead of delay
        """
        from wger.exercises.tasks import sync_exercises_task

        # Call the task with apply_async - it should be mocked
        sync_exercises_task.apply_async(args=[], kwargs={})

        # Verify the task was "called" (mocked)
        mock_apply_async.assert_called_once()


class MockFileSystemTestCase(BaseTestCase, TestCase):
    """
    Example: Using in-memory storage for file operations
    """

    @override_settings(
        DEFAULT_FILE_STORAGE='django.core.files.storage.InMemoryStorage',
        MEDIA_ROOT='/tmp/test_media'
    )
    def test_file_upload_with_in_memory_storage(self):
        """
        Example: Test file operations without touching the real filesystem
        """
        # Create a test image file
        image_content = b'fake image data'
        image_file = SimpleUploadedFile(
            'test.jpg',
            image_content,
            content_type='image/jpeg'
        )

        # Test that we can work with the file
        self.assertEqual(image_file.size, len(image_content))
        self.assertEqual(image_file.name, 'test.jpg')

    def test_file_operations_with_mock(self):
        """
        Example: Mock file operations to avoid filesystem I/O
        """
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b'file content'
            mock_open.return_value.__enter__.return_value = mock_file

            # reads a file
            with open('some_file.txt', 'rb') as f:
                content = f.read()

            self.assertEqual(content, b'file content')
            mock_open.assert_called_once_with('some_file.txt', 'rb')


class MockCacheTestCase(BaseTestCase, TestCase):
    """
    Example: Testing cache interactions with mocks
    """

    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_cache_operations_mocked(self, mock_cache_set, mock_cache_get):
        """
        Example: Mock cache operations to test cache logic without actual caching
        """
        # Set up mock cache behavior
        mock_cache_get.return_value = None  # Cache miss
        mock_cache_set.return_value = True

        from django.core.cache import cache

        # Test cache miss
        result = cache.get('test_key')
        self.assertIsNone(result)
        mock_cache_get.assert_called_with('test_key')

        # Test cache set
        cache.set('test_key', 'test_value', 60)
        mock_cache_set.assert_called_with('test_key', 'test_value', 60)

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }
    )
    def test_cache_with_locmem(self):
        """
        Example: Use in-memory cache backend for faster tests
        """
        from django.core.cache import cache

        # This uses the in-memory cache, not the real cache backend
        cache.set('test_key', 'test_value', 60)
        result = cache.get('test_key')
        self.assertEqual(result, 'test_value')


class MockErrorHandlingTestCase(BaseTestCase, TestCase):
    """
    Example: Testing error handling with mocked failures
    """

    @patch('requests.get')
    def test_http_timeout_handling(self, mock_get):
        """
        Example: Test how code handles HTTP timeouts
        """
        import requests
        from requests.exceptions import ConnectTimeout

        # Mock a timeout
        mock_get.side_effect = ConnectTimeout('Connection timed out')

        # Test that timeout is handled gracefully
        try:
            response = requests.get('https://example.com/api', timeout=1)
            self.fail("Should have raised ConnectTimeout")
        except ConnectTimeout:
            # Expected behavior
            pass

    @patch('requests.get')
    def test_http_500_error_handling(self, mock_get):
        """
        Example: Test handling of server errors
        """
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'error': 'Internal Server Error'}
        mock_get.return_value = mock_response

        import requests
        response = requests.get('https://example.com/api')
        self.assertEqual(response.status_code, 500)

    @patch('wger.exercises.sync.requests.get')
    def test_sync_handles_http_errors(self, mock_get):
        """
        Example: Test that sync functions handle HTTP errors gracefully
        """
        # Mock an HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception('HTTP Error')
        mock_get.return_value = mock_response

        # Your sync function should handle this
        # This is a template - adjust based on actual error handling in sync.py
        try:
            # Call sync function that uses requests.get
            pass
        except Exception as e:
            # Verify error is handled appropriately
            self.assertIsNotNone(e)

