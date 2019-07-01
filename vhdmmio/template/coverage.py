import sys
import re
import os
import coverage

class FileTracer(coverage.FileTracer):

    def __init__(self, fname):
        super().__init__()
        self._fname = fname

    @staticmethod
    def has_dynamic_source_filename():
        return False

    def source_filename(self):
        return self._fname

    @staticmethod
    def line_number_range(frame):
        return (frame.f_lineno, frame.f_lineno)


class PythonFileReporter(coverage.python.PythonFileReporter):
    pass


class VhdlFileReporter(coverage.FileReporter):

    @staticmethod
    def _line_type(line):
        if line.startswith('$') and line.count('$') == 1:
            return 'directive'
        line = line.strip()
        if not line:
            return 'empty'
        if line.startswith('@') or line.startswith('--'):
            return 'comment'
        return 'code'

    def lines(self):
        lines = set()
        for line_no, line in enumerate(self.source().split('\n')):
            if self._line_type(line) == 'code':
                lines.add(line_no + 1)
        return lines

    def source_token_lines(self):
        for line in self.source().split('\n'):
            print(line, file=sys.stderr)
            yield ({
                'directive': 'key',
                'comment': 'com',
                'empty': 'txt',
                'code': 'txt',
            }[self._line_type(line)], line)


class CoveragePlugin(coverage.CoveragePlugin):
    def file_tracer(self, filename):
        return FileTracer(filename)

    def file_reporter(self, filename):
        if filename.endswith('.vhd') or filename.endswith('.vhdl'):
            return VhdlFileReporter(filename)
        return PythonFileReporter(filename)

    def find_executable_files(self, src_dir):
        for (dirpath, dirnames, filenames) in os.walk(src_dir):
            for filename in filenames:
                filename = os.path.join(dirpath, filename)
                if re.match(r'^[^.#~!$@%^&*()+=,]+(\.template)?\.vhdl?$', filename):
                    yield filename

def coverage_init(reg, options):
    reg.add_file_tracer(CoveragePlugin())
