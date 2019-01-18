"""Detector objects representable in the SignalFx API."""

from copy import deepcopy
import click
from enum import Enum
from signal_analog.resources import Resource
from signal_analog.charts import Chart
from signal_analog.flow import Program
from six import string_types
import signal_analog.util as util
from email_validator import validate_email
from signal_analog.errors import \
    ResourceMatchNotFoundError, \
    ResourceAlreadyExistsError


class Notification(object):
    """A notification model to be attached to a detector."""
    pass


class EmailNotification(Notification):
    """An email notification for detector rules."""

    def __init__(self, email):
        """Initialize a new Email notification.

        Arguments:
            email: the email to notify. This value is validated a little
                   stricter than other notification values to prevent unwanted
                   behavior when a detector actually fires.
        """
        valid_email = validate_email(email, check_deliverability=False)
        self.options = {'type': 'Email', 'email': valid_email['email']}


class PagerDutyNotification(Notification):
    """A PagerDuty notification for detector rules."""

    def __init__(self, pd_id):
        """Initializes a new PagerDuty notification.

        This does not setup a PagerDuty integration for you, one must already
        exist before using this notification type. No validation is done to
        ensure that a PD integration id is valid.

        These values will typically differ depending on the on-call rotation
        you want to add to the detector.

        See the integration page for more detail:
        https://developers.signalfx.com/v2/reference#pagerduty-integration-model

        Arguments:
            pd_id: the id of the PagerDuty integration to include.
        """
        util.assert_valid(pd_id)
        self.options = {'type': 'PagerDuty', 'credentialId': pd_id}


class SlackNotification(Notification):
    """A slack notification for detector rules."""

    def __init__(self, slack_id, channel_name):
        """Initializes a new Slack notification rule.

        This does not setup a Slack integration for you, one must already exist
        before using this notification type. No validation is done to ensure
        that a Slack integration id is valid.

        See the integration page for more detail:
        https://developers.signalfx.com/v2.1/reference#slack-integration-model

        Arguments:
            slack_id: the slack integration id to use
            channel_name: the name of the channel to send alerts to
        """
        util.assert_valid(slack_id)
        util.assert_valid(channel_name)

        self.options = {
            'type': 'Slack',
            'credentialId': slack_id,
            'channel': channel_name
        }


class HipChatNotification(Notification):
    """A HipChat notification for detector rules."""

    def __init__(self, hp_id, room_name):
        """Initializes a new HipChat notification.

        This does not setup a Slack integration for you, one must already exist
        before using this notification type. No validation is done to ensure
        that a HipChat integration id is valid.

        See the integration page for more detail:
        https://developers.signalfx.com/v2/reference#hipchat-integration-model

        Arguments:
            hp_id: the HipChat integration id to use
            room_name: the HipChat room name to post integrations to
        """

        util.assert_valid(hp_id)
        util.assert_valid(room_name)

        self.options = {
            'type': 'HipChat',
            'credentialId': hp_id,
            'room': room_name
        }


class ServiceNowNotification(Notification):
    """A ServiceNow notification for detector rules."""

    def __init__(self, sn_id):
        """Initializes a new ServiceNow notification.

        This does not setup a ServiceNow integration for you, one must already
        exist before using this notification type. No validation is done to
        ensure that a ServiceNow integration id is valid.

        Arguments:
            sn_id: the ServiceNow integration id to use
        """
        util.assert_valid(sn_id)

        self.options = {
            'type': 'ServiceNow',
            'credentialId': sn_id
        }


class VictorOpsNotification(Notification):
    """A VictorOps notification for detector rules."""

    def __init__(self, vo_id, routing_key):
        """Initializes a new VictorOps notification.

        This does not setup a VictorOps integration for you, one must already
        exist before using this notification type. No validation is done to
        ensure that a VictorOps integration id is valid.

        Arguments:
            vo_id: the VictorOps integration id to use
            routing_key: a VictorOps routing key
        """
        util.assert_valid(vo_id)
        util.assert_valid(routing_key)

        self.options = {
            'type': 'VictorOps',
            'credentialId': vo_id,
            'routingKey': routing_key
        }


