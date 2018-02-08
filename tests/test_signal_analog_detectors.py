"""Tests pertaining to the `signal_analog.detectors` module."""

import pytest

from email_validator import EmailNotValidError
from signal_analog.detectors import EmailNotification, PagerDutyNotification, \
                                    SlackNotification, HipChatNotification, \
                                    ServiceNowNotification, \
                                    VictorOpsNotification, \
                                    WebhookNotification, TeamNotification, \
                                    TeamEmailNotification


def test_email_valid():
    email = 'foo@bar.com'
    n = EmailNotification(email)
    assert n.options['type'] == 'Email'
    assert n.options['email'] == email


def test_email_invalid():
    with pytest.raises(EmailNotValidError):
        EmailNotification('foo')


def test_pd_valid():
    pd_id = 'foo'
    n = PagerDutyNotification(pd_id)
    assert n.options['type'] == 'PagerDuty'
    assert n.options['credentialId'] == pd_id


def test_pd_invalid():
    with pytest.raises(ValueError):
        PagerDutyNotification('')


def test_slack_valid():
    sid = 'foo'
    channel = 'bar'
    n = SlackNotification(sid, channel)
    assert n.options['type'] == 'Slack'
    assert n.options['credentialId'] == sid
    assert n.options['channel'] == channel


@pytest.mark.parametrize("input_val", [('foo', ''), ('', 'foo')])
def test_two_arity_invalid(input_val):
    (fst, snd) = input_val

    two_arity_charts = [
        SlackNotification,
        HipChatNotification,
        VictorOpsNotification
    ]

    for notification in two_arity_charts:
        with pytest.raises(ValueError):
            notification(fst, snd)
            notification(snd, fst)


def test_hipchat_valid():
    hcid = 'foo'
    room = 'bar'
    n = HipChatNotification(hcid, room)

    assert n.options['type'] == 'HipChat'
    assert n.options['credentialId'] == hcid
    assert n.options['room'] == room


def test_servicenow_valid():
    snid = 'foo'
    n = ServiceNowNotification(snid)

    assert n.options['type'] == 'ServiceNow'
    assert n.options['credentialId'] == snid


def test_servicenow_invalid():
    with pytest.raises(ValueError):
        ServiceNowNotification('')


def test_victorops_valid():
    void = 'foo'
    routing = 'bar'
    n = VictorOpsNotification(void, routing)

    assert n.options['type'] == 'VictorOps'
    assert n.options['credentialId'] == void
    assert n.options['routingKey'] == routing


def test_webhook_valid():
    url = 'foo.com'
    secret = 'foo'

    n = WebhookNotification(url, secret=secret)

    assert n.options['type'] == 'Webhook'
    assert n.options['url'] == url
    assert n.options['secret'] == secret

    # Without a secret
    n2 = WebhookNotification(url)
    assert n2.options['url'] == url
    assert n2.options.get('secret', None) is None


def test_webhook_invalid():
    with pytest.raises(ValueError):
        WebhookNotification('')


def test_team_valid():
    tid = 'go team'

    n = TeamNotification(tid)
    assert n.options['type'] == 'Team'
    assert n.options['team'] == tid

    n_email = TeamEmailNotification(tid)
    assert n_email.options['type'] == 'TeamEmail'
    assert n_email.options['team'] == tid


def test_team_invalid():
    with pytest.raises(ValueError):
        TeamNotification('')
    with pytest.raises(ValueError):
        TeamEmailNotification('')
