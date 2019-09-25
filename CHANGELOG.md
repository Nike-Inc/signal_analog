## Unrelease changes

* Added `BigPandaNotification` for BigPanda integration within detectors.

## 2.8.0 (2019-09-06)

* Added `groupBy` support to the chart options. Allows grouping for example of HeatMap charts into groups on multiple levels.
* Added support for `colorScale2` option on HeatMap charts. This allows to set custom chart colors for a defined range of values.

## 2.7.2 (2019-05-14)

### Fixed

  - `signal_analog` has learned to use the `groupId` field when updating
  Dashboard resources after the recent Sfx API changes

### Updated

  - As many documentation links as possible since the last doc update from Sfx.
  Notable missing updates are those for 3rd party integration Notifications in
  the `signal_analog.detectors` module.

## 2.7.0 (2019-04-03)

### Updated
  * Removed dashboard numbering for two reasons:
    1. There was a bug in the logic that caused dashboards to be deleted and recreated on update.
    1. The functionality is no longer needed as SignalFx automatically maintains the order that dashboards were provided and allows easy reordering in the UI.
  * AxisOptions are now optional where used

### Fixed

* Fixing applyIfExists option for Dashboard variables.

## 2.6.0 (2019-03-21)

  * AxisOption parameters should be optional.
  * Additional documentation.

## 2.5.0 (2019-03-20)

  * Added `Plot` class, a helper class that gives an interface more like that found in the SignalFx UI.
  * Added `RollupType` enum for specifying the roll-up used in Charts.
  * Added additional documentation links to README.
  * Fix: TextCharts weren't working
  * Fix: YAML load deprecation warning in logging config

## 2.4.0

  * Add numbering to dashboards in a dashboard group for better organization 
  of dashboards

## 2.3.2 (2018-11-12)

  * The `percentile` function on `signal_analog.flow.Data` objects has been
  fixed to use the correct constructor

## 2.3.1 (2018-11-06)

  * signal-analog now prefers `simplejson` if it is available on the path,
  falling back to the `json` module otherwise.

## 2.3.0 (2018-10-30)

  * DashboardGroup has learned how to accept SignalFX Team ids so that they can
  be associated with pre-existing teams via the `with_teams` builder method.

## 2.2.2 (2018-10-03)

### Fixed
  * Add `deprecation` to setup.py.

## 2.2.1 (2018-10-02)

### Changed
  * Added `with_secondary_visualization` function to enable display of various meters (Sparkline, Linear, Radial) in 
  Single Value charts. This replaces the now defunct `with_sparkline_hidden` function. This will not be a 
  'breaking change' until version 3.0.0 when `with_sparkline_hidden` will be removed from `signal_analog`.

  * Added the `deprecation` Python library to this project to note when `with_sparkline_hidden` should be removed. Upon 
  version matching 3.0.0 or higher the tests for that function will begin to fail notifying whoever is releasing that 
  version to remove the defunct `with_sparkline_hidden` function and tests.

## 2.2.0 (2018-09-27)

### Changed
  * Dashboard Create method to accept group id of an existing dashboard group in which case the new dashboard will be
   part of the dashboard group provided

   Example:
```python
response = dashboard\
  .with_charts(memory_chart)\
  .with_api_token('my-api-token')\
  .create(group_id="asdf;lkj")
```
  * Dashboard Group create method to pass group id of the newly created dashboard group to the dashboard create 
  method so that we can avoid  a few redundant calls like cloning and deleting the dashboards

## 2.1.0 (2018-08-21)

### Added

  * ListCharts learned how to filter legend options via the
  `with_legend_options` builder
  * Future chart types that can filter legend options may now take advantage
  of the `signal_analog.charts.LegendOptionsMixin` class
  * The `FieldOption` class has learned to accept `SignalFxFieldOption`s which
  provide mappings between field options seen in the UI and those used in the
  API
      * e.g. `Plot Name` in the UI and `sf_originatingMetric` in the API
  * A new `TextChart` object has been added to `signal_analog.charts` that
  enables text descriptions to be added to dashboards.
  * `PublishLabelOptions` has learned to accept prefix, suffix, and unit
  arguments when labelling data on charts.

### Changed

  * `PublishLabelOptions` has learned to accept all arguments as optional
  with the exception of the `label` argument.

### Fixed

  * A fix has been added for Python 2 users that prevented successful
  dashboard updates.

## 2.0.0 (2018-07-24)

For assistance migrating from 1.x to 2.x please consult the
[migration guide][migration-1x].

### Added

  * Add support for the `dimensions`, `fill`, `integrate`, `kpss`,
  `rateofchange` methods


### Removed

  * `map` method support has been removed
      * It didn't work properly to begin with, and will require some finagling
      to get right given our approach to building SignalFlow statements

### Fixes

  * `top` and `bottom` method signatures have been fixed to use `count`, `by`,
  and `percentage` arguments
  * The following functions have been updated to raise an error if both
  `by` and `over` are defined in the same method call:
      * `count`, `max`, `mean`, `mean_plus_stddev`, `median`, `min`,
      `percentile`, `random`, `size`, `stddev`, `sum`, `variance`
  * `delta` has been updated to no longer accept any method arguments
  * `ewma` has been updated to support the `over` key

