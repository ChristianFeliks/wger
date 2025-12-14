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

# Django
from django.core.exceptions import ValidationError

# wger
from wger.core.tests.base_testcase import BaseTestCase
from wger.core.models import Language
from wger.utils.validators import validate_language_code
from django.test import TestCase


class ValidateLanguageCodeTestCase(BaseTestCase, TestCase):
    """
    Test the validate_language_code validator function
    """

    def setUp(self):
        """Set up test data"""
        super().setUp()
        # Languages are loaded from 'test-languages' fixture via BaseTestCase
        # which includes: 'de' (pk=1), 'en' (pk=2), 'fr' (pk=3)

    def test_valid_language_code(self):
        """Test that valid language codes pass validation"""
        # Assuming 'en' exists in test fixtures
        try:
            validate_language_code('en')
        except ValidationError:
            self.fail("validate_language_code raised ValidationError for valid code 'en'")

    def test_valid_language_code_de(self):
        """Test that valid German language code passes validation"""
        # Assuming 'de' exists in test fixtures
        try:
            validate_language_code('de')
        except ValidationError:
            self.fail("validate_language_code raised ValidationError for valid code 'de'")

    def test_invalid_language_code(self):
        """Test that invalid language codes raise ValidationError"""
        with self.assertRaises(ValidationError) as context:
            validate_language_code('xx')

        self.assertIn('does not exist', str(context.exception))

    def test_invalid_language_code_empty(self):
        """Test that empty language code raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_language_code('')

    def test_invalid_language_code_nonexistent(self):
        """Test that nonexistent language codes raise ValidationError with correct message"""
        invalid_code = 'zzz'
        with self.assertRaises(ValidationError) as context:
            validate_language_code(invalid_code)

        error_message = str(context.exception)
        self.assertIn(invalid_code, error_message)
        self.assertIn('does not exist', error_message)

    def test_case_sensitivity(self):
        """Test that language code validation is case-sensitive"""
        # 'en' exists in fixtures (lowercase)
        validate_language_code('en')
        
        # 'EN' (uppercase) should fail because language codes are stored lowercase
        with self.assertRaises(ValidationError) as context:
            validate_language_code('EN')
        
        self.assertIn('does not exist', str(context.exception))

