"""Runs basic tests for all `vhdmmio`'s generators."""

import os
from os.path import join as pjoin
import tempfile
from unittest import TestCase
from vhdmmio import run_cli

class TestVhdlPaths(TestCase):
    """Runs basic tests for all `vhdmmio`'s generators."""

    @staticmethod
    def _list_files(base):
        """Lists the files in the given directory."""
        return sorted((
            os.path.relpath(pjoin(directory, filename), base)
            for directory, _, filenames in os.walk(base)
            for filename in filenames))

    def test_package_default(self):
        """test package output in default directory"""
        with tempfile.TemporaryDirectory() as base:
            cwd = os.getcwd()
            try:
                os.chdir(base)
                self.assertEqual(run_cli(['-P']), 0)
            finally:
                os.chdir(cwd)
            self.assertEqual(self._list_files(base), ['vhdmmio_pkg.gen.vhd'])

    def test_package_custom(self):
        """test package output in specified directory"""
        with tempfile.TemporaryDirectory() as base:
            cwd = os.getcwd()
            try:
                os.chdir(base)
                self.assertEqual(run_cli(['-P', 'a/b']), 0)
            finally:
                os.chdir(cwd)
            self.assertEqual(self._list_files(base), ['a/b/vhdmmio_pkg.gen.vhd'])

    def test_html_default(self):
        """test HTML output in default directory"""
        with tempfile.TemporaryDirectory() as base:
            cwd = os.getcwd()
            try:
                os.chdir(base)
                self.assertEqual(run_cli(['-H']), 0)
            finally:
                os.chdir(cwd)
            self.assertEqual(self._list_files(base), [
                'vhdmmio-doc/index.html',
                'vhdmmio-doc/style.css'])

    def test_html_custom(self):
        """test HTML output in specified directory"""
        with tempfile.TemporaryDirectory() as base:
            cwd = os.getcwd()
            try:
                os.chdir(base)
                self.assertEqual(run_cli(['-H', 'a/b']), 0)
            finally:
                os.chdir(cwd)
            self.assertEqual(self._list_files(base), [
                'a/b/index.html',
                'a/b/style.css'])
