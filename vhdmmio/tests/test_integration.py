from unittest import TestCase, skipIf
import os
import tempfile
import yaml

from vhdmmio.core.regfile import RegisterFile
from vhdmmio.vhdl import generate as generate_vhdl
from vhdmmio.html import generate as generate_html
import vhdeps
import difflib
import copy

_TEST_YAML = """
meta:
  mnemonic: SSP
  name: test_primitive
  doc: |
    This memory map includes all standard types of primitive fields for
    vhdmmio testing purposes.

features:
  bus-width: 32

interface:
  port-group: reg
  port-flatten: record
  generic-flatten: record

interrupts:

- name: test
- name: hello
  width: 5

fields:

- register-name: constant

  address: 0x0000:0
  type: constant
  name: constant_ss
  value: 1

- address: 0x0000:7..1
  type: constant
  name: constant_sv
  value: 42

- address: 0x0000:8
  repeat: 8
  field-repeat: 8
  type: constant
  name: constant_vs
  value: 0

- address: 0x0000:23..16
  repeat: 2
  field-repeat: 2
  type: constant
  name: constant_vv
  value: 33

- register-name: config

  address: 0x0008:0
  type: config
  name: config_ss

- address: 0x0008:7..1
  type: config
  name: config_sv

- address: 0x0008:8
  repeat: 8
  field-repeat: 8
  type: config
  name: config_vs

- address: 0x0008:23..16
  repeat: 2
  field-repeat: 2
  type: config
  name: config_vv

- register-name: status

  address: 0x0010:0
  type: status
  name: status_ss

- address: 0x0010:7..1
  type: status
  name: status_sv

- address: 0x0010:8
  repeat: 8
  field-repeat: 8
  type: status
  name: status_vs

- address: 0x0010:23..16
  repeat: 2
  field-repeat: 2
  type: status
  name: status_vv

- register-name: latching

  address: 0x0018:0
  type: latching
  name: latching_ss

- address: 0x0018:7..1
  type: latching
  name: latching_sv

- address: 0x0018:8
  repeat: 8
  field-repeat: 8
  type: latching
  name: latching_vs

- address: 0x0018:23..16
  repeat: 2
  field-repeat: 2
  type: latching
  name: latching_vv

- register-name: stream_to_mmio

  address: 0x0020:0
  type: stream-to-mmio
  name: stream_to_mmio_ss

- address: 0x0028
  type: stream-to-mmio
  name: stream_to_mmio_sv

- address: 0x0030:0
  repeat: 2
  field-repeat: 1
  type: stream-to-mmio
  name: stream_to_mmio_vs

- address: 0x0040
  repeat: 2
  field-repeat: 1
  type: stream-to-mmio
  name: stream_to_mmio_vv

- register-name: mmio_to_stream

  address: 0x0050:0
  type: mmio-to-stream
  name: mmio_to_stream_ss

- address: 0x0058
  type: mmio-to-stream
  name: mmio_to_stream_sv

- address: 0x0060:0
  repeat: 2
  field-repeat: 1
  type: mmio-to-stream
  name: mmio_to_stream_vs

- address: 0x0070
  repeat: 2
  field-repeat: 1
  type: mmio-to-stream
  name: mmio_to_stream_vv

- register-name: control

  address: 0x0080:0
  type: control
  name: control_ss

- address: 0x0080:7..1
  type: control
  name: control_sv

- address: 0x0080:8
  repeat: 8
  field-repeat: 8
  type: control
  name: control_vs

- address: 0x0080:23..16
  repeat: 2
  field-repeat: 2
  type: control
  name: control_vv

- register-name: flag

  address: 0x0088:0
  type: flag
  name: flag_ss

- address: 0x0088:7..1
  type: flag
  name: flag_sv

- address: 0x0088:8
  repeat: 8
  field-repeat: 8
  type: flag
  name: flag_vs

- address: 0x0088:23..16
  repeat: 2
  field-repeat: 2
  type: flag
  name: flag_vv

- register-name: volatile_flag

  address: 0x0090:0
  type: volatile-flag
  name: volatile_flag_ss

- address: 0x0090:7..1
  type: volatile-flag
  name: volatile_flag_sv

- address: 0x0090:8
  repeat: 8
  field-repeat: 8
  type: volatile-flag
  name: volatile_flag_vs

- address: 0x0090:23..16
  repeat: 2
  field-repeat: 2
  type: volatile-flag
  name: volatile_flag_vv

- register-name: reverse_flag

  address: 0x0098:0
  type: reverse-flag
  name: reverse_flag_ss

- address: 0x0098:7..1
  type: reverse-flag
  name: reverse_flag_sv

- address: 0x0098:8
  repeat: 8
  field-repeat: 8
  type: reverse-flag
  name: reverse_flag_vs

- address: 0x0098:23..16
  repeat: 2
  field-repeat: 2
  type: reverse-flag
  name: reverse_flag_vv

- register-name: counter

  address: 0x00A0:0
  type: counter
  name: counter_ss

- address: 0x00A0:7..1
  type: counter
  name: counter_sv

- address: 0x00A0:8
  repeat: 8
  field-repeat: 8
  type: counter
  name: counter_vs

- address: 0x00A0:23..16
  repeat: 2
  field-repeat: 2
  type: counter
  name: counter_vv

- register-name: volatile_counter

  address: 0x00A8:0
  type: volatile-counter
  name: volatile_counter_ss

- address: 0x00A8:7..1
  type: volatile-counter
  name: volatile_counter_sv

- address: 0x00A8:8
  repeat: 8
  field-repeat: 8
  type: volatile-counter
  name: volatile_counter_vs

- address: 0x00A8:23..16
  repeat: 2
  field-repeat: 2
  type: volatile-counter
  name: volatile_counter_vv

- register-name: reverse_counter

  address: 0x00B0:0
  type: reverse-counter
  name: reverse_counter_ss

- address: 0x00B0:7..1
  type: reverse-counter
  name: reverse_counter_sv

- address: 0x00B0:8
  repeat: 8
  field-repeat: 8
  type: reverse-counter
  name: reverse_counter_vs

- address: 0x00B0:23..16
  repeat: 2
  field-repeat: 2
  type: reverse-counter
  name: reverse_counter_vv
"""

