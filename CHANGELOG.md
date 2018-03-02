# History

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
