import doctest
import unittest
from pathlib import Path
from random import randint
import re

from colorir import palette, config, Palette, StackPalette, HSV, find_palettes, delete_palette
config.DEFAULT_PALETTES_DIR = str(Path(__file__).resolve().parent / "test_palettes")
# Clear test palette directory
for file in Path(config.DEFAULT_PALETTES_DIR).glob("*"):
    # Keep original test files, remove others
    if re.search(r"test\d", file.name) is None:
        file.unlink()


class TestPalette(unittest.TestCase):
    def test_add_op(self):
        pal = Palette(c1="ffffff") + Palette(c2="000000")
        self.assertEqual(pal, Palette(c1="ffffff", c2="000000"))

    def test_save_load(self):
        colors = {f"c{i}": "%02x%02x%02x" % (randint(0, 255), randint(0, 255), randint(0, 255))
                  for i in range(250)}
        pal = Palette("test_sl", None, **colors)
        pal.save()
        pal2 = Palette.load("test_sl")
        self.assertEqual(pal, pal2)

    def test_load_warns(self):
        with self.assertWarns(Warning):
            Palette.load(palettes=["test1", "test2"], search_builtins=False)


class TestSwatchPalette(unittest.TestCase):
    def test_add_op(self):
        spal = StackPalette(None, None, "ffffff") + StackPalette(None, None, "000000")
        self.assertEqual(spal, StackPalette(None, None, "ffffff", "000000"))

    def test_save_load(self):
        colors = ["%02x%02x%02x" % (randint(0, 255), randint(0, 255), randint(0, 255))
                  for _ in range(250)]
        spal = StackPalette("test_sl", None, *colors)
        spal.save()
        spal2 = StackPalette.load("test_sl")
        self.assertEqual(spal, spal2)

    def test_complementary(self):
        red = "ff0000"
        spal = StackPalette.new_complementary(3, red)
        self.assertEqual(spal, StackPalette(None, None, red, "00ff00", "0000ff"))

    def test_analogous(self):
        red = HSV(0, 1, 1)
        # Center, clockwise and counter-clockwise generation
        c_spal = StackPalette.new_analogous(3, color=red)
        cw_spal = StackPalette.new_analogous(3, color=red, start=1)
        ccw_spal = StackPalette.new_analogous(3, color=red, start=-1)
        self.assertEqual(c_spal, StackPalette(None, None, HSV(330, 1, 1), red, HSV(30, 1, 1)))
        self.assertEqual(cw_spal, StackPalette(None, None, red, HSV(30, 1, 1), HSV(60, 1, 1)))
        self.assertEqual(ccw_spal, StackPalette(None, None, HSV(300, 1, 1), HSV(330, 1, 1), red))
        # Larger hue wheel sections
        wide_spal = StackPalette.new_analogous(3, sections=3, color=red)
        self.assertEqual(wide_spal, StackPalette(None, None, HSV(240, 1, 1), red, HSV(120, 1, 1)))


class TestOtherFunctions(unittest.TestCase):
    def test_find_palettes(self):
        all_pals = find_palettes(search_builtins=False)
        self.assertEqual(all_pals, ['test1', 'test2', 'test3'])
        pals = find_palettes(search_builtins=False, kind=Palette)
        self.assertEqual(pals, ['test1', 'test2'])
        spals = find_palettes(search_builtins=False, kind=StackPalette)
        self.assertEqual(spals, ['test3'])

    def test_delete_palette(self):
        n_pal = Palette("test_del", red="ff0000")
        n_pal.save()
        self.assertIn("test_del", find_palettes())
        delete_palette("test_del")
        self.assertNotIn("test_del", find_palettes())


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(palette))
    return tests


if __name__ == "__main__":
    unittest.main()