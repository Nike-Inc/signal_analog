"""Tests pertaining to the `signal_analog.detectors` module."""

import re
import pytest
import requests
import time

from email_validator import EmailNotValidError
from signal_analog.combinators import Div, GT, LT
from signal_analog.flow import Assign, Data, Detect, Program, Ref, When
from signal_analog.charts import TimeSeriesChart
from signal_analog.detectors import EmailNotification, PagerDutyNotification, \
                                    BigPandaNotification, \
                                    SlackNotification, HipChatNotification, \
                                    ServiceNowNotification, \
                                    VictorOpsNotification, \
                                    AmazonEventBridgeNotification, \
                                    WebhookNotification, TeamNotification, \
                                    TeamEmailNotification, Rule, Severity, \
                                    Time, TimeConfig, VisualizationOptions, \
                                    Detector


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


def test_bp_valid():
    bp_id = 'foo'
    n = BigPandaNotification(bp_id)
    assert n.options['type'] == 'BigPanda'
    assert n.options['credentialId'] == bp_id


def test_bp_invalid():
    with pytest.raises(ValueError):
        BigPandaNotification('')


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


def test_amazoneventbridge_valid():
    aeb_id = 'foo'
    n = AmazonEventBridgeNotification(aeb_id)

    assert n.options['type'] == 'AmazonEventBridge'
    assert n.options['credentialId'] == aeb_id


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
                         ['for_label', 'with_description', 'with_severity',
                          'with_notifications', 'with_parameterized_body',
                          'with_parameterized_subject', 'with_runbook_url',
                          'with_tip'])
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
    assert Rule().is_disabled().options['disabled'] is False


def test_rule_is_disabled():
    assert Rule().is_disabled(disabled=True).options['disabled'] is True


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
                         ['parameterizedBody', 'parameterizedSubject',
                          'runbookUrl', 'tip'])
def test_rule_stringy_things(name):
    expected = 'foo'
    rule = Rule()
    fn = mk_rule_fn(rule, name)
    assert fn('foo').options[name] == expected


def test_time_config_init():
    assert TimeConfig().options == {}


def test_time_config_with_type():
    expected = Time.Relative
    config = TimeConfig().with_type(expected)
    assert config.options['type'] == expected.value


def test_time_config_with_type_invalid():
    with pytest.raises(ValueError):
        TimeConfig().with_type('lol')


def test_time_config_add_millis():
    expected = 100
    config = TimeConfig().__add_millis__(expected, 'foo')
    assert config.options['foo'] == expected


def test_time_config_start_relative():
    with pytest.raises(ValueError):
        TimeConfig().with_type(Time.Relative).with_start(100)


def test_time_config_end_relative():
    with pytest.raises(ValueError):
        TimeConfig().with_type(Time.Relative).with_end(100)


def test_time_config_range_absolute():
    with pytest.raises(ValueError):
        TimeConfig().with_type(Time.Absolute).with_range(100)


def test_time_config_absolute():
    e_start = 100
    e_end = 200

    config = TimeConfig().with_start(e_start).with_end(e_end)
    assert config.options['start'] == e_start
    assert config.options['end'] == e_end

    conf = TimeConfig().with_type(Time.Absolute)\
        .with_start(e_start).with_end(e_end)
    assert conf.options['start'] == e_start
    assert conf.options['end'] == e_end


def test_time_config_relative():
    expected = 100

    config = TimeConfig().with_range(expected)
    assert config.options['range'] == expected

    conf = TimeConfig().with_type(Time.Relative).with_range(expected)
    assert conf.options['range'] == expected


def test_vis_opts_init():
    assert VisualizationOptions().options == {}


def test_vis_opts_time_config_invalid():
    with pytest.raises(ValueError):
        VisualizationOptions().with_time_config(None)


def test_vis_opts_time_config():
    conf = TimeConfig().with_type(Time.Relative).with_range(100)
    opts = VisualizationOptions().with_time_config(conf)

    assert opts.options['time'] == conf.options


def test_show_data_markers_default():
    assert VisualizationOptions()\
        .show_data_markers().options['showDataMarkers'] is False


def test_show_data_markers():
    assert VisualizationOptions().show_data_markers(show_markers=True)\
        .options['showDataMarkers'] is True


def test_detector_init():
    assert Detector().options == {}
    assert Detector().endpoint == '/detector'


def test_detector_with_rules():
    rule = Rule().with_notifications(EmailNotification('foo@bar.com'))
    d = Detector().with_rules(rule)
    assert d.options['rules'] == [rule.options]


def test_detector_with_program():
    program = Program(
        Data('foo').publish(label='A'),
        Data('bar').publish(label='B')
    )
    d = Detector().with_program(program)
    assert d.options['programText'] == str(program)


def test_detector_with_max_dely():
    d = Detector().with_max_delay(900)
    assert d.options['maxDelay'] == 900


