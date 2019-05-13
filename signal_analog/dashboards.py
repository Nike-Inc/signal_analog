from copy import deepcopy

import click

import signal_analog.util as util
from signal_analog.charts import Chart
from signal_analog.errors import ResourceMatchNotFoundError, ResourceAlreadyExistsError
from signal_analog.resources import Resource


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
        super(DashboardGroup, self).__init__(endpoint='/dashboardgroup', session=session)
        self.options = {'dashboards': []}
        self.dashboards = []
        self.clone_options = {'sourceDashboard': ''}
        self.dashboard_group_ids = []

    def with_dashboards(self, *dashboards):
        """Adds the given dashboards to this DashboardGroup.

        Note: each call to with_dashboards appends dashboards to previous dashboards
              configured for this group.

        Arguments:
            *dashboards: one or more dashboard objects to add.
        """

        for dashboard in dashboards:
            self.dashboards.append(dashboard)
        return self

    def with_teams(self, *team_id):
        """Associates this dashboard group to the given teams in SignalFx.

        Arguments:
            *team_id: one or more team ids to add to this dashboard group.
        """
        self.options.update({'teams': list(team_id)})
        return self

    def create(self, dry_run=False, force=False, interactive=False):
        """Creates a SignalFx dashboard group using the /dashboardgroup helper
        endpoint.

        Arguments:
            dry_run: Boolean to test a dry run
            force: Boolean to force creation in case of errors
            interactive: Boolean to be prompted for user input in case of errors

        See: https://developers.signalfx.com/v2/reference#create-dashboard-group
        """

        if dry_run:
            click.echo("Creates a new Dashboard Group named: \"{0}\". API call being executed: \n"
                       "POST {1} \nRequest Body: \n {2}".format(self.options['name'], (self.base_url + self.endpoint),
                                                                self.options))
            return None

        'Create a new Dashboard Group'
        if self.__create_helper__(force=force, interactive=interactive):
            dashboard_group_create_response = self.__action__('post', self.endpoint, lambda x: self.options,
                                                              params={'name': self.__get__('name')}, dry_run=dry_run,
                                                              interactive=interactive, force=force)

            """This is what the following code is doing:
                1) If there are any dashboard resources provided, for every one of those dashboard resource,
                create a new dashboard by providing the group id of the dashboard group that we created above so that
                all the new dashboards will be part of the new dashboard group

                2) Delete the default dashboard that has been created as part of the new dashboard group if it exists
                and then return the GET response of the dashboard group

                3) If no dashboard resources are provided, just create a new dashboard group and return the response"""

            if len(self.dashboards) > 0:
                for dashboard in self.dashboards:
                    dashboard.with_api_token(self.api_token)\
                        .create(group_id=dashboard_group_create_response['id'], force=True)

                if len(dashboard_group_create_response['dashboards']) > 0:
                    Dashboard(session=self.session_handler).with_api_token(self.api_token)\
                        .with_id(dashboard_group_create_response['dashboards'][0])\
                        .delete()

                return self.with_id(dashboard_group_create_response['id']).read()
            else:
                return dashboard_group_create_response

    def read(self, dry_run=False):
        """Gets data of a SignalFx dashboard group using the /dashboardgroup/<id> helper
        endpoint. Dashboard Group Id is required

        Arguments:
            dry_run: Boolean to test a dry run

        See: https://developers.signalfx.com/v2/reference#get-dashboard-groups
        """
        if dry_run:
            click.echo("Returns the data for Dashboard Group id \"{0}\". API call that is executed: \n GET {1}".format(
                self.options['id'], (self.base_url + self.endpoint + '/' + self.options['id'])))
            return None

        return super(DashboardGroup, self).read()

    def __update_dashboard_resources__(self, dashboard_group_state):
        """Update child resources for this dashboard group.

            Arguments:
                dashboard_group_state: Placeholder to store the state of a dashboard group
        """
        state = deepcopy(dashboard_group_state)

        remote_dashboard_ids = state['dashboards']

        remote_group_ids = state['id']

        def get_config_helper(id):
            res = Dashboard(session=self.session_handler).with_api_token(self.api_token).with_id(id).read()
            return {'id': id, 'name': res['name']}

        remote_dashboards = list(map(get_config_helper, remote_dashboard_ids))

        local_dashboards = self.dashboards

        # Update dashboards that exist in SignalFx
        for remote_dashboard in remote_dashboards:
            for local_dashboard in local_dashboards:
                if remote_dashboard['name'] == local_dashboard.__get__('name'):
                    local_dashboard.with_id(remote_dashboard['id'])\
                        .with_group_id(remote_group_ids)\
                        .with_api_token(self.api_token)\
                        .update()
                    break

        # Delete dashboards that exist in SignalFx but not in our local config
        local_names = list(map(lambda x: x.__get__('name'), local_dashboards))
        for remote_dashboard in remote_dashboards:
            if remote_dashboard['name'] not in local_names:
                Dashboard(session=self.session_handler).with_id(remote_dashboard['id'])\
                    .with_api_token(self.api_token)\
                    .delete()

        # Create dashboards that exist in our local config but not in SignalFx
        remote_names = list(map(lambda x: x['name'], remote_dashboards))
        for local_dashboard in local_dashboards:
            if local_dashboard.__get__('name') not in remote_names:
                resp = local_dashboard.with_api_token(self.api_token)\
                    .create(group_id=remote_group_ids, force=True)
                self.clone(resp['id'], state['id'])
                Dashboard().with_id(resp['id']).with_api_token(self.api_token).delete()

        return state

    def update(self, name=None, description=None, resource_id=None, dry_run=False):
        """Updates a SignalFx dashboard group using the /dashboardgroup/_id_ helper
        endpoint.

        Arguments:
            name: String matching a dashboard group
            description: String containing a dashboard group's description
            resource_id: String matching a dashboard group resource
            dry_run: Boolean to test a dry run

        See: https://developers.signalfx.com/v2/reference#update-dashboard-group
        """

        if 'id' in self.options or resource_id:
            dashboard_group = super(DashboardGroup, self).read(resource_id=resource_id)
            self.options = self.__update_dashboard_resources__(dashboard_group)
            return super(DashboardGroup, self).update(name=name, description=description, resource_id=resource_id)
        else:
            query_result = self.__find_existing_resources__()

            try:
                self.__find_existing_match__(query_result)

            except ResourceAlreadyExistsError:
                self.options = self.__update_dashboard_resources__(self.__filter_matches__(query_result))

                if dry_run:
                    click.echo(
                        "Updates the Dashboard Group named: \"{0}\". If it doesn't exist, will create a new one.  "
                        "API call being executed: \n"
                        "PUT {1} \nRequest Body: \n {2}".format(self.options['name'], (
                                self.base_url + self.endpoint + '/' + self.options['id']), self.options))
                    return None

                return super(DashboardGroup, self)\
                    .update(name=name, description=description, resource_id=resource_id, info_only=True)

            except ResourceMatchNotFoundError:
                return self.create(dry_run=dry_run)

    def delete(self, resource_id=None, dry_run=False):
        """Deletes a SignalFx dashboard group using the /dashboardgroup/<id> helper
        endpoint. Dashboard Group Id is required

        Arguments:
            resource_id: String matching a dashboard group resource
            dry_run: Boolean to test a dry run

        See: https://developers.signalfx.com/v2/reference#delete-dashboard-group
        """
        if dry_run:
            click.echo("Dashboard Group id \"{0}\" will be deleted. API call that is executed: \n DELETE {1}".format(
                self.options['id'], (self.base_url + self.endpoint + '/' + self.options['id'])))
            return None

        return super(DashboardGroup, self).delete(resource_id=resource_id)

    def clone(self, dashboard_id, dashboard_group_id, dry_run=False):
        """Clones a SignalFx dashboard using the /dashboardgroup/_id_/dashboard helper
        endpoint. Dashboard Group Id and sourceDashboard Id are required

        Arguments:
            dashboard_id: String matching a dashboard resource within a dashboard group
            resource_id: String matching a dashboard group resource
            dry_run: Boolean to test a dry run

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

        return super(DashboardGroup, self).clone(dashboard_id=dashboard_id, dashboard_group_id=dashboard_group_id)


class Dashboard(Resource):

    def __init__(self, session=None):
        """Base representation of a dashboard in SignalFx.

        Arguments:
            session: optional session harness for making API requests. Mostly
                     used in testing scenarios.
        """
        super(Dashboard, self).__init__(endpoint='/dashboard', session=session)
        self.options = {'charts': []}
        self.filters = {'filters': {}}
        self.events = {'eventOverlays': []}
        self.selectedevents = {'selectedEventOverlays': []}

    def with_charts(self, *charts):
        """Charts to be included in the dashboard"""
        for chart in charts:
            self.options['charts'].append(deepcopy(chart))
        return self

    def with_filters(self, filters):
        """Filters to be included in the dashboard.

        This method exposes functionality like the "DASHBOARD VARIABLES" screen in the SignalFx UI.

        Example:

        >>> Dashboard().with_filter(DashboardFilters().with_variables(
        >>>    FilterVariable().with_property("aws_account_id").with_alias("aws_account_id").with_value(aws_account_id)
        >>>  ).with_time(FilterTime().with_start("-7d").with_end("Now"))
        >>> )
        """
        self.filters.update({'filters': filters.options})
        return self

    def with_event_overlay(self, *eventoverlays):
        """Event overlays to be included in the dashboard drop down options for events"""
        for eventoverlay in eventoverlays:
            self.events['eventOverlays'].append(deepcopy(eventoverlay))
        return self

    def with_selected_event_overlay(self, *selectedeventoverlays):
        """Default events to display on the dashboard"""
        for selectedeventoverlay in selectedeventoverlays:
            self.selectedevents['selectedEventOverlays'].append(deepcopy(selectedeventoverlay))
        return self

    def create(self, group_id=None, dry_run=False, force=False, interactive=False):
        """Creates a Signalfx dashboard using the /dashboard/simple helper
        endpoint. A list of chart models is required.

        Arguments:
            group_id: String Group Id of the Dashboard Group you want to create this dashboard in
            dry_run: Boolean to test a dry run
            force: Boolean to force creation in case of errors
            interactive: Boolean to be prompted for user input in case of errors

        See: https://developers.signalfx.com/v2/reference#dashboardsimple
        """

        if dry_run:
            self.options.update({'charts': util.flatten_charts(self.options)})
            click.echo("Creates a new Dashboard named: \"{0}\". API call being executed: \n"
                       "POST {1} \nRequest Body: \n {2}".format(self.options['name'],
                                                                (self.base_url + self.endpoint +
                                                                 '/simple?name=' + self.__get__('name') +
                                                                 ('&groupId=' + group_id if group_id else '')),
                                                                self.options))
            return None

        if self.__create_helper__(force=force, interactive=interactive):

            dashboard_create_response = self.__action__('post', self.endpoint + '/simple',
                                                        lambda x: util.flatten_charts(self.options),
                                                        params={'name': self.__get__('name'), 'groupId': group_id},
                                                        dry_run=dry_run, interactive=interactive, force=force)

            """Check to see if there are any filters, event overlays, or "selected" event overlays defined,
                If so, update the dashboard with those filters and/or event overlays.
                NOTE: This cannot be done for filters during dashboard creation as we are using /simple endpoint which
                doesn't support passing filters
            """
            if self.events['eventOverlays'] != list() and self.selectedevents['selectedEventOverlays'] != list():
                dashboard_create_response['eventOverlays'] = list(
                    map(lambda e: e.to_dict(), self.events['eventOverlays']))
                dashboard_create_response['selectedEventOverlays'] = list(
                    map(lambda e: e.to_dict(), self.selectedevents['selectedEventOverlays']))
                self.options = dashboard_create_response

            if self.events['eventOverlays'] != list():
                dashboard_create_response['eventOverlays'] = list(
                    map(lambda e: e.to_dict(), self.events['eventOverlays']))
                self.options = dashboard_create_response
                return super(Dashboard, self).update()

            if self.selectedevents['selectedEventOverlays'] != list():
                dashboard_create_response['selectedEventOverlays'] = list(
                    map(lambda e: e.to_dict(), self.selectedevents['selectedEventOverlays']))
                self.options = dashboard_create_response
                return super(Dashboard, self).update()

            if bool(self.filters['filters']):
                dashboard_create_response['filters'] = self.filters['filters']
                self.options = dashboard_create_response
                return super(Dashboard, self).update()

            else:
                return dashboard_create_response

    def read(self, resource_id=None, dry_run=False):
        """Gets data of a Signalfx dashboard using the /dashboard/<id> helper
        endpoint. Dashboard Id is required

        Arguments:
            resource_id: String matching a dashboard resource
            dry_run: Boolean to test a dry run

        See: https://developers.signalfx.com/v2/reference#get-dashboard
        """
        if dry_run:
            click.echo("Returns the data for Dashboard id \"{0}\". API call that is executed: \n GET {1}".format(
                self.options['id'], (self.base_url + self.endpoint + '/' + self.options['id'])))
            return None

        return super(Dashboard, self).read(resource_id=resource_id)

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
            res = Chart(session=self.session_handler).with_api_token(self.api_token).with_id(id).read()
            return {'id': id, 'name': res['name']}

        remote_charts = list(map(get_config_helper, remote_chart_ids))

        local_charts = self.__get__('charts', [])

        # Update charts that exist in SignalFx
        for remote_chart in remote_charts:
            for local_chart in local_charts:
                if remote_chart['name'] == local_chart.__get__('name'):
                    local_chart.with_id(remote_chart['id']).with_api_token(self.api_token).update()
                    break

        # Delete charts that exist in SignalFx but not in our local config
        local_names = list(map(lambda x: x.__get__('name'), local_charts))
        for remote_chart in remote_charts:
            if remote_chart['name'] not in local_names:
                Chart(session=self.session_handler).with_id(remote_chart['id']).with_api_token(self.api_token).delete()
                # Deleting the chart from state to make sure empty chart states are not returned back to the update
                # call which has adverse effects(throws a 500 error)
                state[:] = [d for d in state if d.get('chartId') != remote_chart['id']]

        # Create charts that exist in our local config but not in SignalFx
        remote_names = list(map(lambda x: x['name'], remote_charts))
        for local_chart in local_charts:
            if local_chart.__get__('name') not in remote_names:
                resp = local_chart.with_api_token(self.api_token).create()

                # We need different row and column values when we are creating new charts so that they won't overlap
                # with one another
                row_nums = [chart['row'] for chart in state]
                column_nums = [chart['column'] for chart in state]
                row_num_to_set = 0
                column_num_to_set = 0
                if 0 in row_nums:
                    row_num_to_set = max(set(row_nums)) + 1
                if 0 in column_nums:
                    column_num_to_set = max(set(column_nums)) + 1
                state.append({
                    'chartId': resp['id'],
                    'column': column_num_to_set,
                    'height': 2,
                    'row': row_num_to_set,
                    'width': 6})
        return state

    def update(self, name=None, description=None, resource_id=None, dry_run=False):
        """Updates a Signalfx dashboard using the /dashboard/_id_ helper
        endpoint. A list of chart models is required.

        Arguments:
            name: String containing the name for the dashboard
            description: String containing a description for this dashboard
            resource_id: String matching the resource ID for this dashboard
            dry_run: Boolean to test a dry run

        See: https://developers.signalfx.com/v2/reference#update-dashboard
        """
        if 'id' in self.options or resource_id:
            dashboard = self.read()
            dashboard.update({'charts': self.__update_child_resources__(dashboard['charts'])})

            """ Check to see if there are any filters defined, If so, update the dashboard with those filters."""
            if bool(self.filters['filters']):
                dashboard['filters'] = self.filters['filters']

            self.options = dashboard
            return super(Dashboard, self).update(name=name, description=description, resource_id=resource_id)

        else:
            query_result = self.__find_existing_resources__()

            try:
                self.__find_existing_match__(query_result)

            except ResourceAlreadyExistsError:
                dashboard = self.__filter_matches__(query_result)
                dashboard.update({'charts': self.__update_child_resources__(dashboard['charts'])})

                if name:
                    dashboard.update({'name': name})
                if description:
                    dashboard.update({'description': description})
                """ Check to see if there are any filters defined, If so, update the dashboard with those filters."""
                if bool(self.filters['filters']):
                    dashboard['filters'] = self.filters['filters']

                """ Check to see if there are any overlays defined, If so, update the dashboard with those overlays."""
                if self.events['eventOverlays'] != list():
                    dashboard['eventOverlays'] = list(map(lambda e: e.to_dict(), self.events['eventOverlays']))

                if self.selectedevents['selectedEventOverlays'] != list():
                    dashboard['selectedEventOverlays'] = list(
                        map(lambda e: e.to_dict(), self.selectedevents['selectedEventOverlays']))

                # TODO temporary workaround in the SignalFx API
                #
                # 1. We need to update the dashboard config and PUT it back when
                #    we've updated or added a chart.
                # 2. We should NOT update the dashboard config and PUT it back when
                #    we delete a chart.
                #
                # Our implementation makes it exceptionally inconvenient to special
                # case delete behavior. Let's check back in a bit to see what
                # API changes SignalFx makes.
                if dry_run:
                    click.echo("Updates the Dashboard named: \"{0}\". If it doesn't exist, will create a new one.  "
                               "API call being executed: \n"
                               "PUT {1} \nRequest Body: \n {2}".format(self.options['name'], (
                                self.base_url + self.endpoint + '/' + dashboard['id']), dashboard))
                    return None

                try:
                    return self.__action__('put', '/dashboard/' + dashboard['id'], lambda x: dashboard)
                except RuntimeError:
                    msg = """
