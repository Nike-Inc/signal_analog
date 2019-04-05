#!/usr/bin/env python
#
# Python script for creating/updating a Data Pipeline Dashboard group.
#
# For example, a Data Pipeline might include messages on a SQS queue triggers a Lambda that then writes to
# Dynamo, with another Lambda listening to the Stream, triggering something else, etc.
#
# Layout follows a two column design with each item in the pipeline getting at least one left and right chart.
#
# Left chart typically displays invocations, read/write activity, and latency.
# Right chart gives errors, throttles, iterator age.
#
# Example Usage:
#    ./full_data_pipeline_cloudwatch_example.py --api-key="${sfx_api_key}" update
#
from enum import Enum

from signal_analog.charts import TimeSeriesChart, PlotType, PublishLabelOptions, PaletteColor, \
    AxisOption
from signal_analog.cli import CliBuilder
from signal_analog.combinators import And, Not
from signal_analog.dashboards import DashboardGroup, Dashboard
from signal_analog.filters import DashboardFilters, FilterVariable, FilterTime
from signal_analog.flow import Program, Max, Mean, Sum, Filter, Plot, RollupType

aws_account_id = '123456789012'


def create_lambda_charts(function_name, description):
    """
    Create Lambda charts

    Left chart shows activity and latency.

    Right chart shows errors, throttles, and iterator age.

    """
    charts = []

    charts.append(

        TimeSeriesChart() \
            .with_name("Lambda " + function_name + " Invocations") \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='Invocations',
                palette_index=PaletteColor.green
            ),
            PublishLabelOptions(
                label='Duration',
                palette_index=PaletteColor.gray,
                y_axis=1,
                plot_type=PlotType.line_chart,
                value_unit='Millisecond'
            )
        )
            .with_axes([AxisOption(label="Count", min=0), AxisOption(label="Latency", min=0)])
            .with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="Invocations",
                    filter=And(
                        Filter("FunctionName", function_name),
                        Filter("namespace", "AWS/Lambda"),
                        Filter("stat", "sum")
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
    )

    charts.append(

        TimeSeriesChart() \
            .with_name("Lambda " + function_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='Errors',
                palette_index=PaletteColor.rust
            ),
            PublishLabelOptions(
                label='Throttles',
                palette_index=PaletteColor.sunflower
            ),
            PublishLabelOptions(
                label='IteratorAge',
                value_unit='Millisecond',
                plot_type=PlotType.area_chart,
                palette_index=PaletteColor.slate_blue,
                y_axis=1
            )
        ).with_axes([AxisOption(label="Count", min=0), AxisOption(label="Age", min=0, max=(1000 * 60 * 60 * 36))])
            .with_program(
            Program(
                Plot(
                    assigned_name="B",
                    signal_name="Errors",
                    filter=And(
                        Filter("FunctionName", function_name),
                        Filter("namespace", "AWS/Lambda"),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "FunctionName"])],
                    label="Errors"),
                Plot(
                    assigned_name="C",
                    signal_name="Throttles",
                    filter=And(
                        Filter("FunctionName", function_name),
                        Filter("namespace", "AWS/Lambda"),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "FunctionName"])],
                    label="Throttles"),
                Plot(
                    assigned_name="D",
                    signal_name="IteratorAge",
                    filter=And(
                        Filter("FunctionName", function_name),
                        Filter("Resource", function_name),
                        Filter("namespace", "AWS/Lambda"),
                        Filter('stat', 'upper')
                    ),
                    rollup=RollupType.max,  # max rollup is used here so you can still see spikes over longer windows
                    # Max here is just to get rid of bad extra metric in Sfx
                    fx=[Max(by=["aws_account_id", "FunctionName"])],
                    label="IteratorAge")

            )
        )
    )

    return charts


