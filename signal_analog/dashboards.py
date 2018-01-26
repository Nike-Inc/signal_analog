import json

import requests

from signal_analog.resources import Resource
import signal_analog.util as util
from signal_analog.errors import ResourceMatchNotFoundError, \
        ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError
import click


class Dashboard(Resource):
    def __init__(self, session=None):
        """Base representation of a dashboard in SignalFx.

        Arguments:
            session: optional session harness for making API requests. Mostly
                     used in testing scenarios.
        """
        super(Dashboard, self).__init__(endpoint='/dashboard')
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

    def create(self, dry_run=False, force=False, interactive=False):
        """Creates a Signalfx dashboard using the /dashboard/simple helper
        endpoint. A list of chart models is required.

        See: https://developers.signalfx.com/v2/reference#dashboardsimple
        """
        def create_helper(opts):
            try:
                query_result = self.__find_existing_resources__()
                self.__find_existing_match__(query_result)
            except (ResourceAlreadyExistsError,
                    ResourceHasMultipleExactMatchesError) as e:
                if not force and not interactive:
                    # Rethrow error to user if we're not force creating things
                    raise e
                elif interactive:
                    msg = 'A dashboard with the name "{0}" already exists. ' + \
                          'Do you want to create a new dashboard?'
                    if click.confirm(msg.format(self.__get__('name'))):
                        return util.flatten_charts(self.options)
                    else:
                        raise ResourceAlreadyExistsError(self.__get__('name'))
            # Otherwise this is perfectly fine, create the dashboard!
            except ResourceMatchNotFoundError:
                return util.flatten_charts(self.options)

        return self.__action__('post', self.endpoint + '/simple', create_helper,
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

        query_result = self.__find_existing_resources__()

        try:
            self.__find_existing_match__(query_result)

        except ResourceAlreadyExistsError:
            dashboard = self.__filter_matches__(query_result)

            if name:
                dashboard.update({'name': name})
            if description:
                dashboard.update({'description': description})

            return self.__action__('put', '/dashboard/' + dashboard['id'],
                lambda x: dashboard)
        except ResourceMatchNotFoundError:
            return self.create(dry_run=dry_run)
