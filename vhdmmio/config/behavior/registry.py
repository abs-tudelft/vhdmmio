"""Registry for behavior configurables."""

_BEHAVIOR_LIST = []

def behaviors():
    """Yields the currently registered behaviors in the order in which they
    were defined."""
    for name, cls, brief, level in _BEHAVIOR_LIST:
        yield name, cls, brief, level

def behavior(name, brief, level=0):
    """Decorator generator which registers a behavior configurable."""
    def decorator(cls):
        cls.__str__ = lambda _: name
        _BEHAVIOR_LIST.append((name, cls, brief, level))
        return cls
    return decorator

def behavior_doc(doc, level=0):
    """Appends a documentation-only item to the behavior list in the generated
    documentation."""
    _BEHAVIOR_LIST.append((None, None, doc, level))
