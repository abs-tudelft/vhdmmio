"""Tests the `@` functionality of the VHDL output paths of the CLI."""

import os
from os.path import join as pjoin
import tempfile
from unittest import TestCase
from vhdmmio import run_cli

class TestVhdlPaths(TestCase):
    """Tests the `@` functionality of the VHDL output paths of the CLI."""

    @staticmethod
    def _gen_structure(base, *filenames):
        """Generates a directory structure with some trivial register file
        descriptions."""
        for filename in filenames:
            name = os.path.basename(filename).split('.')[0]
            filename = pjoin(base, filename)
            output_dir = os.path.dirname(filename)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(filename, 'w') as fil:
                fil.write('metadata:\n  name: %s\n' % name)

    @staticmethod
    def _list_files(base):
        """Lists the files in the given directory."""
        return sorted((
            os.path.relpath(pjoin(directory, filename), base)
            for directory, _, filenames in os.walk(base)
            for filename in filenames))

    def _test_internal(
            self, gen_args, input_files, expected_output_files,
            specify_files=False, absolute=False):
        """Tests the given vhdmmio CLI argument list against the given input
        files."""
        input_files = list(input_files)
        with tempfile.TemporaryDirectory() as base:
            self._gen_structure(base, *input_files)
            cwd = os.getcwd()
            try:
                os.chdir(base)
                if specify_files:
                    if absolute:
                        file_args = [os.path.join(base, filename) for filename in input_files]
                    else:
                        file_args = input_files
                elif absolute:
                    file_args = [base]
                else:
                    file_args = []
                self.assertEqual(run_cli(file_args + gen_args), 0)
            finally:
                os.chdir(cwd)
            actual_output_files = []
            for filename in self._list_files(base):
                if filename in input_files:
                    input_files.remove(filename)
                else:
                    actual_output_files.append(filename)
            self.assertEqual(input_files, [])
            self.assertEqual(actual_output_files, expected_output_files)

    def _test(self, args, input_files, expected_output_files):
        """Tests the vhdmmio CLI with the given arguments and various
        permutations of the YAML input file specification against the given
        input files."""
        self._test_internal(args, input_files, expected_output_files, False, False)
        self._test_internal(args, input_files, expected_output_files, False, True)
        self._test_internal(args, input_files, expected_output_files, True, False)
        self._test_internal(args, input_files, expected_output_files, True, True)

    def test_default(self):
        """test CLI default VHDL output directory"""
        self._test(
            ['-V'],
            [
                'a.mmio.yaml',
                'x/b.mmio.yaml',
                'x/y/c.mmio.yaml',
                'z/v/d.mmio.yaml',
            ], [
                'a.gen.vhd',
                'a_pkg.gen.vhd',
                'x/b.gen.vhd',
                'x/b_pkg.gen.vhd',
                'x/y/c.gen.vhd',
                'x/y/c_pkg.gen.vhd',
                'z/v/d.gen.vhd',
                'z/v/d_pkg.gen.vhd',
            ])

    def test_fixed(self):
        """test CLI fixed VHDL output directory"""
        self._test(
            ['-V', 'test'],
            [
                'a.mmio.yaml',
                'x/b.mmio.yaml',
                'x/y/c.mmio.yaml',
                'z/v/d.mmio.yaml',
            ], [
                'test/a.gen.vhd',
                'test/a_pkg.gen.vhd',
                'test/b.gen.vhd',
                'test/b_pkg.gen.vhd',
                'test/c.gen.vhd',
                'test/c_pkg.gen.vhd',
                'test/d.gen.vhd',
                'test/d_pkg.gen.vhd',
            ])

    def test_relative_subfolder(self):
        """test CLI VHDL output directory with relative subfolder"""
        self._test(
            ['-V', '@/test'],
            [
                'a.mmio.yaml',
                'x/b.mmio.yaml',
                'x/y/c.mmio.yaml',
                'z/v/d.mmio.yaml',
            ], [
                'test/a.gen.vhd',
                'test/a_pkg.gen.vhd',
                'x/test/b.gen.vhd',
                'x/test/b_pkg.gen.vhd',
                'x/y/test/c.gen.vhd',
                'x/y/test/c_pkg.gen.vhd',
                'z/v/test/d.gen.vhd',
                'z/v/test/d_pkg.gen.vhd',
            ])

    def test_suffix(self):
        """test CLI VHDL output directory with suffix"""
        self._test(
            ['-V', '@test'],
            [
                'a.mmio.yaml',
                'x/b.mmio.yaml',
                'x/y/c.mmio.yaml',
                'z/v/d.mmio.yaml',
            ], [
                'test/a.gen.vhd',
                'test/a_pkg.gen.vhd',
                'x/ytest/c.gen.vhd',
                'x/ytest/c_pkg.gen.vhd',
                'xtest/b.gen.vhd',
                'xtest/b_pkg.gen.vhd',
                'z/vtest/d.gen.vhd',
                'z/vtest/d_pkg.gen.vhd',
            ])

    def test_fixed_subfolder(self):
        """test CLI VHDL output directory with fixed subfolder"""
        self._test(
            ['-V', 'test/@'],
            [
                'a.mmio.yaml',
                'x/b.mmio.yaml',
                'x/y/c.mmio.yaml',
                'z/v/d.mmio.yaml',
            ], [
                'test/a.gen.vhd',
                'test/a_pkg.gen.vhd',
                'test/x/b.gen.vhd',
                'test/x/b_pkg.gen.vhd',
                'test/x/y/c.gen.vhd',
                'test/x/y/c_pkg.gen.vhd',
                'test/z/v/d.gen.vhd',
                'test/z/v/d_pkg.gen.vhd',
            ])

    def test_prefix(self):
        """test CLI VHDL output directory with prefix"""
        self._test(
            ['-V', 'test@'],
            [
                'a.mmio.yaml',
                'x/b.mmio.yaml',
                'x/y/c.mmio.yaml',
                'z/v/d.mmio.yaml',
            ], [
                'test/a.gen.vhd',
                'test/a_pkg.gen.vhd',
                'testx/b.gen.vhd',
                'testx/b_pkg.gen.vhd',
                'testx/y/c.gen.vhd',
                'testx/y/c_pkg.gen.vhd',
                'testz/v/d.gen.vhd',
                'testz/v/d_pkg.gen.vhd',
            ])
