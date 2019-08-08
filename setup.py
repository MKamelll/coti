# Imports
import setuptools
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent

# Load requirements
with open(PROJECT_ROOT / "requirements.txt") as f:
    INSTALL_REQUIRES = f.read().splitlines()

# # Setup
setuptools.setup(
    name='coti',
    version='1.0',
    description='Tweet media from a Url',
    packages=setuptools.find_packages('src'),
    url='https://github.com/MKamelll/coti',
    python_requires=">=3.7",
    entry_points={
        "console_scripts": ["coti = src.app:main"],
    },
    install_requires=INSTALL_REQUIRES
)
