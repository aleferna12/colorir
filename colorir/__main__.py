import argparse
import sys
from importlib import import_module
from pathlib import Path
from colorir import config

example_path = Path(__file__).resolve().parent.parent / "examples"


def main(example):
    sys.path.append(str(example_path))
    config.DEFAULT_PALETTES_DIR = str(example_path / "ex_palettes")
    import_module(example)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m colorir",
                                     description="Execute example applications.")
    examples_choices = [file.name.replace(".py", "") for file in example_path.glob("*py")]
    parser.add_argument("app",
                        help="which example application to execute (e.g.: simple_turtle_2)",
                        choices=examples_choices)
    args = parser.parse_args()
    main(args.app)