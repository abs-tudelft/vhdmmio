"""Submodule for parsed field behaviors."""

from .base import BehaviorCodeGen
from .primitive import PrimitiveBehaviorCodeGen
from .interrupt import InterruptBehaviorCodeGen
from .axi import AxiBehaviorCodeGen
from .custom import CustomBehaviorCodeGen
