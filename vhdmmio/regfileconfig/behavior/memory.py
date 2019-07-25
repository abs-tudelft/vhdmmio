"""Submodule for `Memory` configurable."""

from ...config import configurable, Configurable
from .registry import behavior, behavior_doc

behavior_doc('Fields for interfacing with memories:')

@behavior(
    'memory', 'not yet implemented!', 1)
@configurable(name='`axi` behavior')
class Memory(Configurable):
    """Not yet implemented!""" # TODO
    #pylint: disable=E0211,E0213
