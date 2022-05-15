import doctest
import unittest
from pathlib import Path
from random import randint

from colorir import palette, config, Palette, SwatchPalette, ColorFormat, HSV

config.DEFAULT_PALETTES_DIR = str(Path(__file__).resolve().parent / "test_palettes")
config.DEFAULT_SWPALETTES_DIR = str(Path(__file__).resolve().parent / "test_swpalettes")


class TestPalette(unittest.TestCase):
    def test_save_load(self):
        colors = {f"c{i}": "%02x%02x%02x" % (randint(0, 255), randint(0, 255), randint(0, 255))
                  for i in range(250)}
        pal = Palette("sl_test", None, **colors)
        pal.save()
        pal2 = Palette.load("sl_test")
        self.assertEqual(pal, pal2)

    def test_load_warns(self):
        with self.assertWarns(Warning):
            Palette.load(palettes=["test1", "test2"], search_builtins=False)


class TestSwatchPalette(unittest.TestCase):
    def test_save_load(self):
        colors = ["%02x%02x%02x" % (randint(0, 255), randint(0, 255), randint(0, 255))
                  for _ in range(250)]
        swpal = SwatchPalette("sl_test", None, *colors)
        swpal.save()
        swpal2 = SwatchPalette.load("sl_test")
        self.assertEqual(swpal, swpal2)

    def test_complementary(self):
        red = "ff0000"
        swpal = SwatchPalette.new_complementary(3, red)
        self.assertEqual(swpal, SwatchPalette(None, None, red, "00ff00", "0000ff"))

    def test_analogous(self):
        red = HSV(0, 1, 1)
        # Center, clockwise and counter-clockwise generation
        c_swpal = SwatchPalette.new_analogous(3, color=red)
        cw_swpal = SwatchPalette.new_analogous(3, color=red, start=1)
        ccw_swpal = SwatchPalette.new_analogous(3, color=red, start=-1)
        self.assertEqual(c_swpal, SwatchPalette(None, None, HSV(330, 1, 1), red, HSV(30, 1, 1)))
        self.assertEqual(cw_swpal, SwatchPalette(None, None, red, HSV(30, 1, 1), HSV(60, 1, 1)))
        self.assertEqual(ccw_swpal, SwatchPalette(None, None, HSV(300, 1, 1), HSV(330, 1, 1), red))
        # Larger hue wheel sections
        wide_swpal = SwatchPalette.new_analogous(3, sections=3, color=red)
        self.assertEqual(wide_swpal, SwatchPalette(None, None, HSV(240, 1, 1), red, HSV(120, 1, 1)))


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(palette))
    return tests


if __name__ == "__main__":
    unittest.main()