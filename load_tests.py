#!/usr/bin/env python
# load_tests.py
import sys
from unittest import TestSuite
from boot_django import boot_django

boot_django()

default_labels = ["femtolytics.tests", ]

def get_suite(labels=default_labels):
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=1)
    failures = runner.run_tests(labels)
    if failures:
        sys.exit(failures)

    # In case this is called from setuptools, return a test suite
    return TestSuite()

if __name__ == "__main__":
    labels = default_labels
    if len(sys.argv[1:]) > 0:
        labels = sys.argv[1:]

    get_suite(labels)
