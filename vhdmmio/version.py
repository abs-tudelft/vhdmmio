"""Version metadata file. This file is overridden by setuptools with the
actual version when the module is "built"."""

import os
from subprocess import Popen, PIPE


def _run_cmd(*args):
    """Runs a command using subprocess, returning a two-tuple consisting of
    the return code and a binary string containing the data written to
    stdout."""
    proc = Popen(
        args, stdin=PIPE, stdout=PIPE, stderr=PIPE,
        cwd=os.path.dirname(__file__))
    output, _ = proc.communicate()
    code = proc.returncode
    return code, output


def _get_version():
    """Attempts to get vhdmmio's version at runtime using `git`."""
    try:
        code, output = _run_cmd('git', 'describe', '--tags')
        if code:
            return 'unknown'
        output = output.decode('utf8').strip().split('-')
        if len(output) != 3:
            return 'unknown'
        version = '%s+%s' % (output[0], output[2])

        code, _ = _run_cmd('git', 'diff', '--quiet')
        if code:
            version += '+dirty'

        return version
    except OSError:
        return 'unknown'


__version__ = _get_version()
