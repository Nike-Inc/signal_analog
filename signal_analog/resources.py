import requests
import json


class Resource(object):

    def __init__(self, base_url='https://api.signalfx.com/v2', endpoint='/',
                 api_token=None, identifier=None):
        """Encapsulation for resources that can exist in the SignalFx API.

        This version of the Resource class does not manage any state with the
        upstream API. That is, if you create a resource, and then create it
        again, duplicates WILL be created. A state management solution may be
        in the cards for a future iteration, but the opportunity cost is not
        quite there yet.

        Attributes:
            TODO
        """

        # Users may want to provide this via the `with_*` builder instead of
        # at resource creation time, so we shouldn't throw an error if they
        # don't pass one in at this point.
        if api_token is not None:
            self.__set_api_token__(api_token)

        if identifier is not None:
            self.__set_id__(identifier)

        self.__set_endpoint__(endpoint)
        self.__set_base_url__(base_url)

    def is_valid(self, value, error_message=None):
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

    def __set_api_token__(self, token):
        """Internal helper for setting valid API tokens."""

        message = """Cannot proceed with an empty API token.
        Either pass one in at Resource instantiation time or provide one
        via the `with_api_token` method."""

        self.is_valid(token, message)
        self.api_token = token

    def __set_endpoint__(self, endpoint):
        """Internal helper for setting valid endpoints."""
        self.is_valid(endpoint,  "Cannot proceed with an empty endpoint")
        self.endpoint = endpoint

    def __set_base_url__(self, base_url):
        """Internal helper for setting valid base_urls."""
        self.is_valid(base_url, "Cannot proceed with empty base_url")
        self.base_url = base_url

    def __set_id__(self, identifier):
        """Internal helper for setting valid base_urls."""
        self.is_valid(identifier, "Cannot proceed with empty identifier")
        self.id = identifier

    def with_api_token(self, token):
        """Set the API token for this resource."""

        self.__set_api_token__(token)
        return self

    def with_id(self, identifier):
        """Set the resource ID for update/delete operations."""

        self.__set_id__(identifier)
        return self

    def create(self):
        """Create this resource in the SignalFx API.

        Arguments:
            None.

        Returns:
            The JSON response if successful, None otherwise. For exceptional
            (400-500) responses an exception will be raised.
        """

        # TODO figure out a cleaner abstraction for validating pre_conditions
        self.is_valid(self.api_token)
        self.is_valid(self.options)

        response = requests.post(
            url=self.base_url + self.endpoint, data=json.dumps(self.options),
            headers={
                'X-SF-Token': self.api_token,
                'Content-Type': 'application/json'
            }
        )

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            return response.raise_for_status()


class Dashboard(Resource):

    def __init__(self):
        """Base representation of a dashboard in SignalFx."""
        super(Resource, self).__init__(endpoint='/dashboard')
