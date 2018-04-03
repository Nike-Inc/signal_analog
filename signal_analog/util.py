"""Methods useful throughout the signal_analog project."""

import click
import json
from collections import Counter


def check_collection(coll, type_):
    """Ensure type consistency for the given collection."""
    for c in coll:
        if not issubclass(c.__class__, type_):
            msg = "We got a '{0}' when we were expecting a '{1}'."
            raise ValueError(msg.format(c.__class__.__name__, type_.__name__))


def in_given_enum(value, enum):
    """Determines if the given value is in the given enum. Raises ValueError
       if it is not.
    """
    if type(value) != enum or value not in enum:
        msg = '"{0}" must be one of {1}.'
        valid_values = [x.value for x in enum]
        raise ValueError(msg.format(value, valid_values))


def is_valid(value, error_message=None, expected_type=None):
    """Void method ensuring value is non-empty.

    Arguments:
        value: the value to check
        expected_type: expected data type of the value. Ex: bool, str
        error_message: an optional error message to provide the user

    Returns:
        Nothing.
    """
    if not value:
        if error_message:
            raise ValueError(error_message)
        else:
            raise ValueError()
    elif expected_type:
        try:
            if not isinstance(value, expected_type):
                raise ValueError('Expecting a variable of type {0}. But got a {1}("{2}")'
                                 .format(expected_type, type(value), value))
        except TypeError:
            raise ValueError('"{0}" is not a valid data type'.format(expected_type))


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


def pp_json(dictionary):
    """Pretty print a dictionary as JSON."""
    click.echo(json.dumps(dictionary, indent=2))


def empty_body():
    """Returns  an empty body when making requests to SignalFx."""
    return lambda x: None
