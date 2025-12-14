#!/usr/bin/env python
"""
Simple performance measurement script.

Run this with: python manage.py shell < measure_performance.py
Or: python -c "exec(open('measure_performance.py').read())"
"""
import time
from django.core.cache import cache
from wger.exercises.api.filtersets import ExerciseFilterSet
from wger.exercises.models import Exercise


def measure_search_languagecode(iterations=1000):
    """Measure performance of search_languagecode"""
    cache.clear()
    
    qs = Exercise.objects.all()
    test_cases = ['en', 'de', 'en,de', 'en,de,fr', 'en,de,fr,es,it']
    
    def run_filter():
        for lang_codes in test_cases:
            filter_set = ExerciseFilterSet(
                data={'language__code': lang_codes},
                queryset=qs
            )
            list(filter_set.qs[:10])
    
    # Warm up
    for _ in range(10):
        run_filter()
    
    cache.clear()
    
    # Measure
    start = time.perf_counter()
    for _ in range(iterations):
        run_filter()
    end = time.perf_counter()
    
    total_ms = (end - start) * 1000
    avg_per_iteration = total_ms / iterations
    avg_per_test_case = avg_per_iteration / len(test_cases)
    
    print(f"\n{'='*80}")
    print(f"PERFORMANCE MEASUREMENT")
    print(f"{'='*80}")
    print(f"Total time: {total_ms:.2f} ms")
    print(f"Average per iteration: {avg_per_iteration:.4f} ms")
    print(f"Average per test case: {avg_per_test_case:.4f} ms")
    print(f"Iterations: {iterations}")
    print(f"{'='*80}\n")
    
    return {
        'total_ms': total_ms,
        'avg_per_iteration_ms': avg_per_iteration,
        'avg_per_test_case_ms': avg_per_test_case,
    }


if __name__ == '__main__':
    result = measure_search_languagecode(1000)

