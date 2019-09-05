"""Integration tests for `vhdmmio.config` and `vhdmmio.configurable`."""

import tempfile
import os
import glob
from unittest import TestCase
from vhdmmio.config import RegisterFileConfig
from vhdmmio.configurable import document_configurables

class TestConfig(TestCase):
    """Integration tests for `vhdmmio.config` and `vhdmmio.configurable`."""

    def test_real_world(self):
        """test config loader against the example yaml files"""

        examples = glob.glob(os.path.dirname(__file__) + '/../../examples/**/*.yaml')
        self.assertTrue(bool(examples))

        for example in examples:
            with tempfile.TemporaryDirectory() as base:
                regfile1 = RegisterFileConfig.load(example)
                regfile1.save(base + '/test_out1.yaml')

                with open(base + '/test_out1.yaml', 'r') as fil:
                    out1 = fil.read()

                regfile2 = RegisterFileConfig.load(base + '/test_out1.yaml')
                regfile2.save(base + '/test_out2.yaml')

                with open(base + '/test_out2.yaml', 'r') as fil:
                    out2 = fil.read()

                self.assertEqual(out1, out2)

                from vhdmmio.core import RegisterFile
                RegisterFile(regfile1, True)

    def test_docgen(self):
        """test register file documentation generation"""
        self.maxDiff = None #pylint: disable=C0103

        with tempfile.TemporaryDirectory() as base:
            document_configurables(RegisterFileConfig, '# Front page\n\nSome text.', base)

            self.assertEqual(sorted(os.listdir(base)), [
                'README.md',
                'SUMMARY.md',
                'axi.md',
                'conditionconfig.md',
                'config.md',
                'constant.md',
                'control.md',
                'counter.md',
                'custom.md',
                'custominterfaceconfig.md',
                'entityconfig.md',
                'featureconfig.md',
                'fieldconfig.md',
                'flag.md',
                'interfaceconfig.md',
                'internalcontrol.md',
                'internalcounter.md',
                'internalflag.md',
                'internalioconfig.md',
                'internalstatus.md',
                'internalstrobe.md',
                'interrupt.md',
                'interruptconfig.md',
                'interruptenable.md',
                'interruptflag.md',
                'interruptpend.md',
                'interruptraw.md',
                'interruptstatus.md',
                'interruptunmask.md',
                'latching.md',
                #'memory.md',
                'metadataconfig.md',
                'mmiotostream.md',
                'multirequest.md',
                'permissionconfig.md',
                'primitive.md',
                'registerfileconfig.md',
                'request.md',
                'status.md',
                'streamtommio.md',
                'strobe.md',
                'subaddressconfig.md',
                'volatilecounter.md',
                'volatileflag.md',
                'volatileinternalcounter.md',
                'volatileinternalflag.md',
                'volatileinterruptflag.md'])
