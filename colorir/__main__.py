import argparse
import sys
from importlib import import_module
from pathlib import Path
from colorir import config


def run_example_app(example):
    example_path = Path(__file__).resolve().parent.parent / "examples"
    sys.path.append(str(example_path))
    config.DEFAULT_PALETTES_DIR = str(example_path / "ex_palettes")
    import_module(example)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m colorir",
                                     description="Execute example applications.")
    parser.add_argument("app",
                        help="which example application to execute (e.g.: simple_turtle_2)")

    args = parser.parse_args()
    run_example_app(args.app)