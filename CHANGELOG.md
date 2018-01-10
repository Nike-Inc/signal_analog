# History

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
