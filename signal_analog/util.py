"""Methods useful throughout the signal_analog project."""


def in_given_enum(value, enum):
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
