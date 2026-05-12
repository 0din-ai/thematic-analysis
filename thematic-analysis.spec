# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Thematic Analysis macOS .app bundle."""

import os

ROOT = SPECPATH  # PyInstaller sets SPECPATH to the spec file's directory
SRC = os.path.join(ROOT, "src")

a = Analysis(
    [os.path.join(ROOT, "scripts", "pyinstaller_entry.py")],
    pathex=[SRC],
    datas=[
        (os.path.join(SRC, "thematic_analysis", "templates"), os.path.join("thematic_analysis", "templates")),
        (os.path.join(ROOT, "prompts"), "prompts"),
        (os.path.join(ROOT, "build", "tiktoken_cache"), "tiktoken_cache"),
    ],
    hiddenimports=[
        # tiktoken plugin discovery (pkgutil.iter_modules)
        "tiktoken_ext",
        "tiktoken_ext.openai_public",
        # rapidfuzz C extensions
        "rapidfuzz.fuzz_cpp",
        "rapidfuzz.utils_cpp",
        # openai SDK HTTP transport chain
        "httpx",
        "httpcore",
        "h11",
        "anyio",
        "anyio._backends._asyncio",
        "certifi",
        "sniffio",
    ],
    excludes=[
        "tkinter",
        "pytest",
        "unittest",
    ],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="thematic-analysis",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    target_arch="arm64",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="thematic-analysis",
)

app = BUNDLE(
    coll,
    name="Thematic Analysis.app",
    bundle_identifier="com.0din.thematic-analysis",
    info_plist={
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
    },
)
