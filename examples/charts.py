#!/usr/bin/env python

"""Examples for the `signal_analog.charts` module."""

from signal_analog.charts \
    import TimeSeriesChart, PlotType, PublishLabelOptions, PaletteColor, AxisOption
from signal_analog.flow import Data, Filter, Program, Plot, RollupType, Sum
from signal_analog.combinators import And

"""
Example 1: single-use chart

This is useful when you just want to create a chart and aren't worried
about re-usability.
"""

# Look at the mean of the cpu.user metric for my-app in the prod environment
app_filter = And(Filter('app', 'my-app'), Filter('env', 'prod'))
program = Program(
    Data('cpu.user', filter=app_filter).mean().publish('A')
)

chart = TimeSeriesChart()\
    .with_name('CPU Used %')\
    .with_description('% CPU used by user')\
    .stack_chart(True)\
    .with_default_plot_type(PlotType.area_chart)\
    .with_program(program)

"""
Example 2: make a re-usable chart (or template)

This is useful when you want your chart to be broadly applicable/used by others
"""


class UserCpuUsedPercentChart(TimeSeriesChart):

    def __init__(self, app, env='prod'):
        super(UserCpuUsedPercentChart, self).__init__()
        self.with_name('CPU Used % from template class')
        self.with_description(
            '% CPU used by type (user, system, i/o, stolen, etc)')
        self.stack_chart(True)
        self.with_default_plot_type(PlotType.area_chart)
        self.with_program(self.__program__(app, env))
        self.with_publish_label_options(
            PublishLabelOptions(
                'A', 0, PaletteColor.hot_pink,
                PlotType.area_chart, 'User CPU %'
            )
        )

    def __program__(self, app, env):
        app_filter = And(Filter('app', 'my-app'), Filter('env', 'prod'))
        return Program(
            Data('cpu.user', filter=app_filter).mean().publish('A')
        )


chart_from_templ = UserCpuUsedPercentChart('my-app')


if __name__ == '__main__':
    from signal_analog.cli import CliBuilder
    cli = CliBuilder().with_resources(chart, chart_from_templ).build()
    cli()


"""
Example 3: make a more advanced chart using more options.

This example charts two metrics on the same chart with a different scale for each.
"""

function_name = 'my-lambda'

chart = TimeSeriesChart() \
            .with_name("Lambda " + function_name + " Invocations") \
            .with_description("") \
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True) \
            .with_publish_label_options(
                PublishLabelOptions(
                    label='Invocations',
                    palette_index=PaletteColor.green
                ),
                PublishLabelOptions(
                    label='Duration',
                    palette_index=PaletteColor.gray,
                    y_axis=1, # right y-axis
                    plot_type=PlotType.line_chart, # override of main chart type for 1 metric
                    value_unit='Millisecond' # SignalFx will automatically convert units to human-readable format
                )
            ) \
            .with_axes([
                AxisOption(label="Count", min=0), # left Y-axis
                AxisOption(label="Latency", min=0) # right Y-axis
            ]) \
            .with_program(
                Program(
                    Plot(
                        assigned_name="A",
                        signal_name="Invocations", # metric name
                        filter=And(
                            Filter("FunctionName", function_name),
                            Filter("namespace", "AWS/Lambda"),
                            Filter("stat", "sum") # CloudWatch sends several stats for each metric so you need to filter
                        ),
                        rollup=RollupType.sum,
                        fx=[Sum(by=["aws_account_id", "FunctionName"])],
                        label="Invocations"),
                    Plot(
                        assigned_name="B",
                        signal_name="Duration",
                        filter=And(
                            Filter("FunctionName", function_name),
                            Filter("namespace", "AWS/Lambda"),
                            Filter("stat", "mean")
                        ),
                        rollup=RollupType.max,  # max rollup is used here so you can still see spikes over longer windows
                        fx=[Sum(by=["aws_account_id", "FunctionName"])],
                        label="Duration")
                )
            )