class WebhookNotification(Notification):
    """A Webhook notification for detector rules."""

    def __init__(self, url, secret=None):
        """Initializes a new webhook notification.

        Arguments:
            url: the URL to call back
            secret: optional, when provided the request will contain a
                    `X-SFX-Signature` header containing the Base64 encoded
                    HMAC-SHA1 digest of the request body using the shared
                    secret.
        """
        util.assert_valid(url)

        self.options = {
            'type': 'Webhook',
            'url': url
        }

        if secret:
            self.options.update({'secret': secret})


class TeamNotification(Notification):
    """A team notification for detector rules."""

    def __init__(self, team_id):
        """Initializes a team notification.

        No validation is done to verify that a team id exists in SignalFx.

        Arguments:
            team_id: the id of the team to message.
        """
        util.assert_valid(team_id)

        self.options = {
            'type': 'Team',
            'team': team_id
        }


class TeamEmailNotification(Notification):
    """A team e-mail notification for detector rules."""

    def __init__(self, team_id):
        """Initializes a new team e-mail notification.

        No validation is done to verify that a team id exists in SignalFx.

        Arguments:
            team_id: the id of the team to e-mail.
        """
        util.assert_valid(team_id)

        self.options = {
            'type': 'TeamEmail',
            'team': team_id
        }


class Severity(Enum):
    """Available severity levels for detector rules."""

    Critical = "Critical"
    Warning = "Warning"
    Major = "Major"
    Minor = "Minor"
    Info = "Info"


class Rule(object):
    """Determines who/what is notified when a detector fires."""

    def __init__(self):
        """Initializes a new rule."""
        self.options = {}

    def for_label(self, label):
        """A label matching a `detect` label within the program text.

            Arguments:
                label: String
        """
        util.assert_valid(label)
        self.options.update({'detectLabel': label})
        return self

    def with_description(self, description):
        """Human-readable description for this rule.

            Arguments:
                description: String
        """
        util.assert_valid(description)
        self.options.update({'description': description})
        return self

    def with_severity(self, severity):
        """Severity of the rule.
            SignalFx supports five severity levels: Critical, Warning, Major, Minor, and Info.

            Arguments:
                severity: String
        """
        util.in_given_enum(severity, Severity)
        self.options.update({'severity': severity.value})
        return self

    def is_disabled(self, disabled=False):
        """When true, notifications and events will not be generated for the
           detect label. False by default.

        Arguments:
            disabled: Boolean
        """
        self.options.update({'disabled': disabled})
        return self

    def with_notifications(self, *notifications):
        """Determines where notifications will be sent when an incident occurs.

        Arguments:
            *notifications: List of notification destinations

            See https://developers.signalfx.com/reference#section-notifications for notification destinations.
        """
        util.check_collection(notifications, Notification)
        self.options.update({
            'notifications': list(map(lambda x: x.options, notifications))
        })
        return self

    def with_parameterized_body(self, body):
        """Custom notification message body for this rule when the alert is
           triggered.

           Arguments:
               body: String

           Content can contain ASCII chars and is parsed as plain text. Quotes
           can be escaped using a backslash, and new line characters are
           indicated with "\\n"

           Available variables can be found here:
           https://docs.signalfx.com/en/latest/detect-alert/set-up-detectors.html#message-variables
        """
        util.assert_valid(body)
        self.options.update({'parameterizedBody': body})
        return self

    def with_parameterized_subject(self, subject):
        """Custom notification message subject for this rule when an alert is
        triggered.

        Arguments:
            subject: String

        See the documentation for `with_parameterized_body` for more detail.
        """
        util.assert_valid(subject)
        self.options.update({'parameterizedSubject': subject})
        return self

    def with_runbook_url(self, url):
        """URL of the page to consult when an alert is triggered.

        Arguments:
            url: String containing a valid URL

        This can be used with custom notification messages. It can be
        referenced using the {{runbookUrl}} template var.
        """
        util.assert_valid(url)
        self.options.update({'runbookUrl': url})
        return self

    def with_tip(self, tip):
        """Plain text suggested first course of action, such as a command line
        to execute.

        Arguments:
            tip: String

        This can be used with custom notification messages. It can be
        referenced using the {{tip}} template var.
        """
        util.assert_valid(tip)
        self.options.update({'tip': tip})
        return self


