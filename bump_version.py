"""
bump_version.py
Reads finofx/__init__.py
Extracts the current version
Bumps major, minor, or patch
Writes the updated version back
Prints the new version for your build logs

🚀 Optional upgrade (if you want it)
I can also generate:
A Git tag + version bump combo script
A pre‑build hook that bumps patch automatically
A semantic version validator
A version.json → init.py sync system
A version banner in your diagnostic prints

If you want any of these, just tell me which direction you want to take.
"""

#!/usr/bin/env python3
import re
import sys
from pathlib import Path

#INIT_FILE = Path(__file__).parent / "__init__.py"
INIT_FILE = Path(__file__).parent / "version.py"
print(INIT_FILE)
VERSION_PATTERN = re.compile(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"')
print(VERSION_PATTERN)

def read_version():
    text = INIT_FILE.read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(text)
    if not match:
        raise RuntimeError("Could not find __version__ in finofx/__init__.py")
    return tuple(map(int, match.groups()))

def write_version(vtuple):
    major, minor, patch = vtuple
    new_version = f'{major}.{minor}.{patch}'
    text = INIT_FILE.read_text(encoding="utf-8")
    new_text = VERSION_PATTERN.sub(f'__version__ = "{new_version}"', text)
    INIT_FILE.write_text(new_text, encoding="utf-8")
    return new_version

def bump(kind):
    major, minor, patch = read_version()

    if kind == "major":
        major += 1
        minor = 0
        patch = 0
    elif kind == "minor":
        minor += 1
        patch = 0
    elif kind == "patch":
        patch += 1
    else:
        raise ValueError("Use: major | minor | patch")

    return write_version((major, minor, patch))

if __name__ == "__main__":
    print(sys.argv)
    print(len(sys.argv))
    if len(sys.argv) != 2:
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)

    new_version = bump(sys.argv[1])
    print("FinOfx version bumped to", new_version)
