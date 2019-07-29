

class CompiledRegisterFile:
    """Class for compiling a register file configuration (that is, run all
    context-sensitive checks and configuration) and representing the result.
    The compiled register file is immutable. The passed configuration object
    is frozen as well, to make sure it stays in sync with the compilation
    result."""

    def __init__(self, config):
        super().__init__()

        # Store the configuration.
        config.freeze()
        self._cfg = config

    @property
    def cfg(self):
        """Returns the frozen configuration object for this compiled register
        file."""
        return self._cfg
