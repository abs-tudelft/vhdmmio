import os
from setuptools import setup

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name = "vhdmmio",
    version = "0.0.1",
    author = "Jeroen van Straten",
    author_email = "j.vanstraten-1@tudelft.nl",
    description = (
        "VHDL code generator for AXI4-lite compatible memory-mapped I/O (MMIO)"
        "register files and bus infrastructure."
    ),
    license = "Apache 2.0",
    keywords = "vhdl mmio registers generator",
    url = "http://packages.python.org/vhdmmio",
    packages=['vhdmmio'],
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: Apache Software License",
    ],
)
