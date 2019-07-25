"""Generates the documentation for the register file description."""

# TODO: work in progress

from plumbum import local
from ..config import document_configurables
from .field_descriptor import FieldDescriptor

local['rm']('-rf', 'mdbook/src')
local['mkdir']('-p', 'mdbook/src')
document_configurables(FieldDescriptor, 'mdbook/src')
with local.cwd('mdbook'):
    local['mdbook']('build')
