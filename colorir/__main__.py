import argparse
import sys
from importlib import import_module
from pathlib import Path


def run_example_app(example):
    example_path = str(Path(__file__).resolve().parent.parent / "examples")
    sys.path.append(example_path)
    import_module(example)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m colorir",
                                     description="Execute example applications.")
    parser.add_argument("app",
                        help="which example application to execute (e.g.: simple_turtle_2)")

    args = parser.parse_args()
    run_example_app(args.app)