"""Run and interact with a Localstack container."""
import logging
import os
import string
import time
from copy import copy

from packaging import version

from pytest_localstack import (
    constants,
    container,
    exceptions,
    plugin,
    service_checks,
    utils,
)
from pytest_localstack.exceptions import UnsupportedLocalstackVersion
from pytest_localstack.services import SERVICES

logger = logging.getLogger(__name__)


class RunningSession:
    """Connects to an already running localstack server"""

    def __init__(
        self,
        hostname,
        services=None,
        region_name=None,
        use_ssl=False,
        localstack_version="latest",
        **kwargs
    ):

        self.kwargs = kwargs
        self.use_ssl = use_ssl
        self.region_name = region_name
        self._hostname = hostname
        self.localstack_version = localstack_version

        if self.localstack_version != "latest" and utils.get_version_tuple(
            localstack_version
        ) < utils.get_version_tuple("0.11"):
            raise UnsupportedLocalstackVersion()

        plugin.manager.hook.contribute_to_session(session=self)
        # If no region was provided, use what botocore defaulted to.
        if not region_name:
            self.region_name = (
                self.botocore.session().get_config_variable("region")
                or constants.DEFAULT_AWS_REGION
            )

        if services is None:
            self.services = SERVICES.keys()
        elif isinstance(services, (list, tuple, set)):
            for service_name in services:
                if service_name not in SERVICES:
                    raise exceptions.ServiceError("unknown service " + service_name)

            self.services = list(services)
        else:
            raise TypeError("unsupported services type: %r" % (services,))

    @property
    def hostname(self):
        """Return hostname of Localstack."""
        return self._hostname

    @property
    def service_aliases(self):
        """Return a full list of possible names supported."""
        return set(self.services)

    def start(self, timeout=60):
        """Starts Localstack if needed."""
        plugin.manager.hook.session_starting(session=self)

        self._check_services(timeout)
        plugin.manager.hook.session_started(session=self)

    def _check_services(self, timeout, initial_retry_delay=0.01, max_delay=1):
        """Check that all Localstack services are running and accessible.

        Does exponential backoff up to `max_delay`.

        Args:
            timeout (float): Number of seconds to wait for services to
                be available.
            initial_retry_delay (float, optional): Initial retry delay value
                in seconds. Will be multiplied by `2^n` for each retry.
                Default: 0.01
            max_delay (float, optional): Max time in seconds to wait between
                checking service availability. Default: 1

        Returns:
            None

        Raises:
            pytest_localstack.exceptions.TimeoutError: If not all services
                started before `timeout` was reached.

        """
        services = set(self.services)
        num_retries = 0
        start_time = time.time()
        while services and (time.time() - start_time) < timeout:
            for service_name in list(
                services
            ):  # list() because set may change during iteration
                try:
                    SERVICES[service_name].check(self)
                    services.discard(service_name)
                except exceptions.ServiceError as e:
                    if (time.time() - start_time) >= timeout:
                        raise exceptions.TimeoutError(
                            "Localstack service not started: {0}".format(service_name)
                        ) from e
            if services:
                delay = (2 ** num_retries) * initial_retry_delay
                if delay > max_delay:
                    delay = max_delay
                    time.sleep(delay)
                    num_retries += 1

    def stop(self, timeout=10):
        """Stops Localstack."""
        plugin.manager.hook.session_stopping(session=self)
        plugin.manager.hook.session_stopped(session=self)

    def __enter__(
        self,
        start_timeout=constants.DEFAULT_CONTAINER_START_TIMEOUT,
        stop_timeout=constants.DEFAULT_CONTAINER_STOP_TIMEOUT,
    ):
        self.__stop_timeout = stop_timeout
        self.start(timeout=start_timeout)
        return self

    def __exit__(self, exc_type, exc, tb):
        timeout = getattr(
            self, "__stop_timeout", constants.DEFAULT_CONTAINER_STOP_TIMEOUT
        )
        self.stop(timeout=timeout)

    def map_port(self, port):
        """Return host port based on Localstack port."""
        return port

    def service_hostname(self, service_name):
        """Get hostname and port for an AWS service."""
        port = self.map_port(4566)

        return "%s:%i" % (self.hostname, port)

    def endpoint_url(self, service_name):
        """Get the URL for a service endpoint."""
        url = ("https" if self.use_ssl else "http") + "://"
        url += self.service_hostname(service_name)
        return url


