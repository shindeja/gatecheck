import boto3
import botocore
from botocore.config import Config
import logging

logger = logging.getLogger(__name__)

def get_ecs_service(region_name, cluster_name, svc_arns):
    services = []
    client = boto3.client("ecs", config=Config(region_name=region_name))
    try:
        response = client.describe_services(
            cluster = cluster_name,
            services = svc_arns,
            include = ['TAGS']
        )
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return (services)
    services = response.get("services", [])
    return (services)

def get_ecs_task(region_name, cluster_name, task_arns):
    tasks = []
    client = boto3.client("ecs", config=Config(region_name=region_name))
    try:
        response = client.describe_tasks(
            cluster = cluster_name,
            tasks = task_arns,
            include = ['TAGS']
        )
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return (tasks)
    tasks = response.get("tasks", [])
    return (tasks)

def get_ecs_task_definition(region_name, task_def_arn):
    task_definitions = []
    client = boto3.client("ecs", config=Config(region_name=region_name))
    try:
        response = client.describe_task_definition(
            taskDefinition = task_def_arn,
            include = ['TAGS']
        )
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return (task_definitions)
    
    task_definitions = response.get("taskDefinition", {})
    return (task_definitions)

def get_subnet(region_name, subnet_id):
    subnets = []
    client = boto3.client("ec2", config=Config(region_name=region_name))
    try:
        response = client.describe_subnets(
            SubnetIds = [
                subnet_id,
            ]
        )
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return (subnets)
    subnets = response.get("Subnets", [])
    return (subnets)

def get_main_route_table(region_name, vpc_id):
    route_tables = []
    client = boto3.client("ec2", config=Config(region_name=region_name))
    try:
        response = client.describe_route_tables(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id,
                    ]
                },
            ]
        )
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return (route_tables)
    
    route_tables = response.get("RouteTables", [])
    return (route_tables)

def get_route_tables(region_name, subnet_id):
    route_tables = []
    client = boto3.client("ec2", config=Config(region_name=region_name))
    try:
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
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return (route_tables)
    
    route_tables = response.get("RouteTables", [])
    if len(route_tables) == 0:
        return (route_tables)
    return (route_tables)

def get_network_interfaces(region_name, network_interface_ids):
    network_interfaces = []
    client = boto3.client("ec2", config=Config(region_name=region_name))
    try:
        response = client.describe_network_interfaces(
            NetworkInterfaceIds = network_interface_ids
        )
    except botocore.exceptions.ClientError as e:
        logger.error(e)
        return (network_interfaces)
    network_interfaces = response.get("NetworkInterfaces", [])
    return (network_interfaces)
