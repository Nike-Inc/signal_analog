#!/usr/bin/env python

"""Examples for the `signal_analog.dashboards` module."""

from signal_analog.flow import Data, Filter
from signal_analog.charts import TimeSeriesChart
from signal_analog.dashboards import Dashboard, DashboardGroup
from signal_analog.combinators import And

"""
Example 1: Creating a new Dashboard Group

This creates a new dashboard group
"""
dashboard_group = DashboardGroup().with_name('Dashboard Group Name')

"""
Example 2: Creating a new Dashboard Group with Dashboards

"""
filters = And(Filter('app', 'my-app'), Filter('env', 'test'))

program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

program1 = Data('network.utilization', filter=filters).publish()
chart1 = TimeSeriesChart().with_name('Chart_Name').with_program(program)

program2 = Data('api_errors', filter=filters).publish()
chart2 = TimeSeriesChart().with_name('Chart_Name').with_program(program)

dashboard1 = Dashboard().with_name('Dashboard1').with_charts(chart)
dashboard2 = Dashboard().with_name('Dashboard2').with_charts(chart, chart1)
dashboard3 = Dashboard().with_name('Dashboard3')\
    .with_charts(chart, chart1, chart2)

dashboard_group_with_dashboards = DashboardGroup() \
    .with_name('Dashboard Group Name') \
    .with_dashboards(dashboard1, dashboard2, dashboard3)

"""
Example 3: Update existing dashboard group by removing one of the dashboards

"""

dashboard_group_remove_dashboard = DashboardGroup()\
                                    .with_name('Dashboard Group Name')\
                                    .with_dashboards(dashboard1, dashboard2)

"""
Example 4: Rename an existing Dashboard

"""
dashboard2 = Dashboard().with_name('Dashboard2_Renamed')\
    .with_charts(chart, chart1)
dashboard_group_rename_dashboard = DashboardGroup()\
                                    .with_name('Dashboard Group Name')\
                                    .with_dashboards(dashboard1, dashboard2)


if __name__ == '__main__':
    from signal_analog.cli import CliBuilder

    cli = CliBuilder().with_resources(dashboard_group,
                                      dashboard_group_with_dashboards,
                                      dashboard_group_remove_dashboard,
                                      dashboard_group_rename_dashboard)\
        .build()
    cli()
