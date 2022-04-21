import doctest
import unittest
from colorir import gradient


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(gradient))
    return tests


if __name__ == "__main__":
    unittest.main()