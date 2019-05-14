# Migrating from 1.x to 2.0

## Fixed Method Signatures

All breaking changes in the 2.0 release revolve around ammending incorrect
or updated method signatures in `signal_analog`. The below table illustrates
the changes between releases:

| 1.x Method Signature | 2.x Method Signature | Documentation |
|-|-|-|
| `bottom(by=None, over=None)` | `bottom(count=None, percentage=None, by=None)` | [link](https://developers.signalfx.com/signalflow_analytics/methods/bottom_stream_method.html) |
| `delta(by=None, over=None)` | `delta()` | [link](https://developers.signalfx.com/signalflow_analytics/methods/delta_stream_method.html) |
| `percentile(by=None, over=None)` | `percentile(over=None, by=None, percentage=None)` | [link](https://developers.signalfx.com/signalflow_analytics/methods/percentile_stream_method.html) |
| `random(by=None, over=None)` | `random(count, percentage=None, by=None)` | [link](https://developers.signalfx.com/signalflow_analytics/methods/random_stream_method.html) |
| `top(by=None, over=None)` | `bottom(count=None, percentage=None, by=None)` | [link](https://developers.signalfx.com/signalflow_analytics/methods/top_stream_method.html) |
| `timeshift(offset=None)` | `timeshift(offset)` | [link](https://developers.signalfx.com/signalflow_analytics/methods/timeshift_stream_method.html) |
| `ewma(alpha)` | `ewma(alpha=None, over=None)` | [link](https://developers.signalfx.com/signalflow_analytics/methods/ewma_stream_method.html) |
| `promote(property)` | `promote(*properties)` | [link](https://developers.signalfx.com/signalflow_analytics/methods/promote_stream_method.html) |

## Backwards incompatible behavior changes

Charts and Notifications optionally accept `Program` statements in place of raw
flow statements. With version 2 of the library these `Program` objects will
now run through a series of validations in order to warn or prevent bad programs
from being sent to SignalFx.

Validations are now defined in the `Programs.validate` method and can
optionally make use of user-defined validations.

The only default validation for the 2.0 release is one that verifies that
_at least_ one statement in a `Program` is published. This may invalidate
previously accepted `Program`s.