def test_detector_with_visualization_options():
    opts = VisualizationOptions()\
        .with_time_config(TimeConfig().with_type(Time.Absolute))
    d = Detector().with_visualization_options(opts)
    assert d.options['visualizationOptions'] == opts.options


def test_detector_with_tags():
    tags = ['foo', 'bar', 'baz']
    d = Detector().with_tags(*tags)
    assert d.options['tags'] == tags


def test_detector_with_teams():
    team_ids = ['team1', 'team2', 'team3']
    d = Detector().with_teams(*team_ids)
    assert d.options['teams'] == team_ids


@pytest.mark.parametrize('method',
                         ['with_program', 'with_visualization_options'])
def test_detector_invalid(method):
    with pytest.raises(ValueError):
        detector = Detector()
        fn = getattr(detector, method)
        fn(None)


def test_detector_from_chart():
    program = Program(Data('cpu.utilization').publish(label='Z'))
    chart = TimeSeriesChart().with_program(program)

    def helper(p):
        return Program(Detect(LT(p.find_label('Z'), 10)).publish(label='foo'))

    detector = Detector().from_chart(chart, helper)
    assert detector.options['programText'] == str(helper(program))


def test_detector_from_chart_mod_prog():
    """We shouldn't be able to muck about with programs from charts."""
    program = Program(Data('disk.utilization').publish(label='X'))
    prog_size = len(program.statements)
    chart = TimeSeriesChart().with_program(program)

    def bad_helper(p):
        p.add_statements(Data("I shouldn't exist").publish(label='Y'))
        return Program(Detect(LT(p.find_label('Z'), 10)).publish(label='foo'))

    Detector().from_chart(chart, bad_helper)

    # bad_helper should not be allowed to add new program statements to
    # the originating chart's program.
    assert prog_size == len(program.statements)


def test_detector_from_chart_not_program():
    """We should throw an error if we receive a chart that doesn't have a
       proper program.
    """
    program = Data('awesome.metrics').publish(label='A')
    chart = TimeSeriesChart().with_program(program)

    with pytest.raises(ValueError):
        Detector().from_chart(chart, lambda x: x)


def test_detector_with_assign_combinator():
    """ We should correctly generate a detector comprised of two assignment
        functions
    """
    cpu_util_string = 'cpu.utilization'
    sum_string = 'utilization_sum'
    count_string = 'utilization_count'
    mean_string = 'utilization_mean'

    sum_data = Data(cpu_util_string).sum()
    count_data = Data(cpu_util_string).count()

    utilization_sum = Assign(sum_string, sum_data)
    utilization_count = Assign(count_string, count_data)

    mean_data = Div(Ref(sum_string), Ref(count_string))

    utilization_mean = Assign(mean_string, mean_data)

    detect = Detect(When(GT(Ref(mean_string), 50))).publish(label='detector')

    program = Program(
        utilization_sum,
        utilization_count,
        utilization_mean,
        detect
    )

    detector = Detector().with_program(program)

    assert detector.options["programText"] == "{0}\n{1}\n{2}\n{3}".format(
        str(utilization_sum),
        str(utilization_count),
        str(utilization_mean),
        str(detect)
    )

    assert program.statements.pop() == detect
    assert program.statements.pop() == utilization_mean
    assert program.statements.pop() == utilization_count
    assert program.statements.pop() == utilization_sum


def test_detector_update(sfx_recorder, session):

    api_token = 'foo'
    label = 'foo'

    def program(threshold):
        return Program(
            Detect(GT(Data('cpu.utilization'), threshold)).publish(label=label)
        )

    rule = Rule()\
        .for_label(label)\
        .with_severity(Severity.Major)\
        .with_notifications(EmailNotification('foo.bar@example.com'))

    # Assert that we can actually update values within a detector
    with sfx_recorder.use_cassette('detector_update_success',
                                      serialize_with='prettyjson'):


        def detector(threshold):
            return Detector(session=session)\
                .with_name('test_update')\
            .with_program(program(threshold))\
            .with_rules(rule)

        create_response = detector(90).with_api_token(api_token).create()
        time.sleep(3)
        update_response = detector(99).with_api_token(api_token).update()

        # These assertions should fail
        assert '90' in create_response['programText']
        assert '99' in update_response['programText']
        assert create_response['id'] == update_response['id']


def test_detector_delete_not_found(sfx_recorder, api_token, detector):

    with sfx_recorder.use_cassette('detector_delete_success',
                                   serialize_with='prettyjson'):

        haskell_curry = detector('francisco_friar', 9001).with_api_token(api_token)
        tim_curry_lol = detector('francisco_friar', 9001).with_api_token(api_token)

        create_response = haskell_curry.create()
        time.sleep(3)
        delete_response = haskell_curry.delete()
        time.sleep(3)
        # TODO something should happen here, empty response I think
        second_delete_response = tim_curry_lol.delete()

        assert '9001' in create_response['programText']
        assert delete_response is None
        assert second_delete_response is None
