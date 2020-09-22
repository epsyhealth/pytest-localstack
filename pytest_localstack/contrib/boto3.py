"""pytest-localstack extensions for boto3."""
import logging
import typing

import boto3.resources.base
import boto3.session
import botocore.client

from pytest_localstack import constants, hookspecs

if typing.TYPE_CHECKING:
    import pytest_localstack.session

logger = logging.getLogger(__name__)


@hookspecs.pytest_localstack_hookimpl
def contribute_to_session(session: "pytest_localstack.session.LocalstackSession"):
    """Add :class:`Boto3TestResourceFactory` to :class:`~.LocalstackSession`."""
    logger.debug("patching session %r", session)
    session.boto3 = Boto3TestResourceFactory(session)


class Boto3TestResourceFactory:
    """Create boto3 clients and resources to interact with a :class:`~.LocalstackSession`.

    Args:
        localstack_session (:class:`.LocalstackSession`):
            The session that this factory should create test resources for.

    """

    _default_session: boto3.session.Session

    def __init__(
        self, localstack_session: "pytest_localstack.session.LocalstackSession"
    ) -> None:
        logger.debug("Boto3TestResourceFactory.__init__")
        self.localstack_session = localstack_session
        self._default_session = None

    def session(self, *args, **kwargs) -> boto3.session.Session:
        """Return a boto3 Session object that will use localstack.

        Arguments are the same as :class:`boto3.session.Session`.
        """
        kwargs["botocore_session"] = self.localstack_session.botocore.default_session
        kwargs.setdefault("aws_access_key_id", constants.DEFAULT_AWS_ACCESS_KEY_ID)
        kwargs.setdefault(
            "aws_secret_access_key", constants.DEFAULT_AWS_SECRET_ACCESS_KEY
        )
        kwargs.setdefault("aws_session_token", constants.DEFAULT_AWS_SESSION_TOKEN)
        return boto3.session.Session(*args, **kwargs)

    @property
    def default_session(self) -> boto3.session.Session:
        """Return a default boto3 Localstack Session.

        Most applications only need one Session.
        """
        if self._default_session is None:
            self._default_session = self.session()
        return self._default_session

    def client(self, service_name: str) -> botocore.client.BaseClient:
        """Return a patched boto3 Client object that will use localstack.

        Arguments are the same as :func:`boto3.client`.
        """
        return self.default_session.client(service_name)  # type: ignore

    def resource(self, service_name: str) -> boto3.resources.base.ServiceResource:
        """Return a patched boto3 Resource object that will use localstack.

        Arguments are the same as :func:`boto3.resource`.
        """
        return self.default_session.resource(service_name)  # type: ignore

    # No need for a patch method.
    # Running the botocore patch will also patch boto3.
