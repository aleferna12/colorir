import doctest
import unittest
from colorir import *

config.REPR_STYLE = "traditional"


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


class TestDistance(unittest.TestCase):
    def test_simple_dist(self):
        dist = utils.simplified_dist(RGB(1, 1, 1), RGB(0, 0, 0))
        self.assertAlmostEqual(dist, 765)


if __name__ == "__main__":
    unittest.main()