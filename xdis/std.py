"""
Provide the same API as Python 3.x so xdis can be used as a drop in
replacement for dis. This will provide a dis module with support for the
Python version being run.

Why would you want this? The main reason is if you want a compatibility shim
for supporting the more advanced Python 3 dis API (being able to iterate through
opcodes, supplying a custom file to dump the dis to) across python versions, for
example:

    import xdis.std as dis

    # works in Python 2 and 3
    for op in dis.Bytecode('for i in range(10): pass'):
        print(op)

"""

# std
import sys
# xdis
from xdis import PYTHON_VERSION, IS_PYPY
from xdis.bytecode import Bytecode as _Bytecode, _Instruction
from xdis.main import get_opcode, disco as _disco
from xdis.util import code_info as _code_info, pretty_flags as _pretty_flags, show_code as _show_code


class _StdApi:

    def __init__(self, python_version=PYTHON_VERSION, is_pypy=IS_PYPY):

        if python_version >= 3.6:
            import xdis.wordcode as xcode
        else:
            import xdis.bytecode as xcode
        self.xcode = xcode

        self.python_version = python_version
        self.is_pypy = is_pypy
        self.opc = opc = get_opcode(python_version, is_pypy)
        self.hasconst = opc.hasconst
        self.hasname = opc.hasname
        self.opmap = opc.opmap
        self.opname = opc.opname
        self.EXTENDED_ARG = opc.EXTENDED_ARG
        self.HAVE_ARGUMENT = opc.HAVE_ARGUMENT

        class Bytecode(_Bytecode):
            """The bytecode operations of a piece of code

            Instantiate this with a function, method, string of code, or a code object
            (as returned by compile()).

            Iterating over this yields the bytecode operations as Instruction instances.
            """
            def __init__(self, x, first_line=None, current_offset=None):
                super(Bytecode, self).__init__(x, opc=opc, first_line=first_line,
                                               current_offset=current_offset)
        self.Bytecode = Bytecode

        class Instruction(_Instruction):
            """Details for a bytecode operation

               Defined fields:
                 opname - human readable name for operation
                 opcode - numeric code for operation
                 arg - numeric argument to operation (if any), otherwise None
                 argval - resolved arg value (if known), otherwise same as arg
                 argrepr - human readable description of operation argument
                 offset - start index of operation within bytecode sequence
                 starts_line - line started by this opcode (if any), otherwise None
                 is_jump_target - True if other code jumps to here, otherwise False
            """

            def __init__(self, *args, **kwargs):
                _Instruction(*args, **kwargs)
                self.opc = opc
        self.Instruction = Instruction

    def _print(self, x, file=None):
        if file is None:
            print(x)
        else:
            file.write(str(x) + '\n')

    def code_info(self, x):
        """Formatted details of methods, functions, or code."""
        return _code_info(x, self.python_version)

    def show_code(self, x, file=None):
        """Print details of methods, functions, or code to *file*.

        If *file* is not provided, the output is printed on stdout.
        """
        return _show_code(x, self.opc.version, file)

    def pretty_flags(self, flags):
        """Return pretty representation of code flags."""
        return _pretty_flags(flags)

    def dis(self, x=None, file=None):
        """Disassemble classes, methods, functions, generators, or code.

        With no argument, disassemble the last traceback.

        """
        self._print(self.Bytecode(x).dis(), file)

    def distb(self, tb=None, file=None):
        """Disassemble a traceback (default: last traceback)."""
        if tb is None:
            try:
                tb = sys.last_traceback
            except AttributeError:
                raise RuntimeError("no last traceback to disassemble")
            while tb.tb_next: tb = tb.tb_next
        self.disassemble(tb.tb_frame.f_code, tb.tb_lasti, file=file)

    def disassemble(self, code, lasti=-1, file=None):
        """Disassemble a code object."""
        return self.disco(code, lasti, file)

    def disco(self, code, lasti=-1, file=None):
        """Disassemble a code object."""
        return _disco(self.python_version, code, timestamp=0,
                      out=file, is_pypy=self.is_pypy, header=False)

    def get_instructions(self, x, first_line=None):
        """Iterator for the opcodes in methods, functions or code

        Generates a series of Instruction named tuples giving the details of
        each operations in the supplied code.

        If *first_line* is not None, it indicates the line number that should
        be reported for the first source line in the disassembled code.
        Otherwise, the source line information (if any) is taken directly from
        the disassembled code object.
        """
        return self.Bytecode(x).get_instructions(x, first_line)

    def findlinestarts(self, code):
        """Find the offsets in a byte code which are start of lines in the source.

        Generate pairs (offset, lineno) as described in Python/compile.c.

        """
        return self.xcode.findlinestarts(code)

    def findlabels(self, code):
        """Detect all offsets in a byte code which are jump targets.

        Return the list of offsets.

        """
        return self.xcode.findlabels(code, self.opc)


def make_std_api(python_version=PYTHON_VERSION, is_pypy=IS_PYPY):
    """
    Generate an object which can be used in the same way as the python
    standard dis module. The difference is that the generated 'module' can be
    used to disassemble byte / word code from a different python version than
    the version of the interpreter under which we are running.

    :param python_version: Generate a dis module for this version of python
                           (defaults to the currently running python version.)
    :param is_pypy:        True if we should generate a dis module that
                           disassembles pypy bytecode (defaults to the
                           currently running python version.)

    :return: object which can be used like the std dis module.
    """
    return _StdApi(python_version, is_pypy)


_std_api = make_std_api()

hasconst = _std_api.hasconst
hasname = _std_api.hasname
opmap = _std_api.opmap
opname = _std_api.opname
EXTENDED_ARG = _std_api.EXTENDED_ARG
HAVE_ARGUMENT = _std_api.HAVE_ARGUMENT
xcode = _std_api.xcode
opc = _std_api.opc
Bytecode = _std_api.Bytecode
Instruction = _std_api.Instruction
code_info = _std_api.code_info
_print = _std_api._print
show_code = _std_api.show_code
pretty_flags = _std_api.pretty_flags
dis = _std_api.dis
distb = _std_api.distb
disassemble = _std_api.disassemble
disco = _std_api.disco
get_instructions = _std_api.get_instructions
findlinestarts = _std_api.findlinestarts
findlabels = _std_api.findlabels
