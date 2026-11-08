#!/usr/bin/env python3
"""Find the DK64 NTSC-U 1.0 ROM among downloaded build inputs and write it as .z64.

Usage: prepare_rom.py <input_dir> <output.z64>

Accepts .z64 (big endian), .v64 (byte swapped) and .n64 (little endian)
files, loose or inside .zip archives, converts to .z64 and checks the SHA-1.
"""
import hashlib
import sys
import zipfile
from pathlib import Path

EXPECTED_SHA1 = "cf806ff2603640a748fca5026ded28802f1f4a50"
ROM_EXTS = {".z64", ".n64", ".v64"}


def to_z64(data: bytes) -> bytes:
    head = data[:4]
    if head == b"\x80\x37\x12\x40":  # z64
        return data
    if head == b"\x37\x80\x40\x12":  # v64: swap every 16-bit pair
        out = bytearray(data)
        out[0::2], out[1::2] = data[1::2], data[0::2]
        return bytes(out)
    if head == b"\x40\x12\x37\x80":  # n64: reverse every 32-bit word
        out = bytearray(len(data))
        for i in range(4):
            out[i::4] = data[3 - i::4]
        return bytes(out)
    return data


def candidates(input_dir: Path):
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext in ROM_EXTS:
            yield str(path), path.read_bytes()
        elif ext == ".zip":
            with zipfile.ZipFile(path) as zf:
                for name in zf.namelist():
                    if Path(name).suffix.lower() in ROM_EXTS:
                        yield f"{path}:{name}", zf.read(name)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    input_dir, output = Path(sys.argv[1]), Path(sys.argv[2])
    seen = []
    for label, data in candidates(input_dir):
        rom = to_z64(data)
        sha1 = hashlib.sha1(rom).hexdigest()
        seen.append(f"{label} -> {sha1}")
        if sha1 == EXPECTED_SHA1:
            output.write_bytes(rom)
            print(f"Using {label} (sha1 {sha1}) -> {output}")
            return 0
    print("::error::No Donkey Kong 64 NTSC-U 1.0 ROM found "
          f"(expected sha1 {EXPECTED_SHA1}).")
    for line in seen or ["(no .z64/.n64/.v64 files found, loose or in .zip)"]:
        print("  " + line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