def create_kinesis_charts(stream_name, description):
    """
    Create Kinesis charts

    Left chart shows incoming records and outgoing records.

    Right chart shows errors, throttles, and iterator age.

    """
    charts = []

    sum_filter = And(
        Filter("StreamName", stream_name),
        Filter("namespace", "AWS/Kinesis"),
        Filter("stat", "sum")
    )

    charts.append(

        TimeSeriesChart() \
            .with_name("Kinesis Stream " + stream_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='IncomingRecords',
                palette_index=PaletteColor.green
            ),
            PublishLabelOptions(
                label='GetRecords.Records',
                palette_index=PaletteColor.light_green
            )
        ).with_axes([AxisOption(label="Count")])
            .with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="IncomingRecords",
                    filter=sum_filter,
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "StreamName"])],
                    label="IncomingRecords"),
                Plot(
                    assigned_name="B",
                    signal_name="GetRecords.Records",
                    filter=sum_filter,
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "StreamName"])],
                    label="GetRecords.Records")

            )
        )
    )

    charts.append(

        TimeSeriesChart() \
            .with_name("Kinesis Stream " + stream_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='ReadThroughputExceeded',
                palette_index=PaletteColor.rust,
                y_axis=0
            ),
            PublishLabelOptions(
                label='WriteThroughputExceeded',
                palette_index=PaletteColor.tangerine,
                y_axis=0
            ),
            PublishLabelOptions(
                label='GetRecords.IteratorAge',
                palette_index=PaletteColor.sunflower,
                value_unit='Millisecond',
                plot_type=PlotType.area_chart,
                y_axis=1
            )).with_axes([AxisOption(label="Count"), AxisOption(label="Age")])
            .with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="ReadProvisionedThroughputExceeded",
                    filter=sum_filter,
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "StreamName"])],
                    label="ReadThroughputExceeded"),
                Plot(
                    assigned_name="B",
                    signal_name="WriteProvisionedThroughputExceeded",
                    filter=sum_filter,
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "StreamName"])],
                    label="WriteThroughputExceeded"),
                Plot(
                    assigned_name="C",
                    signal_name="GetRecords.IteratorAgeMilliseconds",
                    filter=And(

                        Filter("StreamName", stream_name),
                        Filter("namespace", "AWS/Kinesis"),
                        Filter("stat", "upper")
                    ),
                    rollup=RollupType.max,  # max rollup is used here so you can still see spikes over longer windows
                    fx=[Sum(by=["aws_account_id", "StreamName"])],
                    label="GetRecords.IteratorAge")
            )
        )
    )

    return charts


def create_sqs_charts(queue_name, description):
    """
    Create SQS charts

    Left chart shows messages sent/deleted and number visible.

    Right chart shows deadletter queue and age of oldest message.
    """
    charts = []

    filter = And(

        Filter("QueueName", queue_name),
        Filter("namespace", "AWS/SQS"),
        Filter("stat", "sum")
    )

    charts.append(

        TimeSeriesChart() \
            .with_name("SQS " + queue_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='NumberOfMessagesSent',
                palette_index=PaletteColor.green
            ),
            PublishLabelOptions(
                label='NumberOfMessagesDeleted',
                palette_index=PaletteColor.light_green
            ),
            PublishLabelOptions(
                label='ApproximateNumberOfMessagesVisible',
                palette_index=PaletteColor.sky_blue,
                plot_type=PlotType.line_chart
            )
        ).with_axes([AxisOption(label="Count", min=0)])
            .with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="NumberOfMessagesSent",
                    filter=filter,
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "QueueName"])],
                    label="NumberOfMessagesSent"),
                Plot(
                    assigned_name="B",
                    signal_name="NumberOfMessagesDeleted",
                    filter=filter,
                    rollup=RollupType.sum,
                    fx=[Sum(by=["aws_account_id", "QueueName"])],
                    label="NumberOfMessagesDeleted"),
                Plot(
                    assigned_name="C",
                    signal_name="ApproximateNumberOfMessagesVisible",
                    filter=filter,
                    rollup=RollupType.max,
                    fx=[Max(by=["aws_account_id", "QueueName"])],
                    label="ApproximateNumberOfMessagesVisible")

            )
        )
    )

    charts.append(

        TimeSeriesChart() \
            .with_name("SQS " + queue_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='DeadLetterMessages',
                palette_index=PaletteColor.mulberry,
                y_axis=0
            ),
            PublishLabelOptions(
                label='ApproximateAgeOfOldestMessage',
                palette_index=PaletteColor.sunflower,
                value_unit='Second',
                plot_type=PlotType.area_chart,
                y_axis=1
            )
        ).with_axes([AxisOption(label="Count", min=0), AxisOption(label="Age", min=0)])
            .with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="ApproximateNumberOfMessagesVisible",
                    filter=And(
                        # assumes naming convention for DL queues
                        Filter("QueueName", queue_name + "-deadletter", queue_name + "-dlq"),
                        Filter("namespace", "AWS/SQS"),
                        Filter("stat", "upper")
                    ),
                    rollup=RollupType.max,
                    fx=[Sum(by=["aws_account_id", "QueueName"])],
                    label="DeadLetterMessages"),
                Plot(
                    assigned_name="B",
                    signal_name="ApproximateAgeOfOldestMessage",
                    filter=And(
                        Filter("QueueName", queue_name),
                        Filter("namespace", "AWS/SQS"),
                        Filter("stat", "upper")
                    ),
                    rollup=RollupType.max,  # max rollup is used here so you can still see spikes over longer windows
                    fx=[Max(by=["aws_account_id", "QueueName"])],
                    label="ApproximateAgeOfOldestMessage")
            )
        )
    )

    return charts


