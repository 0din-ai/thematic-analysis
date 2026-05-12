"""Pre-download tiktoken BPE encoding files for bundling.

Run this at build time to populate build/tiktoken_cache/ with the
encoding files the app needs. The PyInstaller spec bundles this
directory so the frozen app never makes network requests for tokenization.
"""

import os
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "build" / "tiktoken_cache"


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["TIKTOKEN_CACHE_DIR"] = str(CACHE_DIR)

    import tiktoken

    # These are the two encodings the app may use:
    # - cl100k_base: fallback for unrecognized model names
    # - o200k_base: used by gpt-4o, o3, o4-mini, gpt-5 family
    for encoding_name in ("cl100k_base", "o200k_base"):
        print(f"Downloading {encoding_name}...")
        tiktoken.get_encoding(encoding_name)

    files = list(CACHE_DIR.iterdir())
    print(f"Cached {len(files)} files in {CACHE_DIR}:")
    for f in files:
        print(f"  {f.name} ({f.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
