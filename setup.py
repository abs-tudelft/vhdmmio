#!/usr/bin/env python3

import os
from setuptools import setup
from setuptools.command.test import test as TestCommand

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

class NoseTestCommand(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Run nose ensuring that argv simulates running nosetests directly
        import nose
        nose.run_exit(argv=['nosetests'])

setup(

    # Metadata
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
    long_description = read('README.md'),
    long_description_content_type = 'text/markdown',
    classifiers = [
        "Development Status :: 1 - Planning",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: Apache Software License",
    ],
    packages = ['vhdmmio'],

    # Install dependencies
    install_requires = ['pyyaml'],

    # Testing
    tests_require = ['nose', 'coverage'],
    cmdclass = {'test': NoseTestCommand},

    # Setup dependencies
    setup_requires = ['setuptools-lint', 'pylint']

)