def create_dynamodb_charts(table_name, description):
    """
    Create charts for DynamoDB Table.

    Left chart shows read/write capacity consumed, plus latency.

    Right chart shows Errors and Throttling.
    """

    charts = []

    charts.append(

        TimeSeriesChart() \
            .with_name("Dynamo Table " + table_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='ConsumedReadCapacity',
                palette_index=PaletteColor.green
            ),
            PublishLabelOptions(
                label='ConsumedWriteCapacity',
                palette_index=PaletteColor.light_green
            ),
            PublishLabelOptions(
                label='Latency',
                palette_index=PaletteColor.gray,
                plot_type=PlotType.line_chart,
                value_unit='Millisecond',
                y_axis=1
            )
        ).with_axes([AxisOption(label="Units", min=0), AxisOption(label="Latency", min=0)])
            .with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="ConsumedReadCapacityUnits",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["TableName", "aws_account_id"])],
                    label="ConsumedReadCapacity"
                ),
                Plot(
                    assigned_name="B",
                    signal_name="ConsumedWriteCapacityUnits",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["TableName", "aws_account_id"])],
                    label="ConsumedWriteCapacity"
                ),
                Plot(
                    assigned_name="C",
                    signal_name="SuccessfulRequestLatency",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "mean")
                    ),
                    rollup=RollupType.max,
                    fx=[Mean(by=["TableName", "aws_account_id"])],
                    label="Latency"
                )
            )
        )
    )

    charts.append(

        TimeSeriesChart() \
            .with_name("Dynamo Table " + table_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='ThrottledRequests',
                palette_index=PaletteColor.rust
            ),
            PublishLabelOptions(
                label='ReadThrottle',
                palette_index=PaletteColor.tangerine
            ),
            PublishLabelOptions(
                label='WriteThrottle',
                palette_index=PaletteColor.sunflower
            ),
            PublishLabelOptions(
                label='SystemErrors',
                palette_index=PaletteColor.rose,
                y_axis=1
            )
        ).with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="ThrottledRequests",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["TableName", "aws_account_id"])],
                    label="ThrottledRequests"
                ),
                Plot(
                    assigned_name="B",
                    signal_name="ReadThrottleEvents",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["TableName", "aws_account_id"])],
                    label="ReadThrottle"
                ),
                Plot(
                    assigned_name="C",
                    signal_name="WriteThrottleEvents",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["TableName", "aws_account_id"])],
                    label="WriteThrottle"
                ),
                Plot(
                    assigned_name="D",
                    signal_name="SystemErrors",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "sum"),
                        Not(Filter("Operation", "GetRecords"))  # GetRecords is a Dynamo Stream operation
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["TableName", "aws_account_id"])],
                    label="SystemErrors")
            )
        )
    )

    return charts


