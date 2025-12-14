#!/usr/bin/env python
"""
Simple timing script to measure execution time before and after optimization.

This script measures the time taken by search_languagecode method.
"""
import time
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from wger.exercises.api.filtersets import ExerciseFilterSet
from wger.exercises.models import Exercise
from django.core.cache import cache


def clear_cache():
    """Clear Django cache to ensure fresh measurements"""
    cache.clear()


def measure_search_languagecode(iterations=1000):
    """
    Measure the execution time of search_languagecode method.
    
    Returns: average time per call in milliseconds
    """
    clear_cache()
    
    qs = Exercise.objects.all()
    
    # Test with multiple language codes to trigger multiple load_language calls
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
                queryset=qs
            )
            # Force evaluation of queryset
            list(filter_set.qs[:10])
    
    # Warm up (to avoid cold start effects)
    for _ in range(10):
        run_filter()
    
    clear_cache()
    
    # Measure
    start_time = time.perf_counter()
    
    for _ in range(iterations):
        run_filter()
    
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    avg_time_per_iteration = (total_time / iterations) * 1000  # Convert to milliseconds
    avg_time_per_test_case = avg_time_per_iteration / len(test_cases)
    
    return {
        'total_time_ms': total_time * 1000,
        'avg_per_iteration_ms': avg_time_per_iteration,
        'avg_per_test_case_ms': avg_time_per_test_case,
        'iterations': iterations,
    }


if __name__ == '__main__':
    print("=" * 80)
    print("TIMING MEASUREMENT: ExerciseFilterSet.search_languagecode")
    print("=" * 80)
    print(f"Running {1000} iterations...")
    print()
    
    results = measure_search_languagecode(iterations=1000)
    
    print(f"Total time: {results['total_time_ms']:.2f} ms")
    print(f"Average per iteration: {results['avg_per_iteration_ms']:.4f} ms")
    print(f"Average per test case: {results['avg_per_test_case_ms']:.4f} ms")
    print(f"Iterations: {results['iterations']}")
    print()
    print("=" * 80)
    print("Note: This measures the time including database queries.")
    print("=" * 80)

