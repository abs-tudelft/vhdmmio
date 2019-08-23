#!/usr/bin/env python3

import os
from setuptools import setup
from setuptools.command.test import test as TestCommand
from setuptools.command.build_py import build_py as BuildCommand

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

class BuildWithVersionCommand(BuildCommand):
    def run(self):
        BuildCommand.run(self)
        if not self.dry_run:
            version_fname = os.path.join(self.build_lib, 'vhdmmio', 'version.py')
            with open(version_fname, 'w') as fildes:
                fildes.write('__version__ = """' + self.distribution.metadata.version + '"""\n')

setup(
    name = 'vhdmmio',
    version_config={
        'version_format': '{tag}+{sha}',
        'starting_version': '0.0.1'
    },
    author = 'Jeroen van Straten',
    author_email = 'j.vanstraten-1@tudelft.nl',
    description = (
        'VHDL code generator for AXI4-lite compatible memory-mapped I/O (MMIO)'
        'register files and bus infrastructure.'
    ),
    license = 'Apache',
    keywords = 'vhdl mmio registers generator',
    url = 'https://github.com/abs-tudelft/vhdmmio',
    long_description = read('README.md'),
    long_description_content_type = 'text/markdown',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Generators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
    ],
    project_urls = {
        'Source': 'https://github.com/abs-tudelft/vhdmmio',
    },
    packages = [
        'vhdmmio',
        'vhdmmio.core',
        'vhdmmio.vhdl',
        'vhdmmio.html'
    ],
    include_package_data=True,
    entry_points = {'console_scripts': ['vhdmmio=vhdmmio:run_cli']},
    python_requires = '>=3',
    install_requires = [
        'pyyaml',
        'markdown2'
    ],
    setup_requires = [
        'wheel',
        'setuptools-lint',
        'pylint',
        'setuptools-git'
    ],
    tests_require = [
        'nose',
        'coverage',
        'vhdeps'
    ],
    cmdclass = {
        'test': NoseTestCommand,
        'build_py': BuildWithVersionCommand,
    },
)
