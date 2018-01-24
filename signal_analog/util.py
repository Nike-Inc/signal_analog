"""Methods useful throughout the signal_analog project."""

from collections import Counter


def in_given_enum(value, enum):
    """Determines if the given value is in the given enum. Raises ValueError
       if it is not.
    """
    if type(value) != enum or value not in enum:
        msg = '"{0}" must be one of {1}.'
        valid_values = [x.value for x in enum]
        raise ValueError(msg.format(value, valid_values))


def is_valid(value, error_message=None):
    """Void method ensuring value is non-empty.

    Arguments:
        value: the value to check
        error_message: an optional error message to provide the user

    Returns:
        Nothing.
    """
    if not value:
        if error_message:
            raise ValueError(error_message)
        else:
            raise ValueError()


def find_duplicates(xs):
    return [item for item, count in Counter(xs).items() if count > 1]

def flatten_charts(opts):
    """Given an options object, return a list of JSON-serialized chart objects.

    Arguments:
        opts: a Resource chart object

    Returns:
        A list of charts serialized as JSON objects.
    """
    return list(map(lambda c: c.to_dict(), opts.get('charts', [])))
