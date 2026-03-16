#!/usr/bin/env python3
"""Setup script for SimpleMail."""

from setuptools import setup, find_packages

setup(
    name="simplemail",
    version="1.0.0",
    description="Tillgänglig e-postklient med piktogramstöd och uppläsning",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SimpleMail Team",
    license="GPL-3.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "simplemail": [
            "locale/*/LC_MESSAGES/*.mo",
            "icons/*.svg",
        ],
    },
    data_files=[
        ("share/applications", ["data/simplemail.desktop"]),
        ("share/icons/hicolor/scalable/apps", ["data/icons/simplemail.svg"]),
    ],
    entry_points={
        "console_scripts": [
            "simplemail=simplemail.app:main",
        ],
    },
    install_requires=[
        "PyGObject>=3.42.0",
        "pycairo>=1.20.0",
        "pyttsx3>=2.90",
        "keyring>=23.0.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: Swedish",
        "Programming Language :: Python :: 3",
        "Topic :: Communications :: Email",
    ],
)
