
vhdMMIO
=======

[![PyPi](https://badgen.net/pypi/v/vhdmmio)](https://pypi.org/project/vhdmmio/)
[![Documentation](https://badgen.net/badge/documentation/%20/green)](https://abs-tudelft.github.io/vhdmmio/)
[![Build Status](https://dev.azure.com/abs-tudelft/vhdmmio/_apis/build/status/abs-tudelft.vhdmmio?branchName=master)](https://dev.azure.com/abs-tudelft/vhdmmio/_build/latest?definitionId=4&branchName=master)
[![codecov](https://codecov.io/gh/abs-tudelft/vhdmmio/branch/master/graph/badge.svg)](https://codecov.io/gh/abs-tudelft/vhdmmio)
[![License](https://badgen.net/github/license/abs-tudelft/vhdmmio)](https://github.com/abs-tudelft/vhdmmio/blob/master/LICENSE)

vhdMMIO is a fully vendor-agnostic tool to build AXI4-lite MMIO
infrastructure with, based on easy-to-write YAML specification files. For
instance:

```yaml
metadata:
  name: basic

fields:

  - address: 0
    name: ctrl
    behavior: control

  - address: 4
    name: stat
    behavior: status

  - address: 0x1---
    name: slv_a
    behavior: axi
```

gives you a VHDL file with a 32-bit output for the control register at address
0x0000, a 32-bit input for the status register at address 0x0004, and a slave
AXI4-lite bus mapped to address 0x1000 through 0x1FFF. vhdMMIO also generates
documentation, ensuring that it stays up-to-date. We aim to generate at least
C header files in the future as well, but this is currently not implemented.

Installation
------------

While the project is very much in alpha, it is already usable and fairly
stable. Installation can be done through pip:

    pip3 install vhdmmio

This installs the `vhdmmio` command-line tool and the Python 3 library it
wraps. Basic usage of the command-line tool is just

    vhdmmio -H -P -V

which searches the current working directory for `*.mmio.yaml` files, and
generates HTML documentation into `./vhdmmio-doc` (`-H`), generates the common
vhdMMIO package file - `vhdmmio_pkg.gen.vhd` - in the current working directory
(`-P`), and generates the custom VHDL package and entity for each YAML file in
the same directory as the YAML file (`-V`).

Documentation
-------------

Most of vhdMMIO's documentation is concerned with the structure of the YAML
configuration files. You can find this
[here](https://abs-tudelft.github.io/vhdmmio/).
You can also find example register file descriptions
[here](https://github.com/abs-tudelft/vhdmmio/tree/master/examples).
