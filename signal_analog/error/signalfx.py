"""Errors specific to SignalFx API interactions."""


class SignalFxError(Exception):
    """Base exception for any SignalFx API errors."""

    pass


class ResourceNotFound(SignalFxError):
    """The given resource was not found in SignalFx."""

    def __init__(self, endpoint):
        msg = f"Could not find resource at endpoint '{endpoint}' in SignalFx."
        super(ResourceNotFound, self).__init__(msg)


class Unauthorized(SignalFxError):
    """The given request did not successfully authenticate with SignalFx."""

    def __init__(self):
        msg = (
            "The provided token was not able to be used to authenticate"
            + "successfully with SignalFx. Have you made sure that:\n\t"
            + "- The token is correct?\n\t"
            + "- The token is active?\n\t"
            + "- There are no extra whitespace characters in the token?"
        )
        super(Unauthorized, self).__init__(msg)
