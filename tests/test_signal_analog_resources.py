import pytest
import requests_mock
from requests.exceptions import HTTPError
import betamax
from betamax_serializers import pretty_json
import requests

from signal_analog.resources import Resource, __SIGNALFX_API_ENDPOINT__
from signal_analog.dashboards import Dashboard
import signal_analog.util as util
import json

# Global config. This will store all recorded requests in the 'mocks' dir
with betamax.Betamax.configure() as config:
    betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.cassette_library_dir = 'tests/mocks'

# Don't get in the habit of doing this, but it simplifies testing
global_session = requests.Session()
global_recorder = betamax.Betamax(global_session)

bad_str_inputs = [None, ""]


@pytest.mark.parametrize("expected", bad_str_inputs)
def test_resource_init_empty_opts_args(expected):
        with pytest.raises(ValueError):
                Resource(base_url=expected)
                Resource(endpoint=expected)
                Resource(api_token=expected)
                Resource().with_api_token(expected)


@pytest.mark.parametrize("input,expected",
                         [(None, __SIGNALFX_API_ENDPOINT__), ("foo", "foo")])
def test_resource_init_base_url(input, expected):
        if input is None:
                resource = Resource()
        else:
                resource = Resource(input)

        assert resource.base_url == expected


@pytest.mark.parametrize("input,expected", [(None, '/'), ('/foo', '/foo')])
def test_resource_init_endpoint(input, expected):
        # TODO would be interesting to validate endpoints always start with '/'
        if input is None:
                resource = Resource()
        else:
                resource = Resource(endpoint=input)

        assert resource.endpoint == expected


def test_resource_init_api_token():
        expected = "foo"
        resource = Resource(api_token=expected)
        assert resource.api_token == expected


def test_is_valid_without_message():
        with pytest.raises(ValueError) as error:
                util.is_valid(None, error_message=None)
                assert error.message is None


def test_resource_with_api_token():
        expected = 'foo'
        resource = Resource().with_api_token(expected)

        assert resource.api_token == expected


def test_resource_create_happy_path():
        with requests_mock.Mocker() as mock:
                expected = {'foo': 'bar'}

                mock.register_uri(
                        'POST', __SIGNALFX_API_ENDPOINT__ + '/', json=expected
                )

                resource = Resource().with_api_token('test')
                resource.options = {'opt': 'val'}

                response = resource.create()
                assert response == expected


def test_resource_create_error():
        with requests_mock.Mocker() as mock:
                mock.register_uri(
                        'POST', __SIGNALFX_API_ENDPOINT__ + '/', status_code=500
                )

                resource = Resource().with_api_token('test')
                resource.options = {'opt': 'val'}

                with pytest.raises(RuntimeError):
                        resource.create()


def test_resource_create_dry_run():
        with requests_mock.Mocker() as mock:
                expected = {'opt': 'val'}

                mock.register_uri(
                        'POST', __SIGNALFX_API_ENDPOINT__ + '/', json=expected
                )

                resource = Resource().with_api_token('test')
                resource.options = expected

                response = resource.create(dry_run=True)

                assert response == expected

def test_find_existing_resources_no_name():
    """Make sure we don't make network requests if we don't have a name."""
    with pytest.raises(ValueError):
        Dashboard().__find_existing_resources__()


def test_find_existing_resources():
    with global_recorder.use_cassette('get_existing_dashboards',
                                      serialize_with='prettyjson'):
        name = 'Riposte Template Dashboard'

        resp = Dashboard(session=global_session)\
            .with_name('Riposte Template Dashboard')\
            .with_api_token('foo')\
            .__find_existing_resources__()

        assert resp['count'] > 0
        for r in resp['results']:
            assert name in r['name']
