import pytest
import requests_mock
from requests.exceptions import HTTPError

from signal_analog.resources import Resource, __SIGNALFX_API_ENDPOINT__
import signal_analog.util as util
import json

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


@pytest.mark.parametrize("api_token,options", [(None, {}), ("foo", {})])
def test_resource_create_failing_preconds(api_token, options):
        with pytest.raises(ValueError):
                resource = Resource()
                resource.api_token = api_token
                resource.options = options

                resource.create()


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

                with pytest.raises(HTTPError):
                        resource.create()


def test_resource_create_dry_run():
        with requests_mock.Mocker() as mock:
                expected = json.dumps({'opt': 'val'})

                mock.register_uri(
                        'POST', __SIGNALFX_API_ENDPOINT__ + '/', json=expected
                )

                resource = Resource().with_api_token('test')
                resource.options = {'opt': 'val'}

                response = resource.create(dry_run=True)

                assert response == expected
