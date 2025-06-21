"""
Smart Debugger - Project-Agnostic Pytest Debugging Tool
A standalone debugger for pytest that works with any Python project
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart-debugger",
    version="0.1.0",
    author="Smart Debugger Team",
    description="Project-agnostic pytest debugger with intelligent object analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/smart-debugger",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pytest>=7.0.0,<8.0.0",
        "networkx>=2.6.0,<4.0.0",
        "pandas>=1.3.0,<3.0.0",
        "numpy>=1.20.0,<2.0.0",
    ],
    extras_require={
        "dev": [
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
            "flake8>=4.0.0",
            "autoflake>=1.4.0",
            "types-requests",
            "pandas-stubs",
        ]
    },
    entry_points={
        "console_scripts": [
            "smart-debugger=smart_debugger.pytest_breakrepl:main",
        ],
    },
)