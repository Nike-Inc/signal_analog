
class SignalAnalogError(Exception):
    """Base exception for any invalid states in the Signal Analog library."""
    pass


class DashboardMatchNotFoundError(SignalAnalogError):

    def __init__(self, dashboard_name):
        error_msg = 'Could not find an exact match for "{0}" in SignalFx.'
        super(DashboardMatchNotFoundError, self).__init__(
            error_msg.format(dashboard_name))


class DashboardAlreadyExistsError(SignalAnalogError):

    def __init__(self, name):
        # TODO this error message should be updated to add hints about a
        # --force option when it becomes implemented.
        error_msg = 'A dashboard with the name "{0}" already exists. ' +\
            'Unwilling to override.'
        super(DashboardAlreadyExistsError, self).__init__(
            error_msg.format(name))


class DashboardHasMultipleExactMatchesError(SignalAnalogError):

    def __init__(self, dashboard_name):
        error_msg = '"{0}" has more than one exact match in SignalFx. ' +\
            'Unwilling to choose a dashboard at random.'
        super(DashboardHasMultipleExactMatchesError, self).__init__(
            error_msg.format(dashboard_name))
