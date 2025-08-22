# setup.py - Enhanced version with multi-file support
"""
Enhanced package setup configuration for name-address-validator with multi-file processing
"""

from setuptools import setup, find_packages
import os

# Read README file if it exists
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "A comprehensive name and address validation tool with multi-file processing and automatic address format standardization using USPS API and US Census data"

# Read requirements from requirements.txt if it exists
requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
else:
    # Enhanced requirements with new dependencies
    requirements = [
        "streamlit>=1.28.0",
        "requests>=2.31.0",
        "fuzzywuzzy>=0.18.0",
        "python-levenshtein>=0.21.0",
        "click>=8.0.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "xlsxwriter>=3.0.0",
    ]

setup(
    name="name-address-validator",
    version="1.1.0",  # Updated version with new features
    author="Your Name",
    author_email="your.email@example.com",
    description="Enhanced name and address validation tool with multi-file processing and address format standardization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/name-address-validator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "Topic :: Office/Business :: Financial :: Spreadsheet",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Environment :: Web Environment",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "all": [
            # Include all optional dependencies
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0", 
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "name-address-validator=name_address_validator.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "address validation",
        "name validation", 
        "USPS API",
        "data cleaning",
        "CSV processing",
        "multi-file processing",
        "address standardization",
        "data quality",
        "batch processing",
        "streamlit",
        "CLI",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/name-address-validator/issues",
        "Source": "https://github.com/yourusername/name-address-validator",
        "Documentation": "https://github.com/yourusername/name-address-validator#readme",
        "Changelog": "https://github.com/yourusername/name-address-validator/releases",
    },
)