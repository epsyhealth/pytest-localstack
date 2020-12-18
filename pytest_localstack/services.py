from pytest_localstack.service_checks import port_check, botocore_check_response_type


class Service:
    def __init__(self, name, check, pro=False):
        self.pro = pro
        self.name = name
        self.check = check


SERVICES = { s.name: s for s in [
    Service("apigateway", port_check("apigateway")),
    Service("amplify", botocore_check_response_type("amplify", "list_apps", list, "apps"), True),
    Service("appsync", botocore_check_response_type("appsync", "list_graphql_apis", list, "graphqlApis"), True),
    Service("athena", botocore_check_response_type("athena", "list_data_catalogs", list, "DataCatalogsSummary"), True),
    Service("cloudformation", botocore_check_response_type("cloudformation", "list_stacks", list, "StackSummaries")),
    Service("cloudfront", botocore_check_response_type("cloudfront", "list_distributions", list, "DistributionList"), True),
    Service("cloudtrail", botocore_check_response_type("cloudtrail", "list_trails", list, "Trails"), True),
    Service("cloudwatch", botocore_check_response_type("cloudwatch", "list_dashboards", list, "DashboardEntries")),
    Service("codecommit", botocore_check_response_type("codecommit", "list_repositories", list, "repositories"), True),
    Service("cognito", botocore_check_response_type("cognito-identity", "list_identity_pools", list, "IdentityPools"), True),
    Service("dynamodb", botocore_check_response_type("dynamodb", "list_tables", list, "TableNames")),
    Service("dynamodbstreams", botocore_check_response_type("dynamodbstreams", "list_streams", list, "Streams")),
    Service("ecr", botocore_check_response_type("ecr", "describe_repositories", list, "repositories"), True),
    Service("ecs", botocore_check_response_type("ecs", "list_clusters", list, "clusterArns"), True),
    Service("eks", botocore_check_response_type("eks", "list_clusters", list, "clusters"), True),
    Service("ec2", botocore_check_response_type("ec2", "describe_regions", list, "Regions")),
    Service("elasticache", botocore_check_response_type("elasticache", "describe_cache_clusters", list, "CacheClusters")),
    Service("elb", botocore_check_response_type("elb", "describe_load_balancers", list, "LoadBalancerDescriptions")),
    Service("emr", botocore_check_response_type("emr", "list_clusters", list, "Clusters")),
    Service("events", botocore_check_response_type("events", "list_event_buses", list, "EventBuses")),
    Service("es", botocore_check_response_type("es", "list_domain_names", list, "DomainNames")),
    Service("firehose", botocore_check_response_type("firehose", "list_delivery_streams", list, "DeliveryStreamNames")),
    Service("glacier", botocore_check_response_type("glacier", "list_vaults", list, "VaultList")),
    Service("glue", botocore_check_response_type("glue", "list_crawlers", list, "CrawlerNames")),
    Service("iot", botocore_check_response_type("iot", "list_streams", list, "streams")),
    Service("iam", botocore_check_response_type("iam", "list_roles", list, "Roles")),
    Service("kinesis", botocore_check_response_type("kinesis", "list_streams", list, "StreamNames")),
    Service("kafka", botocore_check_response_type("kafka", "list_clusters", list, "ClusterInfoList")),
    Service("kinesisanalytics", botocore_check_response_type("kinesisanalytics", "list_applications", list, "ApplicationSummaries")),
    Service("kms", botocore_check_response_type("kms", "list_keys", list, "Keys")),
    Service("lambda", botocore_check_response_type("lambda", "list_functions", list, "Functions")),
    Service("mediastore", botocore_check_response_type("mediastore", "list_containers", list, "Containers")),
    Service("organizations", botocore_check_response_type("organizations", "list_accounts", list, "Accounts")),
    Service("logs", botocore_check_response_type("logs", "describe_log_groups", list, "logGroups")),
    Service("redshift", botocore_check_response_type("redshift", "describe_clusters", list, "Clusters")),
    Service("route53", port_check("route53")),
    Service("qldb", botocore_check_response_type("qldb", "list_ledgers", list, "Ledgers")),
    Service("rds", botocore_check_response_type("rds", "describe_db_instances", list, "DBInstances")),
    Service("s3", botocore_check_response_type("s3", "list_buckets", list, "Buckets")),
    Service("secretsmanager", botocore_check_response_type("secretsmanager", "list_secrets", list, "SecretList")),
    Service("ses", botocore_check_response_type("ses", "list_identities", list, "Identities")),
    Service("sns", botocore_check_response_type("sns", "list_topics", list, "Topics")),
    # https://github.com/boto/boto3/issues/1813
    Service("sqs", botocore_check_response_type("sqs", "list_queues", dict)),
    Service("ssm", botocore_check_response_type("ssm", "describe_parameters", list, "Parameters")),
    Service("stepfunctions", botocore_check_response_type("stepfunctions", "list_activities", list, "activities")),
    Service("timestream", botocore_check_response_type("timestream-query", "describe_endpoints", list, "Endpoints")),
    Service("transfer", botocore_check_response_type("transfer", "list_servers", list, "Servers")),
    Service("xray", port_check("xray")),
]}
