import doctest
import unittest
from colorir import color, sRGB, simplified_dist


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(color))
    return tests


class TestDistance(unittest.TestCase):
    def test_simple_dist(self):
        dist = simplified_dist(sRGB(255, 255, 255), sRGB(0, 0, 0))
        self.assertAlmostEqual(dist, 765)


if __name__ == "__main__":
    unittest.main()