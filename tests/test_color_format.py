import doctest
import unittest
from colorir import color_format


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(color_format))
    return tests


if __name__ == "__main__":
    unittest.main()