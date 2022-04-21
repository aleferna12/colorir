import doctest
import unittest
from pathlib import Path

from colorir import palette, config

config.DEFAULT_PALETTES_DIR = str(Path(__file__).resolve().parent / "test_palettes")


class TestPalette(unittest.TestCase):
    def test_load_warns(self):
        with self.assertWarns(Warning):
            palette.Palette.load(palettes=["test", "test2"])


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(palette))
    return tests


if __name__ == "__main__":
    unittest.main()