class LocalstackSession(RunningSession):
    """Run a localstack Docker container.

    This class can start and stop a Localstack container, as well as capture
    its logs. It also implments a plugin system to add factories
    for the various AWS client libraries (botocore, boto3, etc).

    Can be used as a context manager:

        >>> import docker
        >>> client = docker.from_env()
        >>> with LocalstackSession(client) as session:
        ...     s3 = session.boto3.resource('s3')

    Args:
        docker_client: A docker-py Client object that will be used
            to talk to Docker.
        services (list|dict, optional): One of

            - A list of AWS service names to start in the
              Localstack container.
            - A dict of service names to the port they should run on.

            Defaults to all services. Setting this
            can reduce container startup time and therefore test time.
        region_name (str, optional): Region name to assume.
            Each Localstack container acts like a single AWS region.
            Defaults to 'us-east-1'.
        kinesis_error_probability (float, optional): Decimal value between
            0.0 (default) and 1.0 to randomly inject
            ProvisionedThroughputExceededException errors
            into Kinesis API responses.
        dynamodb_error_probability (float, optional):  Decimal value
            between 0.0 (default) and 1.0 to randomly inject
            ProvisionedThroughputExceededException errors into
            DynamoDB API responses.
        container_log_level (int, optional): The logging level to use
            for Localstack container logs. Defaults to :attr:`logging.DEBUG`.
        localstack_version (str, optional): The version of the Localstack
            image to use. Defaults to `latest`.
        auto_remove (bool, optional): If True, delete the Localstack
            container when it stops.
        container_name (str, optional): The name for the Localstack
            container. Defaults to a randomly generated id.
        use_ssl (bool, optional): If True use SSL to connect to Localstack.
            Default is False.
        **kwargs: Additional kwargs will be stored in a `kwargs` attribute
            in case test resource factories want to access them.

    """

    image_name = "localstack/localstack"
    factories = []

    def __init__(
        self,
        docker_client,
        services=None,
        region_name=None,
        kinesis_error_probability=0.0,
        dynamodb_error_probability=0.0,
        container_log_level=logging.DEBUG,
        localstack_version="latest",
        auto_remove=True,
        pull_image=True,
        container_name=None,
        use_ssl=False,
        localstack_api_key=None,
        **kwargs
    ):
        self._container = None
        self._factory_cache = {}

        self.docker_client = docker_client
        self.region_name = region_name
        self.kinesis_error_probability = kinesis_error_probability
        self.dynamodb_error_probability = dynamodb_error_probability
        self.auto_remove = bool(auto_remove)
        self.pull_image = bool(pull_image)

        super(LocalstackSession, self).__init__(
            hostname=constants.LOCALHOST,
            services=services,
            region_name=region_name,
            use_ssl=use_ssl,
            localstack_version=localstack_version,
            **kwargs
        )

        self.container_log_level = container_log_level
        self.localstack_version = localstack_version
        self.container_name = container_name or generate_container_name()
        self.localstack_api_key = localstack_api_key

    def start(self, timeout=60):
        """Start the Localstack container.

        Args:
            timeout (float, optional): Wait at most this many seconds
                for the Localstack services to start. Default is 1 minute.

        Raises:
            pytest_localstack.exceptions.TimeoutError:
                If *timeout* was reached before all Localstack
                services were available.
            docker.errors.APIError: If the Docker daemon returns an error.

        """
        if self._container is not None:
            raise exceptions.ContainerAlreadyStartedError(self)

        logger.debug("Starting Localstack container %s", self.container_name)
        logger.debug("%r running starting hooks", self)
        plugin.manager.hook.session_starting(session=self)

        image_name = self.image_name + ":" + self.localstack_version
        if self.pull_image:
            logger.debug("Pulling docker image %r", image_name)
            self.docker_client.images.pull(image_name)

        start_time = time.time()

        services = ",".join(self.services)
        kinesis_error_probability = "%f" % self.kinesis_error_probability
        dynamodb_error_probability = "%f" % self.dynamodb_error_probability
        use_ssl = str(self.use_ssl).lower()

        print(services)

        environment = {
            "DEFAULT_REGION": self.region_name,
            "SERVICES": services,
            "KINESIS_ERROR_PROBABILITY": kinesis_error_probability,
            "DYNAMODB_ERROR_PROBABILITY": dynamodb_error_probability,
            "USE_SSL": use_ssl,
        }

        if self.localstack_api_key:
            environment["LOCALSTACK_API_KEY"] = self.localstack_api_key



        logger.info("Starting localstack container")
        self._container = self.docker_client.containers.run(
            image_name,
            name=self.container_name,
            detach=True,
            auto_remove=self.auto_remove,
            environment=environment,
            ports={4566: None},
        )
        logger.debug(
            "Started Localstack container %s (id: %s)",
            self.container_name,
            self._container.short_id,
        )

        # Tail container logs
        container_logger = logger.getChild("containers.%s" % self._container.short_id)
        self._stdout_tailer = container.DockerLogTailer(
            self._container,
            container_logger.getChild("stdout"),
            self.container_log_level,
            stdout=True,
            stderr=False,
        )
        self._stdout_tailer.start()
        self._stderr_tailer = container.DockerLogTailer(
            self._container,
            container_logger.getChild("stderr"),
            self.container_log_level,
            stdout=False,
            stderr=True,
        )
        self._stderr_tailer.start()

        try:
            timeout_remaining = timeout - (time.time() - start_time)
            if timeout_remaining <= 0:
                raise exceptions.TimeoutError("Container took too long to start.")

            self._check_services(timeout_remaining)

            logger.debug("%r running started hooks", self)
            plugin.manager.hook.session_started(session=self)
            logger.debug("%r finished started hooks", self)
        except exceptions.TimeoutError:
            if self._container is not None:
                self.stop(0.1)
            raise

    def stop(self, timeout=10):
        """Stop the Localstack container.

        Args:
            timeout (float, optional): Timeout in seconds to wait for the
                container to stop before sending a SIGKILL. Default: 10

        Raises:
            docker.errors.APIError: If the Docker daemon returns an error.

        """
        if self._container is not None:
            logger.debug("Stopping %r", self)
            logger.debug("Running stopping hooks for %r", self)
            plugin.manager.hook.session_stopping(session=self)
            logger.debug("Finished stopping hooks for %r", self)
            self._container.stop(timeout=10)
            self._container = None
            self._stdout_tailer = None
            self._stderr_tailer = None
            logger.debug("Stopped %r", self)
            logger.debug("Running stopped hooks for %r", self)
            plugin.manager.hook.session_stopped(session=self)
            logger.debug("Finished stopped hooks for %r", self)

    def __del__(self):
        """Stop container on garbage collection."""
        self.stop(0.1)

    def map_port(self, port):
        """Return host port based on Localstack container port."""
        if self._container is None:
            raise exceptions.ContainerNotStartedError(self)
        result = self.docker_client.api.port(self._container.id, int(port))
        if not result:
            return None
        return int(result[0]["HostPort"])


def generate_container_name():
    """Generate a random name for a Localstack container."""
    valid_chars = set(string.ascii_letters)
    chars = []
    while len(chars) < 6:
        new_chars = [chr(c) for c in os.urandom(6 - len(chars))]
        chars += [c for c in new_chars if c in valid_chars]
    return "pytest-localstack-" + "".join(chars)
