
vhdMMIO
=======

[![PyPi](https://badgen.net/pypi/v/vhdmmio)](https://pypi.org/project/vhdmmio/)
[![Build Status](https://dev.azure.com/abs-tudelft/vhdmmio/_apis/build/status/abs-tudelft.vhdmmio?branchName=master)](https://dev.azure.com/abs-tudelft/vhdmmio/_build/latest?definitionId=4&branchName=master)
[![codecov](https://codecov.io/gh/abs-tudelft/vhdmmio/branch/master/graph/badge.svg)](https://codecov.io/gh/abs-tudelft/vhdmmio)
[![License](https://badgen.net/github/license/abs-tudelft/vhdmmio)](https://github.com/abs-tudelft/vhdmmio/blob/master/LICENSE)

vhdMMIO will be a fully vendor-agnostic tool to build an AXI4-lite MMIO
infrastructure with. It will generate at least VHDL files, C header files, and
basic documentation from a single source, ensuring that these things stay in
sync and preventing you from writing massive amounts of boilerplate code for
every register file you need. Besides MMIO routing, it will also support
interrupt routing natively.

The project is currently in the planning phase.
