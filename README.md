[![CircleCI](https://circleci.com/gh/Nike-Inc/signal_analog.svg?style=svg)](https://circleci.com/gh/Nike-Inc/signal_analog)
# signal_analog

A [`troposphere`](https://github.com/cloudtools/troposphere)-inspired library
for programmatic, declarative definition and management of SignalFx Charts,
Dashboards, and Detectors.

This library assumes a basic familiarity with resources in SignalFx. For a
good overview of the SignalFx API consult the [upstream documentation][sfxdocs].

## TOC

  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
      - [Building Charts](#building-charts)
      - [Building Dashboards](#building-dashboards)
      - [Updating Dashboards](#updating-dashboards)
      - [Dashboard Filters](#providing-dashboard-filters)
      - [Dashboard Event Overlays](#dashboard-event-overlays-and-selected-event-overlays)
      - [Creating Detectors](#creating-detectors)
          - [Detectors That Combine Data Streams](#detectors-that-combine-data-streams)
          - [Building Detectors from Existing Charts](#building-detectors-from-existing-charts)
      - [Using Flow and Combinator Functions In Formulas](#using-flow-and-combinator-functions-in-formulas)
      - [Building Dashboard Groups](#building-dashboard-groups)
      - [Updating Dashboard Group](#updating-dashboard-groups)
      - [Talking to the SignalFlow API Directly](#talking-to-the-signalflow-api-directly)
      - [General `Resource` Guidelines](#general-resource-guidelines)
      - [Creating a CLI for your resources](#creating-a-cli-for-your-resources)
  - [Documentation](#documentation)
  - [Example Code](#example-code)
  - [Contributing](#contributing)

## Features

  - Provides bindings for the SignalFlow DSL
  - Provides abstractions for:
      - Charts
      - Dashboards, DashboardGroups
      - Detectors
  - A CLI builder to wrap resource definitions (useful for automation)

## Installation

Add `signal_analog` to the requirements file in your project:

```
# requirements.txt
# ... your other dependencies
signal_analog
```

Then run the following command to update your environment:

```
pip install -r requirements.txt
```

## Usage

`signal_analog` provides two kinds of abstractions, one for building resources
in the SignalFx API and the other for describing metric timeseries through the
[Signal Flow DSL][signalflow].

The following sections describe how to use `Resource` abstractions in
conjunction with the [Signal Flow DSL][signalflow].

### Building Charts

`signal_analog` provides constructs for building charts in the
`signal_analog.charts` module.

Consult the [upstream documentation][charts] for more information Charts.

Let's consider an example where we would like to build a chart to monitor
memory utilization for a single applicaton in a single environment.

This assumes a service reports metrics for application name as `app` and
environment as `env` with memory utilization reporting via the
`memory.utilization` metric name.

In a timeseries chart, all data displayed on the screen comes from at least one
`data` definition in the SignalFlow language. Let's begin by defining our
timeseries:

```python
from signal_analog.flow import Data

ts = Data('memory.utilization')
```

In SignalFlow parlance a timeseries is only displayed on a chart if it has been
"published". All stream functions in SignalFlow have a `publish` method that
may be called at the _end_ of all timeseries transformations.

```python
ts = Data('memory.utilization').publish()
```

As a convenience, all transformations on stream functions return the callee,
so in the above example `ts` remains bound to an instance of `Data`.

Now, this timeseries isn't very useful by itself; if we attached this program
to a chart we would see _all_ timeseries for _all_ [Riposte] applications
reporting to SignalFx!

We can restrict our view of the data by adding a filter on application name:

```python
from signal_analog.flow import Data, Filter

app_filter = Filter('app', 'foo')

ts = Data('memory.utilization', filter=app_filter).publish()
```

Now if we created a chart with this program we would only be looking at metrics
that relate to the `foo` application. Much better, but we're still
looking at instance of `foo` _regardless_ of the environment it
lives in.

What we'll want to do is combine our `app_filter` with another filter for the
environment. The `signal_analog.combinators` module provides some helpful
constructs for achieving this goal:

```python
from signal_analog.combinators import And

env_filter = Filter('env', 'prod')

all_filters = And(app_filter, env_filter)

ts = Data('memory.utilization', filter=all_filters).publish()
```

Excellent! We're now ready to create our chart.

First, let's give our chart a name:

```python
from signal_analog.charts import TimeSeriesChart

memory_chart = TimeSeriesChart().with_name('Memory Used %')
```

Like it's `flow` counterparts, `charts` adhere to the builder pattern for
constructing objects that interact with the SignalFx API.

With our name in place, let's go ahead and add our program:

```python
memory_chart = TimeSeriesChart().with_name('Memory Used %').with_program(ts)
```

Each Chart understands how to serialize our SignalFlow programs appropriately,
so it is sufficient to simply pass in our reference here.

Finally, let's change the plot type on our chart so that we see solid areas
instead of flimsy lines:

```python
from signal_analog.charts import PlotType

memory_chart = TimeSeriesChart()\
                 .with_name('Memory Used %')\
                 .with_program(ts)
                 .with_default_plot_type(PlotType.area_chart)
```

[Terrific]; there's only a few more details before we have a complete chart.

In the following sections we'll see how we can create dashboards from
collections of charts.

### Building Dashboards

`signal_analog` provides constructs for building charts in the
`signal_analog.dashboards` module.

Consult the [upstream documentation][dashboards] for more information on the
Dashboard API.

Building on the examples described in the previous section, we'd now like to
build a dashboard containing our memory chart.

We start with the humble `Dashboard` object:

```python
from signal_analog.dashboards import Dashboard

dash = Dashboard()
```

Many of the same methods for charts are available on dashboards as well, so
let's give our dashboard a memorable name and configure it's API token:

```python
dash.with_name('My Little Dashboard: Metrics are Magic')\
    .with_api_token('my-api-token')
```

Our final task will be to add charts to our dashboard and create it in the API!

```python
response = dash\
  .with_charts(memory_chart)\
  .with_api_token('my-api-token')\
  .create()
```

At this point one of two things will happen:

  - We receive some sort of error from the SignalFx API and an exception
  is thrown
  - We successfully created the dashboard, in which case the JSON response is
  returned as a dictionary.

Also, if you have an existing Dashboard Group and you want this new dashboard to be part of that dashboard group, you
 can pass that group id of the dashboard group when creating the dashboard. Something like this:

```python
response = dash\
  .with_charts(memory_chart)\
  .with_api_token('my-api-token')\
  .create(group_id="asdf;lkj")
``` 
 
Now, storing API keys in source isn't ideal, so if you'd like to see how you
can pass in your API keys at runtime check the documentation below to see how
you can [dynamically build a CLI for your resources](#cli-builder).

### Updating Dashboards
Once you have created a dashboard you can update properties like name and
description:

```python
dash.update(
    name='updated_dashboard_name',
    description='updated_dashboard_description'
)
```

`Dashboard` updates will also update any `Chart` configurations it owns.

    Note: If the given dashboard does not already exist, `update` will create a new dashboard for you

### Providing Dashboard Filters

Dashboards can be configured to provide various filters that affect the behavior of all configured charts (overriding any conflicting filters at the chart level). You may wish to do this in order to quickly change the environment that you're observing for a given set of charts.


```python
from signal_analog.filters import DashboardFilters, FilterVariable, FilterSource, FilterTime
app_var = FilterVariable().with_alias('app')\
.with_property('app')\
.with_is_required(True)\
.with_value('foo')

env_var = FilterVariable().with_alias('env')\
.with_property('env')\
.with_is_required(True)\
.with_value('prod')

aws_src = FilterSource().with_property("aws_region").with_value('us-west-2')

time = FilterTime().with_start("-1h").with_end("Now")

app_filter = DashboardFilters() \
.with_variables(app_var, env_var) \ 
.with_sources(aws_src) \
.with_time(time)
```
So, here we are creating a few filters "app=foo" and "env=prod", 
a source filter "aws_region=us-west-2" and
a time filter "-1h till Now"
Now we can pass this config to a dashboard object:

```python
response = dash\
.with_charts(memory_chart)\
.with_api_token('my-api-token')\
.with_filters(app_filter)\
.create()
```

If you are updating an existing dashboard:

```python
response = dash\
.with_filters(app_filter)\
.update()
```

### Dashboard Event Overlays and Selected Event Overlays

To view events overlayed on your charts within a dashboard requires an event to be viewed, a chart with showEventLines
enabled, and a dashboard with the correct eventOverlays settings (and selectedEventOverlays to show events by default).

Assuming that the events you would like to see exist; you would make a chart with showEventLines like so:

```python
from signal_analog.flow import Data
from signal_analog.charts import TimeSeriesChart
program = Data('cpu.utilization').publish()
chart = TimeSeriesChart().with_name('Chart With Event Overlays')\
    .with_program(program).show_event_lines(True)
```
With our chart defined, we are ready to prepare our event overlays and selected event overlays for the dashboard.
First we define the event signals we would like to match. In this case, we will look for an event named "test" (include
 leading and/or trailing asterisks as wildcards if you need partial matching).
Next we use those event signals to create our eventOverlays, making sure to include a color index for our event's symbol,
and setting event line to True.
We also pass our event signals along to the selectedEventOverlays, which will tell the dashboard to display matching
events by default.

```python
from signal_analog.eventoverlays import EventSignals, EventOverlays, SelectedEventOverlays
events = EventSignals().with_event_search_text("*test*")\
    .with_event_type("eventTimeSeries")

eventoverlay = EventOverlays().with_event_signals(events)\
    .with_event_color_index(1)\
    .with_event_line(True)

selectedeventoverlay = SelectedEventOverlays()\
    .with_event_signals(events)
```

Next we combine our chart, our event overlay, and our selected event overlay into a dashboard object:

```python
from signal_analog.dashboards import Dashboard
dashboard_with_event_overlays = Dashboard().with_name('Dashboard With Overlays')\
    .with_charts(chart)\
    .with_event_overlay(eventoverlay)\
    .with_selected_event_overlay(selectedeventoverlay)
```

Finally we build our resources in SignalFX with the cli builder:

```python
if __name__ == '__main__':
    from signal_analog.cli import CliBuilder
    cli = CliBuilder().with_resources(dashboard_with_event_overlays)\
        .build()
    cli()
```

### Creating Detectors

`signal_analog` provides a means of managing the lifecycle of `Detectors` in
the `signal_analog.detectors` module. As of `v0.21.0` only a subset of
the full Detector API is supported.

Consult the [upstream documentation][detectors] for more information about
Detectors.

Detectors are comprised of a few key elements:

  - A name
  - A SignalFlow Program
  - A set of rules for alerting

We start by building a `Detector` object and giving it a name:

```python
from signal_analog.detectors import Detector

detector = Detector().with_name('My Super Serious Detector')
```

We'll now need to give it a program to alert on:

```python
from signal_analog.flow import Program, Detect, Filter, Data
from signal_analog.combinators import GT

# This program fires an alert if memory utilization is above 90% for the
# 'bar' application.
data = Data('memory.utilization', filter=Filter('app', 'bar')).publish(label='A')
alert_label = 'Memory Utilization Above 90'
detect = Detect(GT(data, 90)).publish(label=alert_label)

detector.with_program(Program(detect))
```

With our name and program in hand, it's time to build up an alert rule that we
can use to notify our teammates:

```python
# We provide a number of notification strategies in the detectors module.
from signal_analog.detectors import EmailNotification, Rule, Severity

info_rule = Rule()\
  # From our detector defined above.
  .for_label(alert_label)\
  .with_severity(Severity.Info)\
  .with_notifications(EmailNotification('me@example.com'))

detector.with_rules(info_rule)

# We can now create this resource in SignalFx:
detector.with_api_token('foo').create()
# For a more robust solution consult the "Creating a CLI for your Resources"
# section below.
```

To add multiple alerting rules we would need to use different `detect`
statements with distinct `label`s to differentiate them from one another.

#### Detectors that Combine Data Streams

More complex detectors, like those created as a function of two other data
streams, require a more complex setup including data stream assignments.
If we wanted to create a detector that watched for an average above a certain
threshold, we may want to use the quotient of the sum() of the data and the
count() of the datapoints over a given period of time.

```python
from signal_analog.flow import \
    Assign, \
    Data, \
    Detect, \
    Ref, \
    When

from signal_analog.combinators import \
    Div, \
    GT

program = Program( \
    Assign('my_var', Data('cpu.utilization')) \
    Assign('my_other_var', Data('cpu.utilization').count()) \
    Assign('mean', Div(Ref('my_var'), Ref('my_other_var'))) \
    Detect(When(GT(Ref('mean'), 2000))) \
)

print(program)
```

The above code generates the following program:

```
my_var = data('cpu.utilization')
my_other_var = data('cpu.utilization').count()
mean = (my_var / my_other_var)

when(detect(mean > 2000))
```

#### Building Detectors from Existing Charts

We can also build up Detectors from an existing chart, which allows us to reuse
our SignalFlow program and ensure consistency between what we're monitoring
and what we're alerting on.

Let's assume that we already have a chart defined for our use:

```python
from signal_analog.flow import Program, Data
from signal_analog.charts import TimeSeriesChart

program = Program(Data('cpu.utilization').publish(label='A'))
cpu_chart = TimeSeriesChart().with_name('Disk Utilization').with_program(program)
```

In order to alert on this chart we'll use the `from_chart`  builder for
detectors:

```python
from signal_analog.combinators import GT
from signal_analog.detectors import Detector
from signal_analog.flow import Detect

# Alert when CPU utilization rises above 95%
detector = Detector()\
    .with_name('CPU Detector')\
    .from_chart(
        cpu_chart,
        # `p` is the Program object from the cpu_chart we passed in.
        lambda p: Detect(GT(p.find_label('A'), 95).publish(label='Info Alert'))
    )
```

The above example won't actually alert on anything until we add a `Rule`, which
you can find examples for in the previous section.

### Linking Charts to Existing Detectors

To see a visualization of a Detector's status from within a chart, the `signal_analog.flow` module provides an Alert data stream that can create a signal flow statement. That statement can be appended to the charts Program object. In this example we assume a Detector was previously created and exists. To create the link we will need the detector id. One place to obtain the detector id is to navigate to the detector in the web user interface. The url will have the id in it. The url will look somehting like: https://app.signalfx.com/#/detector/v2/{detector_id}

To refresh our memory, our previous chart example was:

```python
from signal_analog.combinators import And

ts = Data('memory.utilization', filter=all_filters).publish()
```

We can append an additional alert data stream. Import Program and Alerts form the `signal_analog.flow` module. First we need to wrap the Data object in a Program object:

```python
ts_program = Program(ts)
```

Then we can create a new statement using an Alert object with the detector id, publish the stream, and append the new statement to our program:

```python
notifications = Alerts(detector_id).publish()
ts_program.statements.append(notifications)
```

The alert should show as a green box around the chart if the Detector is not in Alarm.

### Using Flow and Combinator Functions In Formulas

`signal_analog` also provides functions for combining SignalFlow statements
into more complex SignalFlow Formulas. These sorts of Formulas can be useful
when creating more complex detectors and charts. For instance, if you would like
to multiply one data stream by another and receive the sum of that Formula,
it can be accomplished using Op and Mul like so:

```python
from signal_analog.flow import Op, Program, Data
from signal_analog.combinators import Mul

# Multiply stream A by stream B and sum the result
    A = Data('request.mean')

    B = Data('request.count')

    C = Op(Mul(A,B)).sum()
```

Print(C) in the above example would produce the following output:

```
(data("request.mean") * data("request.count")).sum()
```

### Building Dashboard Groups

`signal_analog` provides abstractions for building dashboard groups in the
`signal_analog.dashboards` module.

Consult the [upstream documentation][dashboard-groups] for more information on
the Dashboard Groups API.

Building on the examples described in the previous section, we'd now like to
build a dashboard group containing our dashboards.

First, lets build a couple of Dashboard objects similar to how we did it in
the `Building Dashboards` example:

```python
from signal_analog.dashboards import Dashboard, DashboardGroup

dg = DashboardGroup()
dash1 = Dashboard().with_name('My Little Dashboard1: Metrics are Magic')\
    .with_charts(memory_chart)
dash2 = Dashboard().with_name('My Little Dashboard2: Metrics are Magic')\
    .with_charts(memory_chart)
```
**Note: we do not create Dashboard objects ourselves, the DashboardGroup object
is responsible for creating all child resources.**

Many of the same methods for dashboards are available on dashboard groups as
well, so let's give our dashboard group a memorable name and configure it's
API token:

```python

dg.with_name('My Dashboard Group')\
    .with_api_token('my-api-token')
```

Our final task will be to add dashboard to our dashboard group and create it
in the API!

```python
response = dg\
    .with_dashboards(dash1)\
    .with_api_token('my-api-token')\
    .create()
```

Now, storing API keys in source isn't ideal, so if you'd like to see how you
can pass in your API keys at runtime check the documentation below to see how
you can [dynamically build a CLI for your resources](#cli-builder).

### Updating Dashboard Groups

Once you have created a dashboard group, you can update properties like name
and description of a dashboard group or add/remove dashboards in a group.

*Example 1:*

```python
dg.with_api_token('my-api-token')\
    .update(name='updated_dashboard_group_name',
            description='updated_dashboard_group_description')
```

*Example 2:*

```python
dg.with_api_token('my-api-token').with_dashboards(dash1, dash2).update()
```

### Talking to the SignalFlow API Directly

If you need to process SignalFx data outside the confince of the API it may be
useful to call the SignalFlow API directly. Note that you may incur time
penalties when pulling data out depending on the source of the data
(e.g. AWS/CloudWatch).

SignalFlow constructs are contained in the `flow` module. The following is an
example SignalFlow program that monitors an API services (like [Riposte])
RPS metrics for the `foo` application in the `test` environment.

```python
from signal_analog.flow import Data, Filter
from signal_analog.combinators import And

all_filters = And(Filter('env', 'prod'), Filter('app', 'foo'))

program = Data('requests.count', filter=all_filters)).publish()
```

You now have an object representation of the SignalFlow program. To take it for
a test ride you can use the official SignalFx client like so:

```python
# Original example found here:
# https://github.com/signalfx/signalfx-python#executing-signalflow-computations

import signalfx
from signal_analog.flow import Data, Filter
from signal_analog.combinators import And

app_filter = Filter('app', 'foo')
env_filter = Filter('env', 'prod')
program = Data('requests.count', filter=And(app_filter, env_filter)).publish()

with signalfx.SignalFx().signalflow('MY_TOKEN') as flow:
    print('Executing {0} ...'.format(program))
    computation = flow.execute(str(program))

    for msg in computation.stream():
        if isinstance(msg, signalfx.signalflow.messages.DataMessage):
            print('{0}: {1}'.format(msg.logical_timestamp_ms, msg.data))
        if isinstance(msg, signalfx.signalflow.messages.EventMessage):
            print('{0}: {1}'.format(msg.timestamp_ms, msg.properties))
```

### General `Resource` Guidelines

#### Charts Always Belong to Dashboards

It is always assumed that a Chart belongs to an existing Dashboard. This makes
it easier for the library to manage the state of the world.

#### Resource Names are Unique per Account

In a `signal_analog` world it is assumed that all resource names are unique.
That is, if we have two dashboards 'Foo Dashboard', when we attempt to update
_either_ dashboard via `signal_analog` we expect to see errors.

Resource names are assumed to be unique in order to simplify state management
by the library itself. In practice we have not found this to be a major
inconvenience.

#### Configuration is the Source of Truth

When conflicts arise between the state of a resource in your configuration and
what SignalFx thinks that state should be, this library **always** prefers the
local configuration.

#### Only "CCRUD" Methods Interact with the SignalFx API

`Resource` objects contain a number of builder methods to enable a "fluent" API
when describing your project's dashboards in SignalFx. It is assumed that these
methods do not perform state-affecting actions in the SignalFx API.

Only "CCRUD" (Create, Clone, Read, Update, and Delete) methods will affect the
state of your resources in SignalFx.

### Creating a CLI for your Resources

`signal_analog` provides builders for fully featured command line clients that
can manage the lifecycle of sets of resources.

#### Simple CLI integration

Integrating with the CLI is as simple as importing the builder and passing
it your resources. Let's consider an example where we want to update two
existing dashboards:

```python
#!/usr/bin/env python

# ^ It's always good to include a "hashbang" so that your terminal knows
# how to run your script.

from signal_analog.dashboards import Dashboard
from signal_analog.cli import CliBuilder

ingest_dashboard = Dashboard().with_name('my-ingest-service')
service_dashboard = Dashboard().with_name('my-service')

if __name__ == '__main__':
  cli = CliBuilder()\
      .with_resources(ingest_dashboard, service_dashboard)\
      .build()
  cli()
```

Assuming we called this `dashboards.py` we could run it in one of two ways:

  - Give the script execution rights and run it directly
  (typically `chmod +x dashboards.py`)
      - `./dashboards.py --api-key mykey update`
  - Pass the script in to the Python executor
      - `python dashboards.py --api-key mykey update`

If you want to know about the available actions you can take with your new
CLI you can always the `--help` command.

```shell
./dashboards.py --help
```

This gives you the following features:
  - Consistent resource management
      - All resources passed to the CLI builder can be updated with one
      `update` invocation, rather than calling the `update()` method on each
      resource indvidually
  - API key handling for all resources
      - Rather than duplicating your API key for each resource, you can instead
      invoke the CLI with an API key
      - This also provides a way to supply keys for users who don't want to
      store them in source control (that's you! don't store your keys in
      source control)

## Documentation

- [Signal Analog Documentation](https://signal-analog.readthedocs.io/)
- [Introductory Article on Medium](https://medium.com/nikeengineering/introducing-signal-analog-the-troposphere-like-library-for-automating-monitoring-resources-c99eb8c2dca7)

## Example Code

- See [examples](https://github.com/Nike-Inc/signal_analog/tree/master/examples) included in this project.

## Contributing

Please read our [docs here for more info about contributing](CONTRIBUTING.md).

[sfxdocs]: https://developers.signalfx.com/
[signalflow]: https://developers.signalfx.com/signalflow_analytics/signalflow_overview.html
[charts]: https://developers.signalfx.com/charts_reference.html
[terrific]: https://media.giphy.com/media/jir4LEGA68A9y/200.gif
[dashboards]: https://developers.signalfx.com/dashboards_reference.html
[dashboard-groups]: https://developers.signalfx.com/dashboard_groups_reference.html
[detectors]: https://developers.signalfx.com/detectors_reference.html
[Riposte]: https://github.com/Nike-inc/riposte
