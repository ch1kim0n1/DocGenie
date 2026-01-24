"""
DocGenie - Auto-documentation tool for codebases
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="docgenie",
    version="1.0.0",
    author="DocGenie Team",
    author_email="contact@docgenie.dev",
    description="Auto-documentation tool that generates comprehensive README files and HTML documentation for any codebase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/docgenie/docgenie",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "docgenie=docgenie.cli:main",
            "docgenie-html=convert_to_html:convert_to_html",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
