#!/usr/bin/env python3
import sys
from rom import Rom


def print_usage():
    print("Usage:")
    print(f"{sys.argv[0]} <rom>")


def main():
    if len(sys.argv) != 2:
        print_usage()
        return

    print(f"Opening {sys.argv[1]}...")
    rom = Rom(sys.argv[1])
    rom.print_stats()
    rom.test()


main()
