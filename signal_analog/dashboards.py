import json

import requests

from signal_analog.resources import Resource
import signal_analog.util as util
from signal_analog.errors import DashboardMatchNotFoundError, \
        DashboardHasMultipleExactMatchesError, DashboardAlreadyExistsError
import click


class Dashboard(Resource):
    def __init__(self, session=None):
        """Base representation of a dashboard in SignalFx.

        Arguments:
            session: optional session harness for making API requests. Mostly
                     used in testing scenarios.
        """
        super(Dashboard, self).__init__(endpoint='/dashboard/simple')
        self.options = {'charts': []}

        if session:
            self.session_handler = session
        else:
            self.session_handler = requests.Session()

    def with_name(self, name):
        """Sets dashboard's name."""
        util.is_valid(name)
        self.options.update({'name': name})
        return self

    def with_charts(self, *charts):
        for chart in charts:
                self.options['charts'].append(chart)
        return self

    def __get__(self, name, default=None):
        """Internal helper for sourcing top-level options from this
        Dashboard."""
        return self.options.get(name, default)

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
            DashboardMatchNotFoundError:
                if a single exact match couldn't be found in the SignalFx API.
            DashboardAlreadyExistsError:
                if a single exact match is found in the SignalFx API.
            DashboardHasMultipleExactMatchesError:
                if multiple exact matches were found in the SignalFx API.
        """
        results = self.__filter_matches__(query_result)
        if results:
            raise DashboardAlreadyExistsError(self.__get__('name'))

        raise DashboardMatchNotFoundError(self.__get__('name'))

    def __filter_matches__(self, query_result):
        """Attempt to find a matching dashboard given a Sfx API result.

        Arguments:
            query_result: the API response from SignalFx for this Dashboard.

        Returns:
            None.
        """
        name = self.__get__('name', '')
        if not query_result.get('count'):
            raise DashboardMatchNotFoundError(name)

        results = query_result.get('results', [])
        for dashboard in results:
            if name == dashboard.get('name'):
                if self.__has_multiple_matches__(name, results):
                    raise DashboardHasMultipleExactMatchesError(name)
                return dashboard

        raise DashboardMatchNotFoundError(self.__get__('name'))

    def __get_existing_dashboards__(self):
        """Get a list of matches (total and partial) for the given dashboard.
        """
        name = self.__get__('name')
        if not name:
            msg = 'Cannot search for existing dashboards without a name!'
            raise ValueError(msg)

        return self.__action__(
            'get', '/dashboard', lambda x: None, params={'name': name})

    def __update_resource__(self, data):

        response = self.session_handler.request(
            method='PUT',
            url=self.base_url + '/dashboard/' + data['id'],
            data=json.dumps(data),
            headers={'X-SF-Token': self.api_token,
                     'Content-Type': 'application/json'})
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            # Tell the user exactly what went wrong according to SignalFx
            raise RuntimeError(error.response.text)

        return response.json()

    def create(self, dry_run=False, force=False, interactive=False):
        """Creates a Signalfx dashboard using the /dashboard/simple helper
        endpoint. A list of chart models is required.

        See: https://developers.signalfx.com/v2/reference#dashboardsimple
        """
        def create_helper(opts):
            try:
                query_result = self.__get_existing_dashboards__()
                self.__find_existing_match__(query_result)
            except (DashboardAlreadyExistsError,
                    DashboardHasMultipleExactMatchesError) as e:
                if not force and not interactive:
                    # Rethrow error to user if we're not force creating things
                    raise e
                elif interactive:
                    msg = 'A dashboard with the name "{0}" already exists. ' + \
                          'Do you want to create a new dashboard?'
                    if click.confirm(msg.format(self.__get__('name'))):
                        return util.flatten_charts(self.options)
                    else:
                        raise DashboardAlreadyExistsError(self.__get__('name'))
            # Otherwise this is perfectly fine, create the dashboard!
            except DashboardMatchNotFoundError:
                return util.flatten_charts(self.options)

        return self.__action__('post', self.endpoint, create_helper,
            params={'name': self.__get__('name')}, dry_run=dry_run,
            interactive=interactive, force=force)

    def update(self, name=None, description=None, dry_run=False):
        """Updates a Signalfx dashboard using the /dashboard/_id_ helper
        endpoint. A list of chart models is required.

        See: https://developers.signalfx.com/v2/reference#update-dashboard
        """

        updated_opts = dict(self.options)
        if name:
            updated_opts.update({'name': name})
        if description:
            updated_opts.update({'description': description})
        updated_opts.update({'charts': util.flatten_charts(self.options)})

        # Let's override dry-run behavior here since it differs from the defualt
        # implementation.
        if dry_run:
            return updated_opts

        query_result = self.__get_existing_dashboards__()

        try:
            self.__find_existing_match__(query_result)

        except DashboardAlreadyExistsError:
            dashboard = self.__filter_matches__(query_result)

            if name:
                dashboard.update({'name': name})
            if description:
                dashboard.update({'description': description})

            return self.__action__('put', '/dashboard/' + dashboard['id'],
                lambda x: dashboard)
        except DashboardMatchNotFoundError:
            return self.create(dry_run=dry_run)