class Time(Enum):
    """Set relative or absolute timespan."""
    Relative = "relative"
    Absolute = "absolute"


class TimeConfig(object):
    """Controls the time span visualized for a detector."""

    def __init__(self):
        self.options = {}

    def with_type(self, time_type):
        """The type of time span defined.

        Arguments:
            time_type: String either 'relative' or 'absolute'
        """
        util.in_given_enum(time_type, Time)
        self.options.update({'type': time_type.value})
        return self

    def __add_millis__(self, millis, key):
        util.assert_valid(millis)
        self.options.update({key: millis})
        return self

    def with_range(self, millis):
        """The time range _prior_ to now to visualize, in millis.

        Arguments:
            millis: Int

        NOTE: only valid for Time.relative configs.
        Example:
            60000 would visualize the last 60 seconds.
        """
        if self.options.get('type', None) == Time.Absolute.value:
            msg = 'A range can only be set on relative time configs.'
            raise ValueError(msg)

        return self.__add_millis__(millis, 'range')

    def with_start(self, millis):
        """Milliseconds since epoch to start a visualization.

        Arguments:
            millis: Int

        NOTE: only valid for Time.absolute configs.
        """
        if self.options.get('type', None) == Time.Relative.value:
            msg = 'A start time can only be set on absolute time configs.'
            raise ValueError(msg)
        return self.__add_millis__(millis, 'start')

    def with_end(self, millis):
        """Milliseconds since epoch to stop a visualization.

        Arguments:
            millis: Int

        NOTE: only valid for Time.absolute configs.
        """
        if self.options.get('type', None) == Time.Relative.value:
            msg = 'An end time can only be set on absolute time configs.'
            raise ValueError(msg)
        return self.__add_millis__(millis, 'end')


class VisualizationOptions(object):
    """Visualization options for detectors."""

    def __init__(self):
        self.options = {}

    def with_time_config(self, config):
        """Set up time configuration"""
        if not isinstance(config, TimeConfig):
            msg = 'Attempting to set "{0}" to a time config for this ' +\
                  'visualization when we expected a "{1}"'
            raise ValueError(
                msg.format(config.__class__.__name__, TimeConfig.__name__))

        self.options.update({'time': config.options})
        return self

    def show_data_markers(self, show_markers=False):
        """When true, markers will be drawn for each datapoint within the
           visualization.

           Arguments:
               show_markers: Boolean
       """
        self.options.update({'showDataMarkers': show_markers})
        return self


