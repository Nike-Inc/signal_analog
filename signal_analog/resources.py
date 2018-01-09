import requests
import json
import signal_analog.util as util

__SIGNALFX_API_ENDPOINT__ = 'https://api.signalfx.com/v2'


class Resource(object):

    def __init__(self, base_url=__SIGNALFX_API_ENDPOINT__, endpoint='/',
                 api_token=None):
        """Encapsulation for resources that can exist in the SignalFx API.

        This version of the Resource class does not manage any state with the
        upstream API. That is, if you create a resource, and then create it
        again, duplicates WILL be created. A state management solution may be
        in the cards for a future iteration, but the opportunity cost is not
        quite there yet.

        Attributes:
            base_url: the base endpoint to use when talking to SignalFx
            endpoint: the particular endpoint to hit for this resource
            api_token: the api token to authenticate requests with
        """

        # Users may want to provide this via the `with_*` builder instead of
        # at resource creation time, so we shouldn't throw an error if they
        # don't pass one in at this point.
        if api_token is not None:
            self.__set_api_token__(api_token)

        self.__set_endpoint__(endpoint)
        self.__set_base_url__(base_url)

    def __set_api_token__(self, token):
        """Internal helper for setting valid API tokens."""

        message = """Cannot proceed with an empty API token.
        Either pass one in at Resource instantiation time or provide one
        via the `with_api_token` method."""

        util.is_valid(token, message)
        self.api_token = token

    def __set_endpoint__(self, endpoint):
        """Internal helper for setting valid endpoints."""
        util.is_valid(endpoint,  "Cannot proceed with an empty endpoint")
        self.endpoint = endpoint

    def __set_base_url__(self, base_url):
        """Internal helper for setting valid base_urls."""
        util.is_valid(base_url, "Cannot proceed with empty base_url")
        self.base_url = base_url

    def with_api_token(self, token):
        """Set the API token for this resource."""

        self.__set_api_token__(token)
        return self

    def create(self, dry_run=False):
        """Create this resource in the SignalFx API.

        Arguments:
            dry_run: Boolean indicator for a dry-run. When true, this resource
                     will print its configured state and not actually call the
                     SignalFX API.  Default is false.

        Returns:
            The JSON response if successful, None otherwise. For exceptional
            (400-500) responses an exception will be raised.
            When dry_run is true, exception is not raised when API key is
            missing.
        """

        util.is_valid(self.options)

        if dry_run is False:
            # TODO figure out better abstraction for validating pre_conditions
            util.is_valid(self.api_token)

            response = requests.post(
                url=self.base_url + self.endpoint,
                data=json.dumps(self.options),
                headers={
                    'X-SF-Token': self.api_token,
                    'Content-Type': 'application/json'
                }
            )

            try:
                # Throw an exception if we received a non-2xx response.
                response.raise_for_status()
            except requests.exceptions.HTTPError as error:
                # Tell the user exactly what went wrong according to SignalFx
                raise RuntimeError(error.response.text)

            # Otherwise, return our status code
            return response.json()
        else:
            return json.dumps(self.options)

    def update(self, dry_run=False):
        """Update this resource in the SignalFx API.

        Arguments:
            dry_run: Boolean indicator for a dry-run. When true, this resource
                     will print its configured state and not actually call the
                     SignalFX API.  Default is false.

        Returns:
            The JSON response if successful, None otherwise. For exceptional
            (400-500) responses an exception will be raised.
            When dry_run is true, exception is not raised when API key is
            missing.
        """

        util.is_valid(self.options)

        if dry_run is False:
            # TODO figure out better abstraction for validating pre_conditions
            util.is_valid(self.api_token)

            response = requests.put(
                url=self.base_url + self.endpoint(),
                data=json.dumps(self.options),
                headers={
                    'X-SF-Token': self.api_token,
                    'Content-Type': 'application/json'
                }
            )

            try:
                # Throw an exception if we received a non-2xx response.
                response.raise_for_status()
            except requests.exceptions.HTTPError as error:
                # Tell the user exactly what went wrong according to SignalFx
                raise RuntimeError(error.response.text)

            # Otherwise, return our status code
            return response.json()
        else:
            return json.dumps(self.options)

