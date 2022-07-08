import doctest
import unittest
from colorir import color
from colorir.color import *


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(color))
    return tests


class TestDistance(unittest.TestCase):
    def test_color_conversion(self):
        rgba = (50, 78, 5, 255)
        self.assertEqual(
            sRGB(50, 78, 5),
            sRGB._from_rgba(rgba)
        )
        self.assertEqual(
            HSL(0.23059, 0.87950, 0.16275, 1, max_h=1),
            HSL._from_rgba(rgba)
        )
        self.assertEqual(
            HSV(0.23059, 0.93588, 0.30588, 1, max_h=1),
            HSV._from_rgba(rgba)
        )
        self.assertEqual(
            CMY(0.80392, 0.69412, 0.98039, 1),
            CMY._from_rgba(rgba)
        )
        self.assertEqual(
            CMYK(0.35897, 0, 0.9359, 0.69412, 1),
            CMYK._from_rgba(rgba)
        )
        self.assertEqual(
            CIELab(29.757, -22.344, 35.474, 1),
            CIELab._from_rgba(rgba)
        )
        self.assertEqual(
            CIELuv(29.757, -13.267, 33.646, 1),
            CIELuv._from_rgba(rgba)
        )
        self.assertEqual(
            Hex("#ff324e05"),
            Hex._from_rgba(rgba)
        )

    def test_simple_dist(self):
        dist = simplified_dist(sRGB(255, 255, 255), sRGB(0, 0, 0))
        self.assertAlmostEqual(dist, 765)


if __name__ == "__main__":
    unittest.main()