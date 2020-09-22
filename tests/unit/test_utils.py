"""Unit tests for pytest_localstack.utils."""
import os
from typing import Optional

import pytest
from hypothesis import assume, given, settings, strategies as st

from pytest_localstack import utils


def _get_env_var(name: str) -> Optional[str]:
    return os.environ.get(name) or os.environ.get(name.upper(), "")


def _set_env_var(name: str, value: Optional[str]):
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


@given(
    http_proxy=st.sampled_from([None, "http://proxy:3128"]),
    https_proxy=st.sampled_from([None, "http://proxy:3128"]),
    HTTP_PROXY=st.sampled_from([None, "http://proxy:3128"]),
    HTTPS_PROXY=st.sampled_from([None, "http://proxy:3128"]),
    no_proxy=st.sampled_from([None, "localhost,127.0.0.1", "localhost", "foobar"]),
    NO_PROXY=st.sampled_from([None, "localhost,127.0.0.1", "localhost", "foobar"]),
)
@settings(deadline=1000)
def test_check_proxy_env_vars(
    http_proxy: Optional[str],
    https_proxy: Optional[str],
    HTTP_PROXY: Optional[str],
    HTTPS_PROXY: Optional[str],
    no_proxy,
    NO_PROXY: Optional[str],
):
    """Test pytest_localstack.utils.check_proxy_env_vars."""
    with utils.mock.patch.dict(os.environ):
        # mock.patch.dict can't delete keys.
        # Patch os.environ manually.
        _set_env_var("http_proxy", http_proxy)
        _set_env_var("https_proxy", https_proxy)
        _set_env_var("HTTP_PROXY", HTTP_PROXY)
        _set_env_var("HTTPS_PROXY", HTTPS_PROXY)
        _set_env_var("no_proxy", no_proxy)
        _set_env_var("NO_PROXY", NO_PROXY)

        settings_match = (
            ((http_proxy or HTTP_PROXY) == (HTTP_PROXY or http_proxy))
            and ((https_proxy or HTTPS_PROXY) == (HTTPS_PROXY or https_proxy))
            and ((no_proxy or NO_PROXY) == (NO_PROXY or no_proxy))
        )
        has_http_proxy = bool(_get_env_var("http_proxy"))
        has_https_proxy = bool(_get_env_var("https_proxy"))
        good_no_proxy = "127.0.0.1" in (_get_env_var("no_proxy") or "")

        if (has_http_proxy or has_https_proxy) and not (
            settings_match and good_no_proxy
        ):
            with pytest.raises(UserWarning):
                utils.check_proxy_env_vars()
        else:
            utils.check_proxy_env_vars()


@given(
    string=st.text(),
    newline=st.sampled_from(["\n", "\r\n", "\r", "\n\r"]),
    num_newlines=st.integers(min_value=0, max_value=100),
    n=st.integers(min_value=-100, max_value=100),
)
def test_remove_newline(string: str, newline: str, num_newlines: int, n: int):
    assume(not (string.endswith("\n") or string.endswith("\r")))
    string_with_newlines = string + (newline * num_newlines)
    result = utils.remove_newline(string_with_newlines, n)
    assert result == string + (newline * (num_newlines - max(n, 0)))


def test_get_version_tuple():
    assert utils.get_version_tuple("1.2.3") == (1, 2, 3)
    with pytest.raises(ValueError):
        utils.get_version_tuple("latest")
