"""Tests pertaining to the `signal_analog.detectors` module."""

import re
import pytest

from email_validator import EmailNotValidError
from signal_analog.detectors import EmailNotification, PagerDutyNotification, \
                                    SlackNotification, HipChatNotification, \
                                    ServiceNowNotification, \
                                    VictorOpsNotification, \
                                    WebhookNotification, TeamNotification, \
                                    TeamEmailNotification, Rule, Severity


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


def test_rule_init():
    assert Rule().options == {}


def test_rule_for_label():
    expected = 'foo'
    rule = Rule().for_label(expected)
    assert rule.options['detectLabel'] == expected


@pytest.mark.parametrize('method',
    ['for_label', 'with_description', 'with_severity', 'with_notifications',
     'with_parameterized_body', 'with_parameterized_subject',
     'with_runbook_url', 'with_tip'])
def test_rule_invalid(method):
    with pytest.raises(ValueError):
        rule = Rule()
        fn = getattr(rule, method)
        fn(None)


def test_rule_with_description():
    expected = 'foo'
    rule = Rule().with_description(expected)
    assert rule.options['description'] == expected


def test_rule_with_severity():
    expected = Severity.Critical
    rule = Rule().with_severity(expected)
    assert rule.options['severity'] == expected.value


def test_rule_is_disabled_default():
    assert Rule().is_disabled().options['disabled'] == False


def test_rule_is_disabled():
    assert Rule().is_disabled(disabled=True).options['disabled'] == True


def test_rule_with_notifications_single():
    expected = EmailNotification('foo@bar.com')
    rule = Rule().with_notifications(expected)
    assert rule.options['notifications'] == [expected.options]


def test_rule_with_notifiations_multi():
    expected = [EmailNotification('foo@bar.com'),
                TeamNotification('lol')]
    rule = Rule().with_notifications(*expected)

    for n in rule.options['notifications']:
        assert n in map(lambda x: x.options, expected)


def mk_rule_fn(rule, name):
    """Test helper for converting camelCase names to
       underscore_function_names and returning a callable rule fn."""

    parts = re.sub('(?!^)([A-Z][a-z]+)', r' \1', name).split()
    parts.insert(0, 'with')
    fn_name = '_'.join(map(lambda x: x.lower(), parts))
    return getattr(rule, fn_name)

@pytest.mark.parametrize('name',
    ['parameterizedBody', 'parameterizedSubject', 'runbookUrl', 'tip'])
def test_rule_stringy_things(name):
    expected = 'foo'
    rule = Rule()
    fn = mk_rule_fn(rule, name)
    assert fn('foo').options[name] == expected
