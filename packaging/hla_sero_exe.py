"""Entry point for the standalone hla-sero.exe (built by PyInstaller in GitHub Actions).

Double-click -> opens the copy-paste window. From a command prompt the usual
commands work too:  hla-sero.exe convert typing.txt -o result.csv
"""
import sys

from hla_sero.cli import main

sys.exit(main())
