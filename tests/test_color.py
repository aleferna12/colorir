import doctest
import unittest
from colorir import color


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(color))
    return tests


if __name__ == "__main__":
    unittest.main()