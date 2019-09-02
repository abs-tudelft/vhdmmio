"""Submodule for adding all the configuration loading and reconstruction
boilerplate code to classes that must be (de)serializable through
metaprogramming, as well as generation of markdown documentation for the
resulting configuration file syntax."""

# Re-export the classes, functions, and decorators intended to be used by users
# of this submodule.
from .configurable import Configurable, configurable, derive, document_configurables
from .choice import choice, required_choice, choice_default, flag
from .checked import checked, opt_checked
from .subconfig import subconfig, opt_subconfig, embedded, opt_embedded
from .listconfig import listconfig, protolistconfig
from .select import select
from .utils import ParseError, Unset
