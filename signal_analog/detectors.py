"""Detector objects representable in the SignalFx API."""

from enum import Enum
import signal_analog.util as util
from email_validator import validate_email


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
        util.is_valid(pd_id)
        self.options = {'type': 'PagerDuty', 'credentialId': pd_id}


class SlackNotification(Notification):
    """A slack notification for detector rules."""

    def __init__(self, slack_id, channel_name):
        """Initializes a new Slack notification rule.

        This does not setup a Slack integration for you, one must already exist
        before using this notification type. No validation is done to ensure
        that a Slack integration id is valid.

        See the integration page for more detail:
        https://developers.signalfx.com/v2/reference#slack-integration-model

        Arguments:
            slack_id: the slack integration id to use
            channel_name: the name of the channel to send alerts to
        """
        util.is_valid(slack_id)
        util.is_valid(channel_name)

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

        util.is_valid(hp_id)
        util.is_valid(room_name)

        self.options = {
            'type': 'HipChat',
            'credentialId': hp_id,
            'room': room_name
        }


class ServiceNowNotification(Notification):
    """A ServiceNow notifiction for detector rules."""

    def __init__(self, sn_id):
        """Initializes a new ServiceNow notification.

        This does not setup a ServiceNow integration for you, one must already
        exist before using this notification type. No validation is done to
        ensure that a ServiceNow integration id is valid.

        Arguments:
            sn_id: the ServiceNow integration id to use
        """
        util.is_valid(sn_id)

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
        util.is_valid(vo_id)
        util.is_valid(routing_key)

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
        util.is_valid(url)

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
        util.is_valid(team_id)

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
        util.is_valid(team_id)

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
        """A label matching a `detect` label within the program text."""
        util.is_valid(label)
        self.options.update({'detectLabel': label})
        return self

    def with_description(self, description):
        """Human-readable description for this rule."""
        util.is_valid(description)
        self.options.update({'description': description})
        return self

    def with_severity(self, severity):
        """Severity of the rule."""
        util.in_given_enum(severity, Severity)
        self.options.update({'severity': severity.value})
        return self

    def is_disabled(self, disabled=False):
        """When true, notifications and events will not be generated for the
           detect label. False by default.
        """
        self.options.update({'disabled': disabled})
        return self

    def with_notifications(self, *notifications):
        """Determines where notifications will be sent when an incident occurs.
        """
        def yield_notifications(ns):
            for n in ns:
                if not issubclass(n.__class__, Notification):
                    msg = "Rule notifications only accept Notification " + \
                          "objects. Instead we got '{0}'"
                    raise ValueError(msg.format(n.__class__.__name__))
                else:
                    yield n.options

        to_add = list(yield_notifications(notifications))
        self.options.update({'notifications': to_add})
        return self

    def with_parameterized_body(self, body):
        """Custom notifiction message body for this rule when the alert is
           triggeered.

           Content can contain ASCII chars and is parsed as plain text. Quotes
           can be escaped using a backslash, and new line characters are
           indicated with "\\n"

           Available variables can be found here:
           https://docs.signalfx.com/en/latest/detect-alert/set-up-detectors.html#message-variables
        """
        util.is_valid(body)
        self.options.update({'parameterizedBody': body})
        return self

    def with_parameterized_subject(self, subject):
        """Custom notification message subject for this rule when an alert is
        triggered.

        See the documentation for `with_parameterized_body` for more detail.
        """
        util.is_valid(subject)
        self.options.update({'parameterizedSubject': subject})
        return self

    def with_runbook_url(self, url):
        """URL of the page to consult when an alert is triggered.

        This can be used with custom notification messages. It can be
        referenced using the {{runbookUrl}} template var.
        """
        util.is_valid(url)
        self.options.update({'runbookUrl': url})
        return self

    def with_tip(self, tip):
        """Plain text suggested first course of action, such as a command line
        to execute.

        This can be used with custom notification messages. It can be
        referenced using the {{tip}} template var.
        """
        util.is_valid(tip)
        self.options.update({'tip': tip})
        return self


class Time(Enum):
    Relative = "relative"
    Absolute = "absolute"


class TimeConfig(object):
    """Controls the time span visualized for a detector."""

    def __init__(self):
        self.options = {}

    def with_type(self, time_type):
        """The type of time span defined."""
        util.in_given_enum(time_type, Time)
        self.options.update({'type': time_type.value})
        return self

    def __add_millis__(self, millis, key):
        util.is_valid(millis)
        self.options.update({key: millis})
        return self

    def with_range(self, millis):
        """The time range _prior_ to now to visualize, in millis.

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

        NOTE: only valid for Time.absolute configs.
        """
        if self.options.get('type', None) == Time.Relative.value:
            msg = 'A start time can only be set on absolute time configs.'
            raise ValueError(msg)
        return self.__add_millis__(millis, 'start')

    def with_end(self, millis):
        """Milliseconds since epoch to stop a visualization.

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
        if not isinstance(config, TimeConfig):
            msg = 'Attempting to set "{0}" to a time config for this ' +\
                  'visualization when we expected a "{1}"'
            raise ValueError(
                msg.format(config.__class__.__name__, TimeConfig.__name__))

        self.options.update({'time': config.options})
        return self

    def show_data_markers(self, show_markers=False):
        """When ture, markers will be drawn for each datapoint within the
           visualization."""
        self.options.update({'showDataMarkers': show_markers})
        return self
