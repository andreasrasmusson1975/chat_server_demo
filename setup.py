"""
Setup script for the chat_server_demo package.
==============================================

This script configures the installation, packaging, and entry points for the chat_server_demo
application. It uses setuptools to define package metadata, dependencies, and the main console
script for launching the Streamlit-based chat server demo.

Usage
-----
- Install the package locally: `pip install .`
- Build a distribution: `python setup.py sdist bdist_wheel`
- Launch the app: `start_app` (after installation)

See the README.md for more details on usage and development.
"""
from setuptools import setup, find_packages

setup(
    name="chat_server_demo",
    version="0.1.0",
    description="A streamlit demo using a chat server.",
    author="Andreas Rasmusson",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "start_app = chat_server_demo.app.launcher:run",
            "create_db = chat_server_demo.database.create_db:main"
        ]
    },
    include_package_data=True,
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