WARNING: signal_analog has caught a potentially fatal runtime error when
updating a dashboard with the id '{0}'.

This typically happens when we delete a chart from an existing dashboard.
"""

                    click.secho(msg.format(dashboard['id']), fg='yellow')
                    return self.with_id(dashboard['id']).read()

            except ResourceMatchNotFoundError:
                return self.create(dry_run=dry_run)

    def delete(self, resource_id=None, dry_run=False):
        """Deletes a SignalFx dashboard using the /dashboard/<id> helper
        endpoint. Dashboard Id is required

        Arguments:
            resource_id: String matching the resource id for a dashboard
            dry_run: Boolean to test a dry run

        See: https://developers.signalfx.com/v2/reference#delete-dashboard
        """
        if dry_run:
            click.echo("Dashboard id \"{0}\" will be deleted. API call that is executed: \n DELETE {1}".format(
                self.options['id'], (self.base_url + self.endpoint + '/' + self.options['id'])))
            return None

        """So, as per SignalFx design as of 02/19/18,
        Deleting a dashboard via the API does not affect the related charts in any way.
        Only the relationship between the charts and the dashboard is severed. Any charts on the deleted dashboard are
        orphaned and available to other dashboards. If you wish to delete them at the same time you delete their
        current dashboard you must send a Delete Chart API call for each chart. That's exactly what we are doing here.
        """
        list_of_charts = [charts['chartId'] for charts in self.read(resource_id=resource_id)['charts']]
        if list_of_charts:
            for chart in list_of_charts:
                Chart(session=self.session_handler).with_api_token(self.api_token).with_id(chart).delete()

        return super(Dashboard, self).delete(resource_id=resource_id)
