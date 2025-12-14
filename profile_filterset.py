#!/usr/bin/env python
"""
Profiling script for ExerciseFilterSet performance analysis.

This script profiles the search_languagecode method to identify bottlenecks.
"""
import cProfile
import pstats
import io
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


def profile_search_languagecode(iterations=100):
    """
    Profile the search_languagecode method by running it multiple times.
    This simulates real-world usage where the filter is called frequently.
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
    
    # Profile the execution
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run multiple iterations to get accurate timing
    for _ in range(iterations):
        run_filter()
    
    profiler.disable()
    
    # Get statistics
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    
    return s.getvalue()


if __name__ == '__main__':
    print("=" * 80)
    print("PROFILING ExerciseFilterSet.search_languagecode")
    print("=" * 80)
    print(f"Running 100 iterations with multiple language code combinations...")
    print()
    
    stats = profile_search_languagecode(iterations=100)
    print(stats)
    
    print("=" * 80)
    print("Key metrics to look for:")
    print("- load_language function calls and time")
    print("- Database query execution time")
    print("- Total cumulative time")
    print("=" * 80)

