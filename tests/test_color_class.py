import doctest
import unittest
import numpy as np

from colorir import *

config.REPR_STYLE = "traditional"


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(color_class))
    return tests


class TestConversion(unittest.TestCase):
    rgba = np.array([50, 78, 5, 255])

    def test_rgb_conversion(self):
        color = RGB(50, 78, 5, max_rgb=255)
        self.assertEqual(
            color,
            RGB._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (50, 78, 5)
        )

    def test_hsl_conversion(self):
        color = HSL(0.23059, 0.87950, 0.16275, max_h=1)
        self.assertEqual(
            color,
            HSL._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (0.23059, 0.87950, 0.16275)
        )

    def test_hsv_conversion(self):
        color = HSV(0.23059, 0.93588, 0.30588, max_h=1)
        self.assertEqual(
            color,
            HSV._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (0.23059, 0.93588, 0.30588)
        )

    def test_cmy_conversion(self):
        color = CMY(0.80392, 0.69412, 0.98039)
        self.assertEqual(
            color,
            CMY._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (0.80392, 0.69412, 0.98039)
        )

    def test_cmyk_conversion(self):
        color = CMYK(0.35897, 0, 0.9359, 0.69412)
        self.assertEqual(
            color,
            CMYK._from_rgba(self.rgba),
            (0.35897, 0, 0.9359, 0.69412)
        )

    def test_cielab_conversion(self):
        color = CIELab(29.757, -22.344, 35.474)
        self.assertEqual(
            color,
            CIELab._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (29.757, -22.344, 35.474)
        )

    def test_cieluv_conversion(self):
        color = CIELuv(29.757, -13.267, 33.646)
        self.assertEqual(
            color,
            CIELuv._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (29.757, -13.267, 33.646)
        )

    def test_hcluv_conversion(self):
        color = HCLuv(111.514, 36.172, 29.757)
        self.assertEqual(
            color,
            HCLuv._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (111.514, 36.172, 29.757)
        )

    def test_hclab_conversion(self):
        color = HCLab(122.206, 41.926, 29.757)
        self.assertEqual(
            color,
            HCLab._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            (122.206, 41.926, 29.757)
        )

    def test_hex_conversion(self):
        color = Hex("#324e05")
        self.assertEqual(
            color,
            Hex._from_rgba(self.rgba)
        )
        self.assertEqual(
            color,
            "#324e05"
        )


if __name__ == "__main__":
    unittest.main()