def create_dynamodb_with_stream_charts(table_name, description):
    """
    Create charts for DynamoDB Table that has a Stream enabled.

    First left chart shows read/write capacity consumed, plus latency.
    First right chart shows Errors and Throttling on the table.

    Second left chart shows records returned on the Stream.
    Second right chart shows errors on the Stream.
    """
    charts = []

    charts.extend(create_dynamodb_charts(table_name, description))

    charts.append(

        TimeSeriesChart() \
            .with_name("Dynamo Stream " + table_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='ReturnedRecordsCount',
                palette_index=PaletteColor.green,
            )
        ).with_program(
            Program(
                Plot(
                    assigned_name="A",
                    signal_name="ReturnedRecordsCount",
                    filter=And(
                        Filter("TableName", table_name),
                        Filter("stat", "sum")
                    ),
                    rollup=RollupType.sum,
                    fx=[Sum(by=["TableName", "aws_account_id"])],
                    label="ReturnedRecordsCount")

            )
        )
    )

    charts.append(

        # This chart is usually empty because these kinds of Stream errors don't seem to happen much
        TimeSeriesChart() \
            .with_name("Dynamo Stream " + table_name) \
            .with_description(description)
            .with_default_plot_type(PlotType.column_chart) \
            .with_chart_legend_options("sf_metric", show_legend=True)
            .with_publish_label_options(
            PublishLabelOptions(
                label='SystemErrors',
                palette_index=PaletteColor.rose,
                y_axis=1
            )
        ).with_program(
            Plot(
                assigned_name="A",
                signal_name="SystemErrors",
                filter=And(
                    Filter("TableName", table_name),
                    Filter("stat", "sum"),
                    Filter("Operation", "GetRecords")  # Streams only have 1 operation
                ),
                rollup=RollupType.sum,
                fx=[Sum(by=["TableName", "aws_account_id"])],
                label="SystemErrors")
        )
    )

    return charts


class AwsResourceType(Enum):
    """
    Defines resource type
    """
    Lambda = "Lambda"
    DynamoDb = "DynamoDB Table"
    DynamoDbWithStream = "DynamoDB Table w/ Stream"
    SqsQueue = "SQS Queue"
    KinesisStream = "Kinesis Stream"


class AwsResouce(object):
    """
    Generic AWS Resource
    """

    def __init__(self, type, name, description):
        self.type = type
        self.name = name
        self.description = description


def create_pipeline_dashboard(pipeline_name, resources):
    """
    Creates a Dashboard for a Data Pipeline that is defined by a list of AwsResources
    """
    charts = []

    # When defining our Dashboard we could have just called the functions above to create the charts
    # we wanted but instead we've further abstracted by defining AWS Resource Types that can now
    # map to functions.
    for resource in resources:
        if resource.type == AwsResourceType.Lambda:
            charts.extend(create_lambda_charts(resource.name, resource.description))
        elif resource.type == AwsResourceType.DynamoDb:
            charts.extend(create_dynamodb_charts(resource.name, resource.description))
        elif resource.type == AwsResourceType.DynamoDbWithStream:
            charts.extend(create_dynamodb_with_stream_charts(resource.name, resource.description))
        elif resource.type == AwsResourceType.SqsQueue:
            charts.extend(create_sqs_charts(resource.name, resource.description))
        elif resource.type == AwsResourceType.KinesisStream:
            charts.extend(create_kinesis_charts(resource.name, resource.description))
        else:
            raise ValueError("unknown type " + str(resource.type))

    return Dashboard() \
        .with_name(pipeline_name) \
        .with_charts(*charts) \
        .with_filters(
        DashboardFilters() \
            .with_variables(FilterVariable() \
                            .with_property("aws_account_id")
                            .with_alias("aws_account_id")
                            .with_value(aws_account_id)
                            .with_apply_if_exists(True))
            .with_time(FilterTime().with_start("-7d").with_end("Now"))
    )


if __name__ == '__main__':
    dashboards = []
    dashboards.append(create_pipeline_dashboard("My Data Pipeline Dashboard", [

        AwsResouce(
            AwsResourceType.SqsQueue,
            'some-queue',
            'This queue is triggered by a SNS topic'
        ),

        AwsResouce(
            AwsResourceType.Lambda,
            'some-lambda',
            'Lambda listens to Queue and writes to DynamoDB'
        ),

        AwsResouce(
            AwsResourceType.DynamoDbWithStream,
            'my-table',
            'Updated by lambda'
        ),

        AwsResouce(
            AwsResourceType.Lambda,
            'another-lambda',
            'Lambda listens to DynamoDB stream and writes to Kinesis stream'
        ),

        AwsResouce(
            AwsResourceType.KinesisStream,
            'some-kinesis-stream',
            'Some stream with consumers'
        )

    ]))

    # TODO: by simply calling the `create_pipeline_dashboard()` function we can add additional Dashboards in a config style

    group = DashboardGroup() \
        .with_name("My Data Pipeline Dashboard Group") \
        .with_dashboards(*dashboards)

    cli = CliBuilder().with_resources(group).build()
    cli()
