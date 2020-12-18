"""pytest-localstack constants."""

import botocore

from pytest_localstack import utils

# IP for localhost
LOCALHOST = "127.0.0.1"

# The default AWS region.
DEFAULT_AWS_REGION = "us-east-1"

# The default AWS access key.
DEFAULT_AWS_ACCESS_KEY_ID = "accesskey"

# The default AWS secret access key.
DEFAULT_AWS_SECRET_ACCESS_KEY = "secretkey"

# The default AWS session token.
DEFAULT_AWS_SESSION_TOKEN = "token"

DEFAULT_CONTAINER_START_TIMEOUT = 60
DEFAULT_CONTAINER_STOP_TIMEOUT = 10

BOTOCORE_VERSION = utils.get_version_tuple(botocore.__version__)
