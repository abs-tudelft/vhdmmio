"""Module for miscellaneous utilities."""

def doc_enumerate(items, connect_with='and', map_using=str, default='<null>'):
    """Enumerates a list of items using natural English. That is, `'[0]'`,
    `'[0] and [1]'`, , `'[0], [1] and [2]'`, and so on. The connecting word is
    specified using `connect_with` and defaults to `'and'`. Optionally, objects
    can be mapped to a string using a function other than `str` by specifying
    `map_using`. If no items are specified, `default` is returned."""
    items = list(items)
    if not items:
        return default
    if len(items) == 1:
        return map_using(items[0])
    if len(items) == 2:
        return '%s %s %s' % (
            map_using(items[0]),
            connect_with,
            map_using(items[1]))
    return '%s %s %s' % (
        ', '.join(map(map_using, items[:-1])),
        connect_with,
        map_using(items[-1]))
