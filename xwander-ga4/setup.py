"""Setup configuration for xwander-ga4 plugin"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="xwander-ga4",
    version="1.0.0",
    author="Xwander Growth Team",
    description="Google Analytics 4 API wrapper with reporting and dimension management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/accoladians/xwander.com",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-analytics-data>=0.18.0",
        "google-analytics-admin>=0.20.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "xwander-ga4=xwander_ga4.cli:cli",
        ],
    },
)
