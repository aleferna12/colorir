import doctest
import unittest

from colorir import *

config.REPR_STYLE = "traditional"


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(gradient))
    return tests


if __name__ == "__main__":
    unittest.main()