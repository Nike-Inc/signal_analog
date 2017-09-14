# Signal Analog

A troposphere-like library for building and composing SignalFx SignalFlow
programs.

## Features

  - Provides bindings for the SignalFlow DSL

### Planned Features

  - High-level constructs for building Charts

## Installation

Add `signal_analog` to the requirements file in your project:

```
# requirements.txt
# ... your other dependencies
signal_analog
# ... your other dependencies
```

Then run the following command to update your environment:

```
pip install -r requirements.txt
```

If you are unable to install the package then you may need to check your Python
configuration so that functions correctly inside the Nike network. For more
information on how to do please consult this document:

https://confluence.nike.com/display/~ffreir/Nike+Artifactory+and+Python

## Usage

SignalFlow constructs are contained in the `flow` module. The following is an
example SignalFlow program that monitors Riposte RPS metrics for the `foo`
application in the `test` environment.

```python
from signal_analog.flow import Data, Filter

program = Data('requests.count', filter=Filter('app', 'foo', 'env', 'test'))
```

You now have an object representation of the SignalFlow program. To take it for
a test ride you can use the official SignalFx client like so:

```python
# Original example found here:
# https://github.com/signalfx/signalfx-python#executing-signalflow-computations

import signalfx
from signal_analog.flow import Data, Filter

app_filter = Filter('app', 'LegacyIdMapping', 'env', 'prod')
program = Data('requests.count', filter=app_filter).publish()

with signalfx.SignalFx().signalflow('MY_TOKEN') as flow:
    print('Executing {0} ...'.format(program))
    computation = flow.execute(str(program))

    for msg in computation.stream():
        if isinstance(msg, signalfx.signalflow.messages.DataMessage):
            print('{0}: {1}'.format(msg.logical_timestamp_ms, msg.data))
        if isinstance(msg, signalfx.signalflow.messages.EventMessage):
            print('{0}: {1}'.format(msg.timestamp_ms, msg.properties))
```

## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[nik/nike-python-template](https://bitbucket.nike.com/projects/NIK/repos/nike-python-template/browse)
project template.
