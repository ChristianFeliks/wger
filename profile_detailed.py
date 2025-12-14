#!/usr/bin/env python
"""
Detailed profiling script using cProfile to identify bottlenecks.

This script profiles the search_languagecode method to show where time is spent.
"""
import cProfile
import pstats
import io
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


def profile_search_languagecode(iterations=500):
    """
    Profile the search_languagecode method using cProfile.
    """
    from django.test import TestCase
    from wger.core.tests.base_testcase import BaseTestCase
    
    class ProfileTest(BaseTestCase, TestCase):
        """Test class for profiling"""
        
        def setUp(self):
            super().setUp()
            self.qs = Exercise.objects.all()
        
        def test_profile(self):
            """Profile the method"""
            clear_cache()
            
            test_cases = ['en', 'de', 'en,de', 'en,de,fr', 'en,de,fr,es,it']
            
            def run_filter():
                for lang_codes in test_cases:
                    filter_set = ExerciseFilterSet(
                        data={'language__code': lang_codes},
                        queryset=self.qs
                    )
                    list(filter_set.qs[:10])
            
            # Warm up
            for _ in range(10):
                run_filter()
            
            clear_cache()
            
            # Profile
            profiler = cProfile.Profile()
            profiler.enable()
            
            for _ in range(iterations):
                run_filter()
            
            profiler.disable()
            
            # Get statistics
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            print(s.getvalue())
    
    # Run the test
    from django.test.utils import get_runner
    from unittest import TestSuite
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=0, interactive=False, keepdb=True)
    
    suite = TestSuite()
    suite.addTest(ProfileTest('test_profile'))
    
    test_runner.run_tests(['__main__.ProfileTest'])


if __name__ == '__main__':
    print("=" * 80)
    print("DETAILED PROFILING: ExerciseFilterSet.search_languagecode")
    print("=" * 80)
    print(f"Running {500} iterations...")
    print()
    profile_search_languagecode(iterations=500)

