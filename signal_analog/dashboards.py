from copy import deepcopy

from signal_analog.charts import Chart
from signal_analog.resources import Resource
import signal_analog.util as util
from signal_analog.errors import ResourceMatchNotFoundError, \
    ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError
import click


class DashboardGroup(Resource):
    """Representation of a Dashboard Group in SignalFx:

    See: https://developers.signalfx.com/v2/reference#dashboard-groups-overview
    """

    def __init__(self, session=None):
        """Initialize a dashboard group.

        Arguments:
            session: optional session harness for making API requests. Mostly
                     used in testing scenarios.
        """
        super(DashboardGroup, self).__init__(
            endpoint='/dashboardgroup', session=session)
        self.options = {'dashboards': []}
        self.dashboards = []
        self.clone_options = {'sourceDashboard': ''}
        self.dashboard_group_ids = []

    def with_name(self, name):
        """Set this dashboard group's name."""
        util.is_valid(name)
        self.options.update({'name': name})
        return self

    def with_dashboards(self, *dashboards):
        """Adds the given dashboards to this DashboardGroup.

        Note: each call to with_dashboards replaces any previous dashboards
              configured for this group.

        Arguments:
            *dashboards: one or more dashboard objects to add.
        """
        for dashboard in dashboards:
            self.dashboards.append(dashboard)
        return self

    def with_teams(self, *team_id):
        """Adds the given team ids to this dashboard.

        Note: each call to with_dashboards replaces any previous dashboards
              configured for this group.

        Arguments:
            *team_id: one or more team ids to add to this dashboard group.
        """
        raise NotImplementedError('Implemented as part of SIP-1065')

    def create(self, dry_run=False, force=False, interactive=False):
        """Creates a SignalFx dashboard group using the /dashboardgroup helper
        endpoint.

        See: https://developers.signalfx.com/v2/reference#create-dashboard-group
        """

        if dry_run:
            click.echo("Creates a new Dashboard Group named: \"{0}\". API call being executed: \n"
                       "POST {1} \nRequest Body: \n {2}".format(self.options['name'],
                                                                (self.base_url + self.endpoint),
                                                                self.options))
            return None
        if self.create_helper(force=force, interactive=interactive):
            dashboard_group_create_response = self.__action__('post', self.endpoint,
                                                              lambda x: self.options,
                                                              params={'name': self.__get__('name')},
                                                              dry_run=dry_run, interactive=interactive,
                                                              force=force)

            """This is what the following code is doing: 
                1) If any dashboard resources are provided, we already created new dashboards 
                or updated if they already exist via `with_dashboards` method   
                In which case, self.options['dashboards'] will have the list of those dashboard ids.
                We then clone those dashboards to the dashboard group, delete the old duplicate dashboards that are 
                already cloned and also delete the default dashboard that has been created as part of the new dashboard group
                if it exists and then return the GET response of the dashboard group
                
                2) If no dashboard resources are created, just create a new dashboard group and return the response"""

            if len(self.dashboards) > 0:
                for dashboard in self.dashboards:
                    dashboard_create_response = dashboard.with_api_token(self.api_token).update()
                    self.options['dashboards'].append(dashboard_create_response['id'])
                    self.dashboard_group_ids.append(dashboard_create_response['groupId'])

                for dashboard_id in self.options['dashboards']:
                    self.clone(dashboard_id, dashboard_group_create_response['id'])

                for dashboardGroupId in frozenset(self.dashboard_group_ids):
                    self.delete(dashboardGroupId)

                if len(dashboard_group_create_response['dashboards']) > 0:
                    Dashboard().with_api_token(self.api_token).delete(dashboard_group_create_response['dashboards'][0])

                return self.read(dashboard_group_create_response['id'])
            else:
                return dashboard_group_create_response

    def read(self, dashboard_group_id, dry_run=False):
        """Gets data of a SignalFx dashboard group using the /dashboardgroup/<id> helper
        endpoint. Dashboard Group Id is required

        See: https://developers.signalfx.com/v2/reference#get-dashboard-groups
        """
        if dry_run:
            click.echo("Returns the data for Dashboard Group id \"{0}\". API call that is executed: \n GET {1}" \
                       .format(dashboard_group_id, (self.base_url + self.endpoint + '/' + dashboard_group_id)))
            return None

        return self.__action__('get', self.endpoint + '/' + dashboard_group_id,
                               util.empty_body(), params=None,
                               dry_run=dry_run)

    def update(self, name=None, description=None, dry_run=False):
        """Updates a SignalFx dashboard group using the /dashboardgroup/_id_ helper
        endpoint.

        See: https://developers.signalfx.com/v2/reference#update-dashboard-group
        """

        updated_opts = dict(self.options)
        if name:
            updated_opts.update({'name': name})
        if description:
            updated_opts.update({'description': description})

        query_result = self.__find_existing_resources__()

        try:
            self.__find_existing_match__(query_result)

        except ResourceAlreadyExistsError:
            dashboard_group = self.__filter_matches__(query_result)

            if name:
                dashboard_group.update({'name': name})
            if description:
                dashboard_group.update({'description': description})

            if dry_run:
                click.echo("Updates the Dashboard Group named: \"{0}\". If it doesn't exist, will create a new one.  "
                           "API call being executed: \n"
                           "PUT {1} \nRequest Body: \n {2}".format(self.options['name'],
                                                                   (self.base_url + self.endpoint + '/' +
                                                                    dashboard_group[
                                                                        'id']),
                                                                   dashboard_group))
                return None

            if len(self.dashboards) > 0:
                for dashboard in self.dashboards:
                    dashboard_create_response = dashboard.with_api_token(self.api_token).update()
                    self.options['dashboards'].append(dashboard_create_response['id'])
                    self.dashboard_group_ids.append(dashboard_create_response['groupId'])

                for dashboard_id in self.options['dashboards']:
                    # Only clone the dashboards that are not part of the existing dashboard group
                    if Dashboard().with_api_token(self.api_token).read(dashboard_id)['groupId'] != dashboard_group['id']:
                        self.clone(dashboard_id, dashboard_group['id'])

                # Remove the groupId of the current dashboard group from the list of dashboard groups
                # as we don't want to delete the current dashboard group in the next step
                while dashboard_group['id'] in self.dashboard_group_ids:
                    self.dashboard_group_ids.remove(dashboard_group['id'])

                for dashboardGroupId in frozenset(self.dashboard_group_ids):
                    self.delete(dashboardGroupId)

                dashboards_to_delete = [x for x in dashboard_group['dashboards'] if x not in self.options['dashboards']]
                if len(dashboards_to_delete) is not 0:
                    for dashboard_id in dashboards_to_delete:
                        Dashboard().with_api_token(self.api_token).delete(dashboard_id)

            return self.__action__('put', '/dashboardgroup/' + dashboard_group['id'],
                                       lambda x: dashboard_group)
        except ResourceMatchNotFoundError:
            return self.create(dry_run=dry_run)

    def delete(self, dashboard_group_id, dry_run=False):
        """Deletes a SignalFx dashboard group using the /dashboardgroup/<id> helper
        endpoint. Dashboard Group Id is required

        See: https://developers.signalfx.com/v2/reference#delete-dashboard-group
        """
        if dry_run:
            click.echo("Dashboard Group id \"{0}\" will be deleted. API call that is executed: \n DELETE {1}"
                       .format(dashboard_group_id, (self.base_url + self.endpoint + '/' + dashboard_group_id)))
            return None

        return self.__action__('delete', self.endpoint + '/' + dashboard_group_id,
                               util.empty_body(), params=None,
                               dry_run=dry_run)

    def clone(self, dashboard_id, dashboard_group_id, dry_run=False):
        """Clones a SignalFx dashboard using the /dashboardgroup/_id_/dashboard helper
        endpoint. Dashboard Group Id and sourceDashboard Id are required

        See: https://developers.signalfx.com/v2/reference#clone-dashboard-into-dashboard-group
        """
        if dry_run:
            self.clone_options['sourceDashboard'] = dashboard_id
            click.echo("This will clone the dashboard \"{0}\" to Dashboard Group \"{1}\". API call being executed: \n"
                       "POST {2} \nRequest Body: \n {3}".format(dashboard_id, dashboard_group_id,
                                                                (
                                                                        self.base_url + self.endpoint + '/' +
                                                                        dashboard_group_id + '/dashboard'),
                                                                self.clone_options))
            return None

        self.clone_options['sourceDashboard'] = dashboard_id
        return self.__action__('post', self.endpoint + '/' + dashboard_group_id + '/dashboard',
                               lambda x: self.clone_options, params=None,
                               dry_run=dry_run)


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
        """Set this dashboard's name."""
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

        if dry_run:
            click.echo("Creates a new Dashboard named: \"{0}\". API call being executed: \n"
                       "POST {1} \nRequest Body: \n {2}".format(self.options['name'],
                                                                (self.base_url + self.endpoint),
                                                                self.options))
            return None

        if self.create_helper(force=force, interactive=interactive):
            return self.__action__('post', self.endpoint + '/simple',
                                   lambda x: util.flatten_charts(self.options),
                                   params={'name': self.__get__('name')},
                                   dry_run=dry_run, interactive=interactive,
                                   force=force)

    def read(self, dashboard_id, dry_run=False):
        """Gets data of a Signalfx dashboard using the /dashboard/<id> helper
        endpoint. Dashboard Id is required

        See: https://developers.signalfx.com/v2/reference#get-dashboard
        """
        if dry_run:
            click.echo("Returns the data for Dashboard id \"{0}\". API call that is executed: \n GET {1}" \
                       .format(dashboard_id, (self.base_url + self.endpoint + '/' + dashboard_id)))
            return None

        return self.__action__('get', self.endpoint + '/' + dashboard_id,
                               util.empty_body(), params=None,
                               dry_run=dry_run)

    def __update_child_resources__(self, chart_state):
        """Update child resources for this dashboard.
        """
        state = deepcopy(chart_state)

        # Dashboard state can get really screwy sometimes. In certain
        # situations a stale Chart object can be in the Dashboard config
        # _without_ a valid id. Let's be nice and clean that up; makes it
        # easier for us to update Dashboards too.
        for chart in state:
            if chart['chartId'] is None:
                state.remove(chart)

        remote_chart_ids = list(map(lambda x: x['chartId'], state))

        def get_config_helper(id):
            res = Chart(session=self.session_handler) \
                .with_api_token(self.api_token).with_id(id).read()
            return {'id': id, 'name': res['name']}

        remote_charts = list(map(get_config_helper, remote_chart_ids))

        local_charts = self.__get__('charts', [])

        # Update existing charts
        for remote_chart in remote_charts:
            for local_chart in local_charts:
                if remote_chart['name'] == local_chart.__get__('name'):
                    local_chart \
                        .with_id(remote_chart['id']) \
                        .with_api_token(self.api_token) \
                        .update()
                    break

        # Create charts in our local environment but not in SignalFx
        remote_names = list(map(lambda x: x['name'], remote_charts))
        for local_chart in local_charts:
            if local_chart.__get__('name') not in remote_names:
                resp = local_chart \
                    .with_api_token(self.api_token) \
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
                local_chart \
                    .with_id(remote_chart['id']) \
                    .with_api_token(self.api_token) \
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

            # TODO ***REMOVED***
            ***REMOVED***
            #
            # 1. We need to update the dashboard config and PUT it back when
            #    we've updated or added a chart.
            # 2. We should NOT update the dashboard config and PUT it back when
            #    we delete a chart.
            #
            # Our implementation makes it exceptionally inconvenient to special
            # case delete behavior. Let's check back in a bit to see what
            # API changes SignalFx ***REMOVED***.
            #
            # https://jira.nike.com/browse/SIP-1062
            if dry_run:
                click.echo("Updates the Dashboard named: \"{0}\". If it doesn't exist, will create a new one.  "
                           "API call being executed: \n"
                           "PUT {1} \nRequest Body: \n {2}".format(self.options['name'],
                                                                   (self.base_url + self.endpoint + '/' + dashboard[
                                                                       'id']),
                                                                   updated_opts))
                return None

            try:
                return self.__action__('put', '/dashboard/' + dashboard['id'],
                                       lambda x: dashboard)
            except RuntimeError:
                msg = """
WARNING: signal_analog has caught a potentially fatal runtime error when
updating a dashboard with the id '{0}'.

This typically happens when we delete a chart from an existing dashboard. It is
***REMOVED***
ensure that this is resolved in a future release.

To track the status of this work subscribe to the following ticket:
https://jira.nike.com/browse/SIP-1062
                """
                click.secho(msg.format(dashboard['id']), fg='yellow')
                return self.read(dashboard['id'])

        except ResourceMatchNotFoundError:
            return self.create(dry_run=dry_run)

    def delete(self, dashboard_id, dry_run=False):
        """Deletes a SignalFx dashboard using the /dashboard/<id> helper
        endpoint. Dashboard Group Id is required

        See: https://developers.signalfx.com/v2/reference#delete-dashboard
        """
        if dry_run:
            click.echo("Dashboard id \"{0}\" will be deleted. API call that is executed: \n DELETE {1}" \
                       .format(dashboard_id, (self.base_url + self.endpoint + '/' + dashboard_id)))
            return None

        """So, as per SignalFx design as of 02/19/18, 
        Deleting a dashboard via the API does not affect the related charts in any way. 
        Only the relationship between the charts and the dashboard is severed. Any charts on the deleted dashboard are
        orphaned and available to other dashboards. If you wish to delete them at the same time you delete their current 
        dashboard you must send a Delete Chart API call for each chart. And, that's exactly what we are doing here
        """
        list_of_charts = [charts['chartId'] for charts in self.read(dashboard_id)['charts']]

        if len(list_of_charts) > 0:
            for chart in list_of_charts:
                Chart().with_api_token(self.api_token).with_id(chart).delete()

        return self.__action__('delete', self.endpoint + '/' + dashboard_id,
                               util.empty_body(), params=None,
                               dry_run=dry_run)
