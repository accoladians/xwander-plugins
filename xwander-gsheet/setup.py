#!/usr/bin/env python3
"""Setup script for xwander-gsheet package."""

from setuptools import setup, find_packages

setup(
    name="xwander-gsheet",
    version="2.0.0",
    description="AI-first Google Sheets management with section-based abstraction",
    author="xwander-ai",
    license="MIT",
    packages=find_packages(include=["xwander_gsheet", "xwander_gsheet.*"]),
    python_requires=">=3.8",
    install_requires=[
        "gspread>=5.0.0",
        "google-auth>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
