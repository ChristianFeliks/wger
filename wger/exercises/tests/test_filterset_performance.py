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
Performance test for ExerciseFilterSet to measure execution time.
"""

import time
from django.test import TestCase
from django.core.cache import cache

# wger
from wger.core.tests.base_testcase import BaseTestCase
from wger.exercises.api.filtersets import ExerciseFilterSet
from wger.exercises.models import Exercise


class ExerciseFilterSetPerformanceTestCase(BaseTestCase, TestCase):
    """
    Performance tests for ExerciseFilterSet
    """

    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.qs = Exercise.objects.all()

    def test_search_languagecode_performance(self):
        """
        Measure performance of search_languagecode method.
        This test runs the filter multiple times to get accurate timing.
        """
        cache.clear()
        
        # Test cases with varying numbers of language codes
        test_cases = [
            'en',
            'de',
            'en,de',
            'en,de,fr',
            'en,de,fr,es,it',
        ]
        
        def run_filter():
            """Run the filter for all test cases"""
            for lang_codes in test_cases:
                filter_set = ExerciseFilterSet(
                    data={'language__code': lang_codes},
                    queryset=self.qs
                )
                # Force evaluation of queryset
                list(filter_set.qs[:10])
        
        # Warm up (to avoid cold start effects)
        for _ in range(10):
            run_filter()
        
        cache.clear()
        
        # Measure performance
        iterations = 1000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            run_filter()
        
        end_time = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_per_iteration_ms = total_time_ms / iterations
        avg_per_test_case_ms = avg_per_iteration_ms / len(test_cases)
        
        # Store results as test attributes for later comparison
        self.performance_result = {
            'total_ms': total_time_ms,
            'avg_per_iteration_ms': avg_per_iteration_ms,
            'avg_per_test_case_ms': avg_per_test_case_ms,
            'iterations': iterations,
        }
        
        # Print results (will be captured in test output)
        print(f"\n{'='*80}")
        print(f"PERFORMANCE RESULTS")
        print(f"{'='*80}")
        print(f"Total time: {total_time_ms:.2f} ms")
        print(f"Average per iteration: {avg_per_iteration_ms:.4f} ms")
        print(f"Average per test case: {avg_per_test_case_ms:.4f} ms")
        print(f"Iterations: {iterations}")
        print(f"{'='*80}\n")
        
        # Test should pass (we're just measuring, not asserting)
        self.assertIsNotNone(self.performance_result)

