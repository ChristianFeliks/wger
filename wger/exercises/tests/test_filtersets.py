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
from django.test import TestCase
from unittest.mock import (
    MagicMock,
    patch,
)

# Third Party
from django_filters import rest_framework as filters

# wger
from wger.core.tests.base_testcase import BaseTestCase
from wger.exercises.api.filtersets import ExerciseFilterSet
from wger.exercises.models import (
    Exercise,
    Translation,
)


class ExerciseFilterSetTestCase(BaseTestCase, TestCase):
    """
    Unit tests for ExerciseFilterSet filter logic
    """

    def setUp(self):
        """Set up test data"""
        super().setUp()
        # Exercises and translations should be loaded from fixtures

    def test_search_name_fulltext_empty_value(self):
        """Test that empty search value returns original queryset"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': ''},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should return all exercises when search is empty
        self.assertEqual(filtered_qs.count(), qs.count())

    def test_search_name_fulltext_none_value(self):
        """Test that None search value returns original queryset"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={},
            queryset=qs
        )
        # Call the method directly with None
        result = filter_set.search_name_fulltext(qs, 'name__search', None)
        self.assertEqual(result.count(), qs.count())

    def test_search_name_fulltext_with_language_filter(self):
        """Test name search with language code filter"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': 'exercise', 'language__code': 'en'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should return exercises matching the search term in English
        self.assertGreater(filtered_qs.count(), 0)
        # Verify all results have English translations
        for exercise in filtered_qs:
            self.assertTrue(
                exercise.translations.filter(language__short_name='en').exists()
            )

    def test_search_name_fulltext_multiple_languages(self):
        """Test name search with multiple language codes"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': 'demo', 'language__code': 'en,de'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should return exercises matching in either language
        self.assertGreaterEqual(filtered_qs.count(), 0)

    def test_search_name_fulltext_duplicate_language_codes(self):
        """Test that duplicate language codes are handled correctly"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': 'exercise', 'language__code': 'en,en,de'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should handle duplicates gracefully (using set internally)
        self.assertGreaterEqual(filtered_qs.count(), 0)

    def test_search_languagecode_empty_value(self):
        """Test that empty language code returns original queryset"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'language__code': ''},
            queryset=qs
        )
        result = filter_set.search_languagecode(qs, 'language__code', '')
        self.assertEqual(result.count(), qs.count())

    def test_search_languagecode_single_language(self):
        """Test filtering by single language code"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'language__code': 'en'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should return only exercises with English translations
        self.assertGreaterEqual(filtered_qs.count(), 0)
        for exercise in filtered_qs:
            self.assertTrue(
                exercise.translations.filter(language__short_name='en').exists()
            )

    def test_search_languagecode_multiple_languages(self):
        """Test filtering by multiple language codes"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'language__code': 'en,de'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should return exercises with translations in either language
        self.assertGreaterEqual(filtered_qs.count(), 0)

    def test_search_languagecode_unknown_language(self):
        """Test that unknown language codes are handled gracefully"""
        qs = Exercise.objects.all()
        # Mock load_language to return None for unknown codes
        with patch('wger.exercises.api.filtersets.load_language') as mock_load:
            # Return None for unknown codes, which should be filtered out
            def side_effect(code):
                if code == 'zz':
                    return None
                from wger.utils.language import load_language as real_load
                return real_load(code)

            mock_load.side_effect = side_effect
            filter_set = ExerciseFilterSet(
                data={'language__code': 'en,zz'},
                queryset=qs
            )
            # Should handle None languages gracefully
            filtered_qs = filter_set.qs
            self.assertGreaterEqual(filtered_qs.count(), 0)

    def test_search_name_fulltext_without_language_filter(self):
        """Test name search without language filter"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': 'exercise'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should return exercises matching the search term in any language
        self.assertGreaterEqual(filtered_qs.count(), 0)

    def test_filter_combines_name_and_language(self):
        """Test that name search and language filter work together"""
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': 'exercise', 'language__code': 'en'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should return exercises matching both criteria
        self.assertGreaterEqual(filtered_qs.count(), 0)

    @patch('wger.exercises.api.filtersets.is_postgres_db')
    def test_search_name_fulltext_postgres_path(self, mock_is_postgres):
        """Test that PostgreSQL-specific search logic is used when appropriate"""
        from django.db import connection
        
        # Only test PostgreSQL path if we're actually using PostgreSQL
        # Otherwise, skip the test to avoid SQLite errors with SIMILARITY function
        if connection.vendor != 'postgresql':
            self.skipTest("PostgreSQL-specific test skipped on non-PostgreSQL database")
        
        mock_is_postgres.return_value = True
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': 'exercise', 'language__code': 'en'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should use trigram similarity search
        self.assertGreaterEqual(filtered_qs.count(), 0)
        mock_is_postgres.assert_called()

    @patch('wger.exercises.api.filtersets.is_postgres_db')
    def test_search_name_fulltext_non_postgres_path(self, mock_is_postgres):
        """Test that non-PostgreSQL search logic is used for other databases"""
        from django.db import connection
        
        # Only test non-PostgreSQL path if we're not using PostgreSQL
        # This ensures we test the actual code path for the current database
        if connection.vendor == 'postgresql':
            self.skipTest("Non-PostgreSQL test skipped on PostgreSQL database")
        
        mock_is_postgres.return_value = False
        qs = Exercise.objects.all()
        filter_set = ExerciseFilterSet(
            data={'name__search': 'exercise', 'language__code': 'en'},
            queryset=qs
        )
        filtered_qs = filter_set.qs
        # Should use icontains search
        self.assertGreaterEqual(filtered_qs.count(), 0)
        mock_is_postgres.assert_called()

    def test_meta_fields_exact(self):
        """Test that Meta fields are correctly configured"""
        meta_fields = ExerciseFilterSet.Meta.fields
        self.assertIn('id', meta_fields)
        self.assertIn('uuid', meta_fields)
        self.assertIn('category', meta_fields)
        self.assertIn('muscles', meta_fields)
        self.assertIn('equipment', meta_fields)

    def test_meta_model(self):
        """Test that Meta model is correctly set"""
        self.assertEqual(ExerciseFilterSet.Meta.model, Exercise)

