#!/usr/bin/env python

"""Examples for the `signal_analog.filters` module."""

from signal_analog.flow import Data, Filter
from signal_analog.charts import TimeSeriesChart
from signal_analog.dashboards import Dashboard
from signal_analog.combinators import And
from signal_analog.filters import DashboardFilters, FilterVariable, FilterSource, FilterTime

"""
Example 1: Creating a new Dashboard with Filter Variable

This creates a new dashboard for the app specified and with the charts provided and with the Dashboard Filter provided
"""
filters = And(Filter('app', 'my-app'), Filter('env', 'test'))
program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

app_var = FilterVariable().with_alias('application name') \
    .with_property('app') \
    .with_is_required(True) \
    .with_value('my-app')

app_filter = DashboardFilters() \
    .with_variables(app_var)

dashboard_with_single_filter_variable = Dashboard()\
    .with_name('Dashboard Name')\
    .with_charts(chart)\
    .with_filters(app_filter)


"""
Example 2: Creating a new Dashboard with multiple filters

"""
# With the same filters as above example,
program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

app_var = FilterVariable().with_alias('application name') \
    .with_property('app') \
    .with_is_required(True) \
    .with_value('my-app1', 'my-app2')

env_var = FilterVariable().with_alias('env')\
    .with_property('env')\
    .with_is_required(True)\
    .with_value('prod')

app_filter = DashboardFilters() \
    .with_variables(app_var, env_var)

dashboard_with_multiple_filter_variables = Dashboard()\
    .with_name('Dashboard With Multiple Filters')\
    .with_charts(chart)\
    .with_filters(app_filter)


"""
Example 3: Creating a new Dashboard with source filter

"""
# With the same filters as above example,
program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

aws_src = FilterSource().with_property("aws_region").with_value('us-west-2')

app_filter = DashboardFilters() \
    .with_sources(aws_src)

dashboard_with_source_filter = Dashboard()\
    .with_name('Dashboard With Source Filter')\
    .with_charts(chart)\
    .with_filters(app_filter)


"""
Example 4: Creating a new Dashboard with time(as string) filter

"""
# With the same filters as above example,
program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

time = FilterTime().with_start("-1h").with_end("Now")

app_filter = DashboardFilters() \
    .with_time(time)

dashboard_with_time_as_string_filter = Dashboard()\
    .with_name('Dashboard With Time as String Filter')\
    .with_charts(chart)\
    .with_filters(app_filter)


"""
Example 5: Creating a new Dashboard with time(as integer) filter

"""
# With the same filters as above example,
program = Data('cpu.utilization', filter=filters).publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

time = FilterTime().with_start(1523808000000).with_end(1523894400000)

app_filter = DashboardFilters() \
    .with_time(time)

dashboard_with_time_as_integer_filter = Dashboard()\
    .with_name('Dashboard With Time as Integer Filter')\
    .with_charts(chart)\
    .with_filters(app_filter)


"""
Example 6: Update an existing Dashboard by removing one of the filters

"""

app_filter = DashboardFilters().with_variables(app_var)

dashboard_remove_filter = Dashboard()\
    .with_name('Dashboard With Multiple Filters')\
    .with_charts(chart)\
    .with_filters(app_filter)


if __name__ == '__main__':
    from signal_analog.cli import CliBuilder
    cli = CliBuilder().with_resources(dashboard_with_single_filter_variable,
                                      dashboard_with_multiple_filter_variables,
                                      dashboard_with_source_filter,
                                      dashboard_with_time_as_string_filter,
                                      dashboard_with_time_as_integer_filter,
                                      dashboard_remove_filter)\
        .build()
    cli()
