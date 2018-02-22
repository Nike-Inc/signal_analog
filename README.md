# Signal Analog

A troposphere-like library for building and composing SignalFx SignalFlow
programs into Charts, Dashboards, and Detectors.

The rest of this document assumes familiarity with the SignalFx API, SignalFlow
language, and Chart/Dashboard models.

For more information about the above concepts consult the
[upstream documentation].

If you're looking for pre-built dashboards for existing application frameworks
or tools then please consult the [signal\_analog\_patterns] documentation.

## TOC

  - [Features](#features)
      - [Planned Features](#planned-features)
  - [Installation](#installation)
  - [Usage](#usage)
      - [Building Charts](#charts)
      - [Building Dashboards](#dashboards)
          - [A note on Dashboard names](#dashboard-names)
      - [Updating Dashboards](#dashboards-updates)
      - [Building Dashboard Groups](#dashboard-groups)
          - [A note on Dashboard Group names](#dashboard-group-names)
      - [Updating Dashboard Group](#dashboard-group-updates)      
      - [Talking to the SignalFlow API Directly](#signalflow)
      - [Creating a CLI for your resources](#cli-builder)
  - [Contributing](#contributing)
  - [Credits](#credits)

<a name="features"></a>
## Features

  - Provides bindings for the SignalFlow DSL
  - Provides abstractions for building Charts
  - Provides abstractions for building Dashboards

<a name="planned-features"></a>
### Planned Features

  - High-level constructs for building Detectors

<a name="installation"></a>
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

If you are unable to install the package then you may need to check your Python
configuration so that it conforms to Nike's environment. Consult the
following documentation for more info:

https://confluence.nike.com/x/1kPlCg

<a name="usage"></a>
## Usage

<a name="charts"></a>
### Building Charts

`signal_analog` provides constructs for building charts in the
`signal_analog.charts` module.

Consult the [upstream documentation][charts] for more information on the
Chart API.

Let's consider an example where we would like to build a chart to monitor
memory utilization for a single Riposte applicaton in a single environment.

Riposte reports metrics for application name as `app` and environment as `env`
with memory utilization reporting via the `memory.utilization` metric name.

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
to a chart we would see _all_ timeseries for _all_ Riposte applications
reporting to SignalFx.

We can restrict our view of the data by adding a filter on application name:

```python
from signal_analog.flow import Data, Filter

app_filter = Filter('app', 'LegacyIdMapping')

ts = Data('memory.utilization', filter=app_filter).publish()
```

Now if we created a chart with this program we would only be looking at metrics
that relate to the `LegacyIdMapping` application. Much better, but we're still
looking at instance of `LegacyIdMapping` _regardless_ of the environment it
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

In order for any chart to be created we must provide an API token. Contact
your account administrator for the best way to access your account's API
tokens. If you are unsure who your account administrator is consult
[this document to determine the appropriate contact][sfx-contact].

With API token in hand we can now create our chart in the API:

```python
response = memory_chart.with_api_token('my-api-token').create()
```

As of version `0.3.0` one of two things will happen:

  - We receive some sort of error from the SignalFx API and an exception
  is thrown
  - We successfully created the chart, in which case the JSON response is
  returned as a dictionary.

From this point forward we can see our chart in the SignalFx UI by navigating
to https://app.signalfx.com/#/chart/v2/\<chart\_id\>, where `chart_id` is
the `id` field from our chart response.

<a name="dashboards"></a>
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

See the [note below](#dashboard-names) for caveats on naming dashboards.

Our final task will be to add charts to our dashboard and create it in the API!

```python
response = dash.with_charts(memory_chart).create()
```

At this point one of two things will happen:

  - We receive some sort of error from the SignalFx API and an exception
  is thrown
  - We successfully created the dashboard, in which case the JSON response is
  returned as a dictionary.

<a name="dashboard-names"></a>
#### A note on Dashboard names

`signal_analog` assumes that dashboard names are unique in SignalFx. While at
the time of this writing uniqueness is _not_ enforced by the `v2` API, this
convention _is_ enforced by this library.

We make this assumption so that we avoid easily creating duplicate dashboards
and makes updating existing resources easier without having to manage extra
state outside of the SignalFx API.

<a name="dashboards-updates"></a>
### Updating Dashboards
Once you have dashboard created, you can update the properties like name and descriptions of a dashboard

```python
dash.update(name='updated_dashboard_name', description='updated_dashboard_description')
```
At this point one of two things will happen:

  - We receive some sort of error from the SignalFx API and an exception
  is thrown
  - We successfully updated the dashboard, in which case the JSON response is
  returned as a dictionary with the updated properties.

<a name="dashboard-groups"></a>
### Building Dashboard Groups

`signal_analog` provides constructs for building dashboard groups in the
`signal_analog.dashboards` module.

Consult the [upstream documentation][dashboard-groups] for more information on the
Dashboard Groups API.

Building on the examples described in the previous section, we'd now like to
build a dashboard group containing our dashboards.

First, lets build a couple of Dashboard objects similar to how we did it in the `Building Dashboards` example:

```python
from signal_analog.dashboards import Dashboard, DashboardGroup

dg = DashboardGroup()
dash1 = Dashboard().with_name('My Little Dashboard1: Metrics are Magic').with_charts(memory_chart)
dash2 = Dashboard().with_name('My Little Dashboard2: Metrics are Magic').with_charts(memory_chart)
```
**Note that we are not actually creating the dashboards here using the .create() method as we did it in the dashboards 
example.
This will be taken care by the DashboardGroup()** 

Many of the same methods for dashboards are available on dashboard groups as well, so
let's give our dashboard group a memorable name and configure it's API token:

```python

dg.with_name('My Dashboard Group')\
    .with_api_token('my-api-token')
```

See the [note below](#dashboard-group-names) for caveats on naming dashboard groups.

Our final task will be to add dashboard to our dashboard group and create it in the API!

```python
response = dg.with_dashboards(dash1).create()
```

At this point one of two things will happen:

  - We receive some sort of error from the SignalFx API and an exception
  is thrown
  - We successfully created the dashboard group with the provided dashboard resources, in which case the JSON 
  response is returned as a dictionary.

<a name="dashboard-group-names"></a>
#### A note on Dashboard Group names

`signal_analog` assumes that dashboard group names are unique in SignalFx. While at
the time of this writing uniqueness is _not_ enforced by the `v2` API, this
convention _is_ enforced by this library.

We make this assumption so that we avoid easily creating duplicate dashboard groups
and makes updating existing resources easier without having to manage extra
state outside of the SignalFx API.

<a name="dashboard-group-updates"></a>
### Updating Dashboard Groups
Once you have dashboard group created, you can update the properties like name and descriptions of a dashboard group or 
add new dashboards or delete existing dashboards in a dashboard group

*Example 1:*
```python
dg.update(name='updated_dashboard_group_name', description='updated_dashboard_group_description')
```
*Example 2:*
```python
dg.with_dashboards(dash1, dash2).update()
```

At this point one of two things will happen:

  - We receive some sort of error from the SignalFx API and an exception
  is thrown
  - We successfully updated the dashboard group, in which case the JSON response is
  returned as a dictionary with the updated properties.  

<a name="signalflow"></a>
### Talking to the SignalFlow API Directly

If you need to process SignalFx data outside of their walled garden it may be
useful to call the SignalFlow API directly. Note that you may incur time
penalties when pulling data out due to SignalFx's architecture.

SignalFlow constructs are contained in the `flow` module. The following is an
example SignalFlow program that monitors Riposte RPS metrics for the `foo`
application in the `test` environment.

```python
from signal_analog.flow import Data, Filter
from signal_analog.combinators import And

all_filters = And(Filter('env', 'prod'), Filter('app', 'LegacyIdMapping'))

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

app_filter = Filter('app', 'LegacyIdMapping')
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

<a name="cli-builder"></a>
### Creating a CLI for your resources

`signal_analog` provides builders for fully featured command line clients that
can manage sets of resources. These clients make handling resource updates
more consistent and provide additional.

#### Simple CLI integration

Integrating with the CLI is as simple as importing the builder and passing
it your resources. Let's consider an example where we want to update two
existing dashboards:

```python
#!/usr/bin/env python

# ^ It's always good to include a "hashbang" so that your terminal knows
# how to run your script.

# For more info on the patterns library check out the source here:
# https://bitbucket.nike.com/projects/NIK/repos/signal_analog_patterns/browse
from signal_analog_patterns.riposte.dashboard import RiposteDashboard
from signal_analog.cli import CliBuilder

lids = RiposteDashboard('LegacyIdMapping', env='test')
shoeadmin = RiposteDashboard('shoeadmin', env='test')

if __name__ == '__main__':
  cli = CliBuilder().with_resources(lids, shoeadmin).build()
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

<a name="contributing"></a>
## Contributing

Consult the [docs here for more info about contributing](CONTRIBUTING.md).

Activity diagrams for this project are located in the `docs/activity` directory
and can be generated locally by running the `make activity_diagrams` task in
the root of the project. If you don't have `plantuml` installed you can do
so via Homebrew (`brew install plantuml`).

<a name="credits"></a>
## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[nik/nike-python-template](https://bitbucket.nike.com/projects/NIK/repos/nike_python_template/browse)
project template.

[upstream documentation]: https://developers.signalfx.com/docs/signalflow-overview
[charts]: https://developers.signalfx.com/reference#charts-overview-1
[sfx-contact]: https://confluence.nike.com/x/GlHiCQ
[terrific]: https://media.giphy.com/media/jir4LEGA68A9y/200.gif
[dashboards]: https://developers.signalfx.com/v2/reference#dashboards-overview
[dashboard-groups] : https://developers.signalfx.com/v2/reference#dashboard-groups-overview
[signal\_analog\_patterns]: https://bitbucket.nike.com/projects/NIK/repos/signal_analog_patterns/browse
