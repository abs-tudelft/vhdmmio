"""Submodule for primitive field behavior VHDL code generation."""

from .base import BehaviorCodeGen, behavior_code_gen
from ...core.behavior import PrimitiveBehavior

@behavior_code_gen(PrimitiveBehavior)
class PrimitiveBehaviorCodeGen(BehaviorCodeGen):
    """Behavior code generator class for primitive fields."""

    def generate(self):
        """Code generator implementation."""
        # TODO
