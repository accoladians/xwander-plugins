"""Setup configuration for xwander-ads plugin."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="xwander-ads",
    version="1.0.0",
    description="Google Ads API integration - Performance Max campaigns, audiences, conversions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Xwander Platform",
    author_email="joni@accolade.fi",
    url="https://github.com/accoladians/xwander-platform",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "google-ads>=24.0.0",
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "xw-ads=xwander_ads.cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="google-ads pmax performance-max advertising api xwander",
    project_urls={
        "Documentation": "https://github.com/accoladians/xwander-platform/tree/dev/plugins/xwander-ads",
        "Source": "https://github.com/accoladians/xwander-platform",
    },
)