## 1.6.0 (2018-07-18)

  * Add combinators for less-than-or-equal-to (`LTE`) and greater-than-or-equal-to (`GTE`)

## 1.5.1 (2018-06-21)

  * Fix detector update logic to include all fields instead of just name/description

## 1.5.0(2018-05-16)

  * Added `include_zero` method to `TimeSeriesChart` to allow setting the `includeZero` option.

## 1.4.0(2018-05-08)

  * Implements functionality to add event overlays and selected (default) event overlays to dashboards 
  at dashboard creation or update. Includes wildcard matching using the asterisk (*) symbol. 

## 1.3.0(2018-04-17)

  * Implementing the rest of the Dashboard Filters: `source` and `time`

## 1.2.0 (2018-04-11)
  * Added an Assign function that will enable more complex detectors which are constructed by combining multiple data streams
  * Added a Ref flow operator that will enable referencing assignments in a way that can be validated at later steps by checking for an Assign object with a match between the reference string and the assignee

## 1.1.0 (2018-04-04)
  * Introducing Dashboard Filters(only variables as of now) which can be configured to provide various filters that affect the behavior of all configured charts (overriding any conflicting filters at the chart level). You may wish to do this in order to quickly change the environment that you're observing for a given set of charts.

## 1.0.0 (2018-04-02)

  * Symbolic release for `signal_analog`. Future version bumps should conform
  to the `semver` policy outlined [here][deployment].

## 0.25.1 (2018-03-22)

  * The timeshift method's arguments changed. Now accepts a single argument for offset.

## 0.24.0 (2018-03-09)

  * Fix string parsing to not exclude boolean False, which is required for certain functions like .publish()

## 0.23.0 (2018-03-06)

  * Added Op class in flow.py to allow multiplying and dividing datastreams
  to create SignalFlow Functions

## 0.22.0 (2018-03-01)

  * Added Mul and Div combinators for multiplying and dividing streams
  * Added "enable" option for publishing a stream. Setting enable=False
    will hide that particular stream in a chart/detector.

## 0.21.0 (2018-02-28)

  * Dashboard Group support has been added giving you the ability group sets of
  dashboards together in a convenient construct
  * Detector support has been added giving you the ability to create detectors
  from scratch or re-use the SignalFlow program of an existing Chart
  * Dashboards and Charts now update via their `id` instead of by name to
  mitigate name conflicts when creating multiple resources with the same name
  * Dry-run results are now more consistent between all resources and expose
  the API call (sans-headers) that would have been made to use for the given
  resource

## 0.20.0 (2018-01-31)

  * Dashboards have learned how to update their child resources (e.g. if you
    add a chart in your config, the change will be reflected when you next run
    your configuration against SignalFx)
  * The CLI builder has learned how to pass dry-run options to its configured resources
  * Minor bugfixes for the `signal_analog.flow` module

## 0.19.1 (2018-01-26)

  * Added click to setup.py

## 0.19.0 (2018-01-19)

  * Added CLI builder to create and update dashboard resources

## 0.18.0 (2018-01-11)

  * Dashboard resources have learned to interactively prompt the user if the user wants to
   create a new dashboard if there is a pre-existing match (this behavior is disabled
      by default).
  * Added "Update Dashboard" functionality where a user can update the properties of a dashboard(only name and description for now)

## 0.17.0 (2018-01-11)
  * Added Heatmap Chart style
     * Added by Jeremy Hicks

## 0.16.0 (2018-01-10)
  * Added the ability to sort a list chart by value ascending/descending
      * Added by Jeremy Hicks

## 0.15.0 (2018-01-08)

  * Added "Scale" to ColorBy class for coloring thresholds in SingleValueChart
      * Added by Jeremy Hicks

## 0.14.0 (2018-01-04)

  * Added List Chart style
      * Added by Jeremy Hicks

## 0.13.0 (2018-01-04)

  * Dashboard resources have learned how to force create themselves in the
  SignalFx API regardless of a pre-existing match (this behavior is disabled
  by default).

## 0.12.0 (2017-12-21)

  * Dashboard resources have learned how to check for themselves in the
  SignalFx API, and will no longer create themselves if an exact match is found

## 0.3.0 (2017-09-25)

  * Adds support for base Resource object. Will be used for Chart/Dashboard
  abstractions in future versions.
  * Adds support for base Chart and TimeSeriesChart objects. Note that some
  TimeSeriesChart builder options have not yet been implemented (and marked
  clearly with NotImplementedErrors)

## 0.2.0 (2017-09-18)

  * Adds support for function combinators like `and`, `or`, and `not`

## 0.1.1 (2017-09-14)

  * Add README documentation

## 0.1.0 (2017-09-14)

  * Initial release

[deployment]: https://github.com/Nike-Inc/signal_analog/wiki/Developers-::-Deployment
[migration-1x]: ./docs/migrating_from_1.x.md
