import json

import requests

from signal_analog.resources import Resource
import signal_analog.util as util
from signal_analog.errors import DashboardMatchNotFoundError, \
        DashboardHasMultipleExactMatchesError, DashboardAlreadyExistsError


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
        Dashbord."""
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
        name = self.__get__('name', '')
        if not query_result.get('count'):
            raise DashboardMatchNotFoundError(name)

        results = query_result.get('results', [])
        for dashboard in results:
            if name == dashboard.get('name'):
                if self.__has_multiple_matches__(name, results):
                    raise DashboardHasMultipleExactMatchesError(name)
                raise DashboardAlreadyExistsError(name)

        raise DashboardMatchNotFoundError(self.__get__('name'))

    def __get_existing_dashboards__(self):
        """Get a list of matches (total and partial) for the given dashboard.
        """
        name = self.__get__('name')
        if not name:
            msg = 'Cannot search for existing dashboards without a name!'
            raise ValueError(msg)

        response = self.session_handler.get(
            url=self.base_url + '/dashboard',
            params={'name': name},
            headers={
                'X-SF-Token': self.api_token,
                'Content-Type': 'application/json'
            }
        )
        return response.json()

    def __create_resource__(self):
        charts = list(map(lambda c: c.to_dict(), self.options['charts']))

        response = self.session_handler.request(
                method='POST',
                url=self.base_url + self.endpoint,
                params={'name': self.__get__('name')},
                data=json.dumps(charts),
                headers={'X-SF-Token': self.api_token,
                         'Content-Type': 'application/json'})
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            # Tell the user exactly what went wrong according to SignalFx
            raise RuntimeError(error.response.text)

        return response.json()

    def create(self, dry_run=False, force=False):
        """Creates a Signalfx dashboard using the /dashboard/simple helper
        endpoint. A list of chart models is required.

        See: https://developers.signalfx.com/v2/reference#dashboardsimple
        """
        charts = list(map(lambda c: c.to_dict(), self.options['charts']))

        if dry_run is True:
            dump = dict(self.options)
            dump.update({'charts': charts})
            return json.dumps(dump)

        try:
            query_result = self.__get_existing_dashboards__()
            self.__find_existing_match__(query_result)
        except (DashboardAlreadyExistsError,
                DashboardHasMultipleExactMatchesError) as e:
            if not force:
                # Rethrow error to user if we're not force creating things
                raise e
        # Otherwise this is perfectly fine, create the dashboard!
        except DashboardMatchNotFoundError:
            pass

        return self.__create_resource__()
