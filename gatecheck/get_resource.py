import boto3
from botocore.config import Config
import logging

logger = logging.getLogger(__name__)

def get_ecs_service(region_name, cluster_name, svc_arns):
    services = []
    client = boto3.client("ecs", config=Config(region_name=region_name))
    response = client.describe_services(
        cluster = cluster_name,
        services = svc_arns,
        include = ['TAGS']
    )
    services = response.get("services", [])
    return (services)

def get_ecs_task(region_name, cluster_name, task_arns):
    tasks = []
    client = boto3.client("ecs", config=Config(region_name=region_name))
    response = client.describe_tasks(
        cluster = cluster_name,
        tasks = task_arns,
        include = ['TAGS']
    )
    tasks = response.get("tasks", [])
    return (tasks)

def get_ecs_task_definition(region_name, task_def_arn):
    task_definitions = []
    client = boto3.client("ecs", config=Config(region_name=region_name))
    response = client.describe_task_definition(
        taskDefinition = task_def_arn,
        include = ['TAGS']
    )
    task_definitions = response.get("taskDefinition", {})
    return (task_definitions)

def get_route_tables(region_name, subnet_id):
    route_tables = []
    client = boto3.client("ec2", config=Config(region_name=region_name))
    response = client.describe_route_tables(
        Filters=[
            {
                'Name': 'association.subnet-id',
                'Values': [
                    subnet_id,
                ]
            },
        ]
    )
    route_tables = response.get("RouteTables", [])
    return (route_tables)

def get_network_interfaces(region_name, network_interface_ids):
    network_interfaces = []
    client = boto3.client("ec2", config=Config(region_name=region_name))
    response = client.describe_network_interfaces(
        NetworkInterfaceIds = network_interface_ids
    )
    network_interfaces = response.get("NetworkInterfaces", [])
    return (network_interfaces)
