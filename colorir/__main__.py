import argparse
from os import path
from runpy import run_module
from . import config
config.DEFAULT_PALETTES_DIR = path.join(path.dirname(__file__), "examples/ex_palettes")


def main(example):
    run_module("colorir.examples." + example)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m colorir",
                                     description="Execute example applications.")
    parser.add_argument("app",
                        help="which example application to execute (e.g.: simple_turtle_2)")
    args = parser.parse_args()
    main(args.app)