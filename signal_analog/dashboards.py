import json

import requests

from signal_analog.resources import Resource
import signal_analog.util as util
from signal_analog.errors import DashboardMatchNotFoundError, \
        DashboardHasMultipleExactMatchesError, DashboardAlreadyExistsError


class Dashboard(Resource):
    def __init__(self):
        """Base representation of a dashboard in SignalFx."""
        super(Dashboard, self).__init__(endpoint='/dashboard/simple')
        self.options = {'charts': []}

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
        return self.options.get(name, default)

    def __has_multiple_matches__(self, dashboard_name, dashboards):
        dashboard_names = list(map(lambda x: x.get('name'), dashboards))
        return dashboard_name in util.find_duplicates(dashboard_names)

    def __find_existing_match__(self, query_result):
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
        name = self.options.get('name', None)
        if not name:
            msg = 'Cannot search for existing dashboards without a name!'
            raise ValueError(msg)

        response = requests.get(
            url=self.base_url + '/dashboard',
            params={'name': name},
            headers={
                'X-SF-Token': self.api_token,
                'Content-Type': 'application/json'
            }
        )
        return response.json()

    def create(self, dry_run=False):
        """Creates a Signalfx dashboard using the /dashboard/simple helper
        endpoint. A list of chart models is required.

        See: https://developers.signalfx.com/v2/reference#dashboardsimple
        """
        request_param = {'name': self.options.get('name', None)}
        charts = list(map(lambda c: c.to_dict(), self.options['charts']))

        if dry_run is True:
            dump = dict(self.options)
            dump.update({'charts': charts})
            return json.dumps(dump)
        else:
            response = requests.request(
                    method='POST',
                    url=self.base_url + self.endpoint,
                    params=request_param,
                    data=json.dumps(charts),
                    headers={'X-SF-Token': self.api_token,
                             'Content-Type': 'application/json'})
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as error:
                # Tell the user exactly what went wrong according to SignalFx
                raise RuntimeError(error.response.text)

            return response.json()
