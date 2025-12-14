#!/usr/bin/env python
"""
Profiling test using Django test framework.

This script runs a test that exercises the filter and measures performance.
"""
import cProfile
import pstats
import io
import time
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_settings')
django.setup()

from wger.exercises.api.filtersets import ExerciseFilterSet
from wger.exercises.models import Exercise
from django.core.cache import cache


def clear_cache():
    """Clear Django cache"""
    cache.clear()


def measure_performance(iterations=1000):
    """
    Measure performance of search_languagecode method.
    Uses Django test database setup.
    """
    from django.test import TestCase
    from wger.core.tests.base_testcase import BaseTestCase
    
    class PerformanceTest(BaseTestCase, TestCase):
        """Test class for performance measurement"""
        
        def setUp(self):
            super().setUp()
            self.qs = Exercise.objects.all()
        
        def test_search_languagecode_performance(self):
            """Test that measures performance"""
            clear_cache()
            
            test_cases = [
                'en',
                'de',
                'en,de',
                'en,de,fr',
                'en,de,fr,es,it',
            ]
            
            def run_filter():
                for lang_codes in test_cases:
                    filter_set = ExerciseFilterSet(
                        data={'language__code': lang_codes},
                        queryset=self.qs
                    )
                    # Force evaluation
                    list(filter_set.qs[:10])
            
            # Warm up
            for _ in range(10):
                run_filter()
            
            clear_cache()
            
            # Measure
            start = time.perf_counter()
            for _ in range(iterations):
                run_filter()
            end = time.perf_counter()
            
            total_ms = (end - start) * 1000
            avg_per_iteration = total_ms / iterations
            avg_per_test_case = avg_per_iteration / len(test_cases)
            
            print(f"\n{'='*80}")
            print(f"PERFORMANCE RESULTS (BEFORE OPTIMIZATION)")
            print(f"{'='*80}")
            print(f"Total time: {total_ms:.2f} ms")
            print(f"Average per iteration: {avg_per_iteration:.4f} ms")
            print(f"Average per test case: {avg_per_test_case:.4f} ms")
            print(f"Iterations: {iterations}")
            print(f"{'='*80}\n")
            
            # Store result for comparison
            self.performance_result = {
                'total_ms': total_ms,
                'avg_per_iteration_ms': avg_per_iteration,
                'avg_per_test_case_ms': avg_per_test_case,
            }
    
    # Run the test
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=0, interactive=False, keepdb=True)
    
    suite = django.test.TestSuite()
    suite.addTest(PerformanceTest('test_search_languagecode_performance'))
    
    result = test_runner.run_tests(['__main__.PerformanceTest'])
    
    return result


if __name__ == '__main__':
    print("Running performance test...")
    measure_performance(iterations=1000)