class Detector(Resource):
    """Resource encapsulating Detectors in the SignalFx API.

    A detector is a collection of rules that define who should be notified when
    certain detect functions within SignalFlow fire alerts. Each rule maps a
    detect label to a severity and a list of notifications. When the conditions
    within the given detect function are fulfilled, notifications will be sent
    to the destinations defined in the rule for that detect function.
    """

    def __init__(self, session=None):
        super(Detector, self).__init__(endpoint='/detector', session=session)
        self.options = {}

    def with_rules(self, *rules):
        """Rules to include in the detector."""
        util.check_collection(rules, Rule)
        self.options.update({
            'rules': list(map(lambda x: x.options, rules))
        })
        return self

    def with_program(self, program):
        """Program defining the detector."""
        if not issubclass(program.__class__, Program):
            msg = 'Signal Analog Detectors only support Program objects, we' +\
                   ' got a "{0}" instead.'
            raise ValueError(msg.format(program.__class__.__name__))

        if isinstance(program, Program):
            program.validate()

        self.options.update({
            'programText': str(program)
        })
        return self

    def with_max_delay(self, delay):
        """The number of milliseconds to wait for late datapoints before rejecting them.

        Arguments:
            delay: Int
        """
        util.assert_valid(delay)
        self.options.update({'maxDelay': delay})
        return self

    def with_visualization_options(self, opts):
        """Visualization opts to use when viewing the detector in SignalFx."""
        if not issubclass(opts.__class__, VisualizationOptions):
            msg = 'Got a "{0} when we were expecting a "{0}"'
            raise ValueError(msg.format(
                opts.__class__.__name__, VisualizationOptions.__name__))

        self.options.update({'visualizationOptions': opts.options})
        return self

    def with_tags(self, *tags):
        """Tags associated with the detector.

        Arguments:
            *tags: List of tags to attach to the detector
        """
        util.check_collection(tags, string_types)
        self.options.update({'tags': list(tags)})
        return self

    def with_teams(self, *team_ids):
        """Team IDs to associate the detector to.

        Arguments:
            *team_ids: List of team_ids to attach to the detector
        """
        util.check_collection(team_ids, string_types)
        self.options.update({'teams': list(team_ids)})
        return self

    def from_chart(self, chart, update_fn):
        """Given a Chart and an update fn, return a SignalFlow program.

        Arguments:
            chart: the Chart object containing the desired SignalFlow program.
            update_fn: a function of type Program -> Program, allowing you
                       to access the program of a given chart and return a
                       modified version for this detector.
        """
        if not issubclass(chart.__class__, Chart):
            msg = 'Expected a Chart but got a "{0}" instead when building ' +\
                  'a Detector named "{1}".'
            raise ValueError(msg.format(
                chart.__class__.__name__,
                self.__get__('name', 'undefined')
            ))

        program = deepcopy(chart.__get__('programText', Program()))

        if not issubclass(program.__class__, Program):
            msg = """
                  Detector.from_chart only supports Charts that implement a Program. "{0}"
                  contains a "{1}".

                  You might consider contacting the Chart author to update their configuration to
                  implement a proper `Program` from the `signal_analog.flow` module.
                  """
            raise ValueError(msg.format(
                chart.__class__.__name__,
                program.__class__.__name__
            ))

        self.options.update({'programText': str(update_fn(program))})
        return self

    def create(self, dry_run=False, force=False, interactive=False):
        """Creates a Detector in SignalFx.

        Arguments:
            dry_run: Boolean to test a dry run
            force: Boolean to force a create
            interactive: Boolean to start interactive create

        See: https://developers.signalfx.com/v2/reference#detector
        """

        if self.__create_helper__(force=force, interactive=interactive):
            return self.__action__('post', self.endpoint,
                                   lambda x: x,
                                   dry_run=dry_run, interactive=interactive,
                                   force=force)

    def update(self, name=None, description=None, dry_run=False):
        """Update a detector in the SignalFx API.

        Arguments:
            name: String defining name of detector to update
            description: String defining description of updated detector
            dry_run: Boolean to test a dry run

        See: https://developers.signalfx.com/v2/reference#detectorid-2
        """

        updated_opts = dict(self.options)
        if name:
            updated_opts.update({'name': name})
        if description:
            updated_opts.update({'name': description})

        if dry_run:
            msg = """
                  Updates the Detector named "{0}". If it doesn't exist, we'll create a new one.
                  API calls being executed:
                      GET {1}
                      PUT {2}
                  Request Body:
                      {3}
                  """
            click.echo(msg.format(
                self.__get__('name'),
                self.base_url + self.endpoint,
                self.base_url + self.endpoint + '/<id>',
                updated_opts
            ))
            return None

        query_result = self.__find_existing_resources__()

        try:
            self.__find_existing_match__(query_result)

        except ResourceAlreadyExistsError:
            detector = self.__filter_matches__(query_result)

            detector.update(updated_opts)

            return self.__action__('put', self.endpoint + '/' + detector['id'],
                                   lambda x: detector)
        except ResourceMatchNotFoundError:
            return self.create(dry_run=dry_run)
