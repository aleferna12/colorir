import doctest
import unittest
from colorir import color_class
from colorir.color_class import *


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(color_class))
    return tests


class TestConversion(unittest.TestCase):
    # Probably should split in multiple tests
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
            HCLuv(111.514, 36.172, 29.757, 1),
            HCLuv._from_rgba(rgba)
        )
        self.assertEqual(
            HCLab(122.206, 41.926, 29.757, 1),
            HCLab._from_rgba(rgba)
        )
        self.assertEqual(
            Hex("#ff324e05"),
            Hex._from_rgba(rgba)
        )


if __name__ == "__main__":
    unittest.main()