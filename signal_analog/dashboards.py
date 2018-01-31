import json
import requests
from copy import deepcopy

from signal_analog.charts import Chart
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
        super(Dashboard, self).__init__(endpoint='/dashboard', session=session)
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
                        return util.flatten_charts(opts)
                    else:
                        raise ResourceAlreadyExistsError(self.__get__('name'))
            # Otherwise this is perfectly fine, create the dashboard!
            except ResourceMatchNotFoundError:
                pass

            return util.flatten_charts(opts)

        return self.__action__('post', self.endpoint + '/simple', create_helper,
            params={'name': self.__get__('name')}, dry_run=dry_run,
            interactive=interactive, force=force)

    def __update_child_resources__(self, chart_state):
        """Update child resources for this dashboard.
        """
        state = deepcopy(chart_state)

        # Dashboard state can get really screwy sometimes. In certain situations
        # a stale Chart object can be in the Dashboard config _without_ a valid
        # id. Let's be nice and clean that up; makes it easier for us to
        # update Dashboards too.
        for chart in state:
            if chart['chartId'] is None:
                state.remove(chart)

        remote_chart_ids = list(map(lambda x: x['chartId'], state))
        def get_config_helper(id):
            res = Chart(session=self.session_handler)\
                .with_api_token(self.api_token).with_id(id).read()
            return {'id': id, 'name': res['name']}
        remote_charts = list(map(get_config_helper, remote_chart_ids))

        local_charts = self.__get__('charts', [])

        # Update existing charts
        for remote_chart in remote_charts:
            for local_chart in local_charts:
                if remote_chart['name'] == local_chart.__get__('name'):
                    local_chart\
                        .with_id(remote_chart['id'])\
                        .with_api_token(self.api_token)\
                        .create()
                    break

        # Create charts in our local environment but not in SignalFx
        remote_names = list(map(lambda x: x['name'], remote_charts))
        for local_chart in local_charts:
            if local_chart.__get__('name') not in remote_names:
                resp = local_chart\
                    .with_api_token(self.api_token)\
                    .create()
                state.append({
                    'chartId': resp['id'],
                    'column': 11,  # TODO can we provide better defaults?
                    'height': 3,
                    'row': 99,
                    'width': 6
                })

        # Delete charts that exist in SignalFx but not our local config
        local_names = list(map(lambda x: x.__get__('name'), local_charts))
        for remote_chart in remote_charts:
            if remote_chart['name'] not in local_names:
                local_chart\
                    .with_id(remote_chart['id'])\
                    .with_api_token(self.api_token)\
                    .delete()

        return state

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
            dashboard.update({
                'charts': self.__update_child_resources__(dashboard['charts'])
            })

            if name:
                dashboard.update({'name': name})
            if description:
                dashboard.update({'description': description})

            # TODO we are forced to do this while SignalFx figures out their
            # API problems. The gist of it is:
            #
            # 1. We need to update the dashboard config and PUT it back when
            #    we've updated or added a chart.
            # 2. We should NOT update the dashboard config and PUT it back when
            #    we delete a chart.
            #
            # Our implementation makes it exceptionally inconvenient to special
            # case delete behavior. Let's check back in a bit to see what
            # API changes SignalFx can make for us.
            #
            # https://jira.nike.com/browse/SIP-1062
            try:
                return self.__action__('put', '/dashboard/' + dashboard['id'],
                        lambda x: dashboard)
            except RuntimeError:
                msg = """
WARNING: signal_analog has caught a potentially fatal runtime error when
updating a dashboard with the id '{0}'.

This typically happens when we delete a chart from an existing dashboard. It is
considered a defect in the SignalFx API, and the relevant teams are working to
ensure that this is resolved in a future release.

To track the status of this work subscribe to the following ticket:
https://jira.nike.com/browse/SIP-1062
                """
                click.secho(msg.format(dashboard['id']), fg='yellow')

        except ResourceMatchNotFoundError:
            return self.create(dry_run=dry_run)
