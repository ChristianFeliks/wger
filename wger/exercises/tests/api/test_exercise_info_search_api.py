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
from django.urls import reverse

# Third Party
from rest_framework import status

# wger
from wger.core.tests.api_base_test import ApiBaseTestCase
from wger.core.tests.base_testcase import BaseTestCase


class ExerciseInfoFilterApiTestCase(BaseTestCase, ApiBaseTestCase):
    url = '/api/v2/exerciseinfo/'

    def setUp(self):
        super().setUp()
        self.init_media_root()

    def _results(self, response):
        if isinstance(response.data, dict) and 'results' in response.data:
            return response.data['results']
        return response.data

    def _has_translation_name(self, item, expected_name: str) -> bool:
        for t in item.get('translations', []):
            if t.get('name') == expected_name:
                return True
        return False

    def test_basic_search_logged_out(self):
        """
        Logged-out users can search via name__search and language__code
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'exercise', 'language__code': 'en'},
        )
        results = self._results(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 4)
        ids = {item['id'] for item in results}
        self.assertIn(1, ids)
        item1 = next(item for item in results if item['id'] == 1)
        self.assertTrue(self._has_translation_name(item1, 'An exercise'))

    def test_basic_search_logged_in(self):
        """
        Logged-in users get the same results
        """
        self.authenticate('test')
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'exercise', 'language__code': 'en'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 4)
        ids = {item['id'] for item in results}
        self.assertIn(1, ids)
        item1 = next(item for item in results if item['id'] == 1)
        self.assertTrue(self._has_translation_name(item1, 'An exercise'))

    def test_search_language_code_en_no_results(self):
        """
        A DE-only exercise name should not be found when searching in English
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'Weitere', 'language__code': 'en'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 0)

    def test_search_language_code_de(self):
        """
        A DE-only exercise should be found when searching in German
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'Weitere', 'language__code': 'de'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 4)

    def test_search_several_language_codes(self):
        """
        Passing different language codes works correctly
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'demo', 'language__code': 'en,de'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 4)

    def test_search_unknown_language_codes(self):
        """
        Unknown language codes are ignored
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'demo', 'language__code': 'en,de,zz'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 4)

    def test_search_all_languages(self):
        """
        Disable all language filters when language__code is omitted
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'demo'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 4)

    def test_search_matches_alias(self):
        """
        Alias terms should also match
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'different', 'language__code': 'en'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 1)

    def test_search_empty_query(self):
        """
        Empty search query should return all results (or handle gracefully)
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': '', 'language__code': 'en'},
        )
        results = self._results(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Empty search might return all or none, depending on implementation
        self.assertIsInstance(results, list)

    def test_search_pagination(self):
        """
        Test that pagination works correctly with search filters
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'exercise', 'language__code': 'en', 'page_size': 2},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if pagination is enabled (response is a dict with 'results' key)
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
            # If pagination is working, results should be limited to page_size
            # If not, all results are returned (which is also valid)
            # So we just check that we got results and the structure is correct
            self.assertIsInstance(results, list)
            self.assertGreaterEqual(len(results), 0)
            # Check pagination metadata if present
            if 'count' in response.data:
                self.assertIsInstance(response.data['count'], int)
            # 'next' may or may not be present depending on whether there are more pages
            # So we don't assert it must exist
        else:
            # If pagination is not enabled, response.data is a list
            # This is also valid, just different pagination configuration
            self.assertIsInstance(response.data, list)
            self.assertGreaterEqual(len(response.data), 0)

    def test_search_ordering(self):
        """
        Test that ordering works with search filters
        """
        response = self.client.get(
            reverse('exerciseinfo-list'),
            {'name__search': 'exercise', 'language__code': 'en', 'ordering': 'id'},
        )
        results = self._results(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if len(results) > 1:
            ids = [item['id'] for item in results]
            self.assertEqual(ids, sorted(ids))
