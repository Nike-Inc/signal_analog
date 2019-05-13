import sys

import click
import requests

import signal_analog.util as util
from signal_analog import debug
from signal_analog.errors import ResourceMatchNotFoundError, \
    ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError

# py2/3 compatibility hack so that we can consistently handle JSON errors.
try:
    from simplejson.decoder import JSONDecodeError
except ImportError:
    try:
        from json.decoder import JSONDecodeError
    except ImportError:
        JSONDecodeError = ValueError

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

        Arguments:
            base_url: the base endpoint to use when talking to SignalFx
            endpoint: the particular endpoint to hit for this resource
            api_token: the api token to authenticate requests with
            session: optional session harness for making API requests. Mostly
                     used in test scenarios.
        """

        self.options = {}

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

    def with_name(self, name):
        """The name to give this resource.

        Arguments:
            name: String
        """
        util.assert_valid(name)
        self.options.update({'name': name})
        return self

    def with_description(self, description):
        """The description to attach to this resource.

        Arguments:
            description: String
        """
        util.assert_valid(description)
        self.options.update({'description': description})
        return self

    def with_id(self, ident):
        """The id for this resource. Useful for creates/deletes.

        Arguments:
            ident: String
        """
        util.assert_valid(ident)
        self.options.update({'id': ident})
        return self

    def with_group_id(self, ident):
        """The groupId for this resource. Useful for creates/deletes.

        Arguments:
            ident: String
        """
        util.assert_valid(ident)
        self.options.update({'groupId': ident})
        return self

    def __set_api_token__(self, token):
        """Internal helper for setting valid API tokens.

        Arguments: String
        """

        message = """Cannot proceed with an empty API token.
        Either pass one in at Resource instantiation time or provide one
        via the `with_api_token` method."""

        util.assert_valid(token, message)
        self.api_token = token

    def __set_endpoint__(self, endpoint):
        """Internal helper for setting valid endpoints.

        Arguments:
            endpoint: String
        """
        util.assert_valid(endpoint, error_message="Cannot proceed with an empty endpoint")
        self.endpoint = endpoint

    def __set_base_url__(self, base_url):
        """Internal helper for setting valid base_urls.

        Arguments:
            base_url: String
        """
        util.assert_valid(base_url, error_message="Cannot proceed with empty base_url")
        self.base_url = base_url

    def with_api_token(self, token):
        """Set the API token for this resource.

        Arguments:
            token: String
        """

        self.__set_api_token__(token)
        return self

    def __action__(self, action, endpoint, update_fn, params=None,
                   dry_run=False, interactive=False, force=False):
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
                HTTPError: when a network exception occurred
        """
        if dry_run:
            opts = dict(self.options)
            if self.options.get('charts', []):
                opts.update({'charts': util.flatten_charts(self.options)})
            return opts

        util.assert_valid(self.api_token)

        response = self.session_handler.request(
            action,
            url=self.base_url + endpoint,
            params=params,
            json=update_fn(self.options),
            headers={
                'X-SF-Token': self.api_token,
                'Content-Type': 'application/json'
            })

        debug(
            "{0} {1}".format(
                response.request.method.upper(),
                response.request.url)
        )
        if response.request.body:
            debug(response.request.body)

        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            if response.status_code == 405:
                msg = "Oops! We encountered a 405 exception for {0}" +\
                      " resource. Possible cause: You might be passing an " +\
                      "empty id"
                click.echo(msg.format(str(self.__class__.__name__)))
                sys.exit(1)
            # Tell the user exactly what went wrong according to SignalFX
            raise RuntimeError(error.response.text)
        except JSONDecodeError:
            # Some responses from the API don't return anything, in these
            # situations we shouldn't either
            return None

    def __get__(self, name, default=None):
        """Helper for sourcing top-level options from this resource.

        Arguments:
            name: String
            default: String
        """
        return self.options.get(name, default)

    def __find_existing_resources__(self):
        """ Get a list of matches (total and partial) for the given dashboard.
        """
        name = self.__get__('name')
        if not name:
            msg = 'Cannot search for existing dashboards without a name!'
            raise ValueError(msg)

        return self.__action__(
            'get', self.endpoint, lambda x: None, params={'name': name})

    def __has_multiple_matches__(self, dashboard_name, dashboards):
        """Determine if the current dashboard has multiple exact matches.

        Arguments:
            dashboard_name: the name of the dashboard to check
            dashboards: a collection of dashboard objects to search

        Returns:
            True if multiple exact matches are found, false otherwise.
        """
        dashboard_names = list(map(lambda x: x.get('name'), dashboards))
        return dashboard_name in util.find_duplicates(dashboard_names)

    def __find_existing_match__(self, query_result):
        """Attempt to find a matching dashboard given a Sfx API result.

        Arguments:
            query_result: the API response from SignalFx for this Dashboard.

        Returns:
            None.

        Raises:
            ResourceMatchNotFoundError:
                if a single exact match couldn't be found in the SignalFx API.
            ResourceAlreadyExistsError:
                if a single exact match is found in the SignalFx API.
            ResourceHasMultipleExactMatchesError:
                if multiple exact matches were found in the SignalFx API.
        """
        results = self.__filter_matches__(query_result)
        if results:
            raise ResourceAlreadyExistsError(self.__get__('name'))

        raise ResourceMatchNotFoundError(self.__get__('name'))

    def __filter_matches__(self, query_result):
        """Attempt to find a matching dashboard given a Sfx API result.

        Arguments:
            query_result: the API response from SignalFx for this Dashboard.

        Returns:
            None.
        """
        name = self.__get__('name', '')
        if not query_result.get('count'):
            raise ResourceMatchNotFoundError(name)

        results = query_result.get('results', [])
        for dashboard in results:
            if name == dashboard.get('name'):
                if self.__has_multiple_matches__(name, results):
                    raise ResourceHasMultipleExactMatchesError(name)
                return dashboard

        raise ResourceMatchNotFoundError(self.__get__('name'))

    def create(self, dry_run=False, interactive=False, force=False):
        """Default implementation for resource creation.

        Arguments:
            dry_run: Boolean to test a dry run
            interactive: Boolean to run in interactive mode
            force: Boolean to force execution
        """
        return self.__action__('post', self.endpoint, lambda x: x,
                               dry_run=dry_run, interactive=interactive,
                               force=force)

    def update(self, name=None, description=None, resource_id=None, info_only=False):
        """Attempt to update the given resource in SignalFx.

        Your have to provide the resource id via
        'with_id' or you can pass the id as a parameter

        info_only will read the provided resource back from SFX

        Arguments:
            name: String
            description: String
            resource_id: String
            info_only: Boolean
        """
        rid = resource_id if resource_id else self.__get__('id')
        if name:
            self.options.update({'name': name})
        if description:
            self.options.update({'description': description})
        if info_only is True:
            if rid:
                return self.__action__(
                    'get', self.endpoint + '/' + rid, lambda x: x)
            else:
                raise ValueError('Id is required for resource updates')
        if rid:
            return self.__action__(
                'put', self.endpoint + '/' + rid, lambda x: x)
        else:
            raise ValueError('Id is required for resource updates')

    def read(self, resource_id=None):
        """Attempt to find the given resource in SignalFx.

        Your chances are much higher if you provide the chart id via
        'with_id'. Otherwise, we will attempt to do a best effort to search for
        your chart based on name.

        Arguments:
            resource_id: String
        """
        rid = resource_id if resource_id else self.__get__('id')
        if rid:
            return self.__action__(
                'get', self.endpoint + '/' + rid, lambda x: None)
        else:
            return self.__action__(
                'get', self.endpoint, lambda x: None,
                params={'name': self.__get__('name')})['results'][0]

    def delete(self, resource_id=None):
        """Delete the given resource in the SignalFx API.

        Arguments:
            resource_id: String
        """
        rid = resource_id if resource_id else self.__get__('id')

        if rid:
            return self.__action__(
                'delete', self.endpoint + '/' + rid,
                lambda x: None)
        else:
            return self.__action__(
                'delete', self.endpoint + '/' + self.read()['id'],
                lambda x: None)

    def clone(self, dashboard_id, dashboard_group_id, dry_run=False):
        """Default implementation for resource cloning.

        Arguments:
            dashboard_id: String
            dashboard_group_id: String
            dry_run: String
        """

        self.options = {'sourceDashboard': dashboard_id}
        return self.__action__(
            'post',
            self.endpoint + '/' + dashboard_group_id + '/dashboard',
            lambda x: x, dry_run=dry_run)

    def __create_helper__(self, force=False, interactive=False):
        """Helper for creating new resources.

        Arguments:
            force: Boolean
            interactive: Boolean
        """
        try:
            query_result = self.__find_existing_resources__()
            self.__find_existing_match__(query_result)
        except (ResourceAlreadyExistsError,
                ResourceHasMultipleExactMatchesError) as e:
            if not force and not interactive:
                # Rethrow error to user if we're not force creating things
                raise e
            elif interactive:
                msg = 'A resource with the name "{0}" already exists. ' +\
                      'Do you want to create a new one?'
                if click.confirm(msg.format(self.__get__('name'))):
                    return True
                else:
                    raise ResourceAlreadyExistsError(self.__get__('name'))
        # Otherwise this is perfectly fine, create the resource!
        except ResourceMatchNotFoundError:
            pass

        return True
