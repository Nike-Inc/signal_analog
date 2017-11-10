import json

import requests

from signal_analog.resources import Resource
import signal_analog.util as util


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
