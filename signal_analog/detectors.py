"""Detector objects representable in the SignalFx API."""

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

