#!/usr/bin/env python

import sys

import lox


def main() -> None:
    """Main loop for lox."""
    if len(sys.argv) > 2:
        sys.stderr.write("Usage: pylox.py [script]")
        exit(64)
    elif len(sys.argv) == 2:
        lox.run_file(sys.argv[1])
    else:
        lox.run_prompt()

    exit(0)

if __name__ == "__main__":
    main()