class TestIntegration(TestCase):

    @skipIf('ENABLE_LENGTHY' not in os.environ, '$ENABLE_LENGTHY not set')
    def test_integration(self):
        self.maxDiff = None
        for group in [False, 'reg']:
            for flatten in ['all', 'record', 'never']:
                if hasattr(yaml, 'safe_load'):
                    spec = yaml.safe_load(_TEST_YAML)
                else:
                    spec = yaml.load(_TEST_YAML)
                spec['interface']['port-group'] = group
                spec['interface']['port-flatten'] = flatten

                regfile = RegisterFile.from_dict(spec)

                with tempfile.TemporaryDirectory() as tempdir:
                    generate_vhdl([regfile], tempdir)
                    generate_html([regfile], tempdir)
                    run_a = ''
                    for name in sorted(os.listdir(tempdir)):
                        with open(tempdir + os.sep + name, 'r') as fil:
                            run_a += fil.read()
                    self.assertEqual(vhdeps.run_cli(['ghdl', '-i', tempdir]), 0)

                spec = regfile.to_dict()
                regfile = RegisterFile.from_dict(spec)

                with tempfile.TemporaryDirectory() as tempdir:
                    generate_vhdl([regfile], tempdir)
                    generate_html([regfile], tempdir)
                    run_b = ''
                    for name in sorted(os.listdir(tempdir)):
                        with open(tempdir + os.sep + name, 'r') as fil:
                            run_b += fil.read()

                if run_a != run_b:
                    print('\n'.join(difflib.ndiff(run_a.split('\n'), run_b.split('\n'))))
                    self.assertTrue(False)
