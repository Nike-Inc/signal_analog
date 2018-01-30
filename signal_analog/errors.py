
class SignalAnalogError(Exception):
    """Base exception for any invalid states in the Signal Analog library."""
    pass

class ResourceMatchNotFoundError(SignalAnalogError):
    def __init__(self, resource_name):
        msg = 'Could not find an exact match for "{0}" in SignalFx.'
        super(ResourceMatchNotFoundError, self).__init__(
            msg.format(resource_name))

class ResourceAlreadyExistsError(SignalAnalogError):

    def __init__(self, name):
        # TODO this error message should be updated to add hints about a
        # --force option when it becomes implemented.
        error_msg = """
    A resource with the name "{0}" already exists.
    Unwilling to override. If you are creating a Dashboard you may try
    setting the `force` keyword argument to True to override this
    behavior.
        """
        super(ResourceAlreadyExistsError, self).__init__(
            error_msg.format(name))


class ResourceHasMultipleExactMatchesError(SignalAnalogError):

    def __init__(self, dashboard_name):
        error_msg = """
    "{0}" has more than one exact match in SignalFx. Unwilling to choose a
    resource at random.
        """
        super(ResourceHasMultipleExactMatchesError, self).__init__(
            error_msg.format(dashboard_name))
