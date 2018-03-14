#!/usr/bin/env python

"""Examples for the `signal_analog.dashboards` module."""

from signal_analog.flow import Data, Filter
from signal_analog.charts import TimeSeriesChart
from signal_analog.dashboards import Dashboard
from signal_analog.combinators import And

"""
Example 1: Creating a new Dashboard

This creates a new dashboard for the app specified and with the charts provided
"""
filters = And(Filter('app', 'my-app'), Filter('env', 'test'))
program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

dashboard_with_single_chart = Dashboard()\
    .with_name('Dashboard Name')\
    .with_charts(chart)


"""
Example 2: Creating a new Dashboard with multiple charts

"""
# With the same filters as above example,
program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

program1 = Data('network.utilization', filter=filters).publish()
chart1 = TimeSeriesChart().with_name('Chart_Name').with_program(program)

program2 = Data('api_errors', filter=filters).publish()
chart2 = TimeSeriesChart().with_name('Chart_Name').with_program(program)

dashboard_with_multiple_charts = Dashboard()\
    .with_name('Dashboard With Multiple Charts')\
    .with_charts(chart, chart1, chart2)


"""
Example 3: Update existing dashboard by removing one of the charts

"""

dashboard_remove_chart = Dashboard()\
    .with_name('Dashboard Name')\
    .with_charts(chart, chart1)

"""
Example 3: Rename and existing chart

"""
chart1 = TimeSeriesChart()\
    .with_name('Chart_Name_Renamed')\
    .with_program(program)
dashboard_rename_chart = Dashboard()\
    .with_name('Dashboard Name')\
    .with_charts(chart, chart1)

if __name__ == '__main__':
    from signal_analog.cli import CliBuilder
    cli = CliBuilder().with_resources(dashboard_with_single_chart,
                                      dashboard_with_multiple_charts,
                                      dashboard_remove_chart,
                                      dashboard_rename_chart)\
        .build()
    cli()
