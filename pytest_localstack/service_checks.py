"""Checks to see if Localstack service is running.

Each check takes a :class:`.LocalstackSession` and
raises :class:`~pytest_localstack.exceptions.ServiceError`
if the service is not available.
"""
import contextlib
import functools
import socket
import urllib.parse

import botocore.config

from pytest_localstack import constants, exceptions


def is_port_open(port_or_url, timeout=1):
    """Check if TCP port is open."""
    if isinstance(port_or_url, (str, bytes)):
        url = urllib.parse.urlparse(port_or_url)
        port = url.port
        host = url.hostname
    else:
        port = port_or_url
        host = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with contextlib.closing(sock):
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0


def port_check(service_name):
    """Check that a service port is open."""

    def _check(localstack_session):
        url = localstack_session.endpoint_url(service_name)
        if not is_port_open(url):
            raise exceptions.ServiceError(service_name=service_name)

    return _check


def botocore_check(service_name, client_func_name):
    """Decorator to check service via botocore Client.

    `client_func_name` should be the name of a harmless client
    method to call that has no required arguements.
    `list_*` methods are usually good candidates.
    """

    def _decorator(check_results_func):
        @functools.wraps(check_results_func)
        def _wrapped(localstack_session):
            url = localstack_session.endpoint_url(service_name)
            if not is_port_open(url):
                raise exceptions.ServiceError(service_name=service_name)
            config_kwargs = {
                "connect_timeout": 1,
                "read_timeout": 1,
                "s3": {"addressing_style": "path"},
            }
            if constants.BOTOCORE_VERSION >= (1, 6, 0):
                config_kwargs["retries"] = {"max_attempts": 1}
            client = localstack_session.botocore.client(
                service_name,
                # Handle retries at a higher level
                config=botocore.config.Config(**config_kwargs),
            )
            client_func = getattr(client, client_func_name)
            try:
                response = client_func()
                check_results_func(response)
            except Exception as e:
                raise exceptions.ServiceError(service_name=service_name) from e

        return _wrapped

    return _decorator


def botocore_check_response_type(
    service_name, client_func_name, expected_type, *response_keys
):
    """Generate a service check function that tests that the response is a specific type.

    Optionally pass response_keys to check the type of something nested in a
    response dict.
    """

    @botocore_check(service_name, client_func_name)
    def _f(client_response):
        for key in response_keys:
            client_response = client_response[key]
        assert isinstance(client_response, expected_type)

    return _f
