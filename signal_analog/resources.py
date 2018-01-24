import requests
import json
import signal_analog.util as util

__SIGNALFX_API_ENDPOINT__ = 'https://api.signalfx.com/v2'


class Resource(object):

    def __init__(self, base_url=__SIGNALFX_API_ENDPOINT__, endpoint='/',
                 api_token=None, session=None):
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
            session: optional session harness for making API requests. Mostly
                     used in test scenarios.
        """

        # Users may want to provide this via the `with_*` builder instead of
        # at resource creation time, so we shouldn't throw an error if they
        # don't pass one in at this point.
        if api_token is not None:
            self.__set_api_token__(api_token)

        if session:
            self.session_handler = session
        else:
            self.session_handler = requests.Session()

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

    def __action__(self, action, endpoint, update_fn,
                    params=None, dry_run=False, interactive=False, force=False):
        """Perform a stateful HTTP action against the SignalFx API.

        Arguments:
            action: the action to take
            update_fn: callback allowing modification of the payload before
                       sending to SignalFx.
            dry_run: When true, this resource prints its configured state
                     without calling SignalFx.
            interactive: When true, this resource asks the caller which version
                         resource to modify.
            force: When true, this resource modifies itself in SignalFx
                   disregarding previous SignalFx state.

            Returns:
                The JSON response if successful.

            Raises:
                HTTPError: when a network exception ocurred
        """
        util.is_valid(self.options)

        if dry_run:
            opts = dict(self.options)
            if self.options.get('charts', []):
                opts.update({'charts': util.flatten_charts(self.options)})
            return opts

        util.is_valid(self.api_token)

        response = self.session_handler.request(
            action,
            url=self.base_url + endpoint,
            params=params,
            json=update_fn(self.options),
            headers={
                'X-SF-Token': self.api_token,
                'Content-Type': 'application/json'
            })

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            # Tell the user exactly what went wrong according to SignalFX
            raise RuntimeError(error.response.text)

        return response.json()

    def create(self, dry_run=False, interactive=False, force=False):
        """Default implementation for resource creation."""
        return self.__action__('post', self.endpoint, lambda x: x,
            params=None, dry_run=dry_run, interactive=interactive, force=force)
