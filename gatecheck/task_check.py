import get_resource
from action import handle_webhook_alert
from policy import PolicyCheck
import logging

logger = logging.getLogger(__name__)


def handle_task_termination(task, task_definition_arn, policy_violations):
    return


##############################################################
# Functions to get task subnet(s) and subnet type
##############################################################

def get_subnet_type(region_name, subnet_id):
    subnet_type = "private"
    route_tables = get_resource.get_route_tables(region_name, subnet_id)
    if len(route_tables) <= 0:
        # then the subnet is implicitly associated to VPC main route table
        subnet_detail = get_resource.get_subnet(region_name, subnet_id)
        if len(subnet_detail) <= 0:
            logger.info("No subnet found for subnet {} in region {}. Skipping".format(subnet_id, region_name))
            return subnet_type
        
        vpc_id = subnet_detail[0].get('VpcId', '')
        if len(vpc_id) <= 0:
            logger.info("No VPC found for subnet {} in region {}. Skipping".format(subnet_id, region_name))
            return subnet_type
        route_tables = get_resource.get_main_route_table(region_name, vpc_id)
    
    if len(route_tables) <= 0:
        logger.info("No route table found for subnet {} in region {}. Skipping".format(subnet_id, region_name))
        return subnet_type
    
    for route_table in route_tables:
        routes = route_table.get('Routes', [])
        if len(routes) <= 0:
            continue
        for route in routes:
            gateway_id = route.get('GatewayId', '')
            if gateway_id.startswith('igw-'):
                subnet_type = "public"
                return subnet_type
            
    return subnet_type

def task_get_subnets(task):
    subnets = []
    attachments = task.get('attachments', [])
    if len(attachments) <= 0:
        return subnets
    for attachment in attachments:
        if attachment.get('type') == 'ElasticNetworkInterface':
            details = attachment.get('details', [])
            for d in details:
                if d.get('name') == 'subnetId':
                     subnets.append(d.get('value'))
    return subnets

def get_subnet_violations(region_name, task, allowed_values):
    policy_violations = []
    subnets = task_get_subnets(task)
    for subnet in subnets:
        subnet_type = get_subnet_type(region_name, subnet)
        pc = PolicyCheck("subnet", subnet_type, allowed_values, "exact", subnet)
        if not pc.check():
            policy_violations.append(pc)
    return policy_violations
    
##############################################################
# Get task network interface 
# and check for public IP association
##############################################################

def has_public_ip(region_name, network_interface):
    network_interface_list = get_resource.get_network_interfaces(region_name, [network_interface])
    if len(network_interface_list) <= 0:
        logger.info("No network interface found for network interface {} in region {}".format(network_interface, region_name))
        return False
    association = network_interface_list[0].get('Association', {})
    public_ip = association.get('PublicIp', "")
    return (len(public_ip) > 0)

def task_get_network_interface(task):
    network_interface = ""
    attachments = task.get('attachments', [])
    if len(attachments) <= 0:
        return network_interface
    for attachment in attachments:
        if attachment.get('type') == 'ElasticNetworkInterface':
            details = attachment.get('details', [])
            for d in details:
                if d.get('name') == 'networkInterfaceId':
                     network_interface = d.get('value')
    return network_interface

def get_ip_violations(region_name, task, allowed_values):
    policy_violations = []
    network_interface = task_get_network_interface(task)
    if len(network_interface) <= 0:
        logger.info("No network interface found for task in region {}".format(region_name))
        return policy_violations
    ip_type = "public" if has_public_ip(region_name, network_interface) else "private"
    pc = PolicyCheck("ip", ip_type, allowed_values, "exact", network_interface)
    if not pc.check():
        policy_violations.append(pc)
    return policy_violations

##############################################################
# Image compliance check
##############################################################
def task_get_images(task):
    images = []
    containers = task.get('containers', [])
    for c in containers:
        image = c.get('image', '')
        images.append(image)

    return images

def get_image_violations(task, allowed_values, check_type):
    policy_violations = []
    images = task_get_images(task)
    for image in images:
        pc = PolicyCheck("image", image, allowed_values, check_type, image)
        if not pc.check():
            policy_violations.append(pc)
    return policy_violations

##############################################################
# Generic task attribute check
##############################################################
def get_task_attribute_violations(task, attribute, allowed_values, check_type):
    policy_violations = []
    attribute_value = task.get(attribute)
    if attribute_value is None: 
        logger.info("Can't find attribute {} in task. Skipping policy check".format(attribute))
        return policy_violations
    pc  = PolicyCheck(attribute, attribute_value, allowed_values, check_type, "task")
    if not pc.check():
        policy_violations.append(pc)
    return policy_violations

##############################################################
# Main enforce task policy function
# Gathers all the policy violations
# if policy is violated and action is to terminate the task
# then the task will be terminated and no more evaluation will be done
# if policy is violated and action is to send a notification
# then all violations are compiled and sent to the webhook
# all violations are logged until a terminate violation is found
##############################################################
def enforce_task_policy(region_name, policy, task, task_definition):
    task_arn = task.get('taskArn', '')
    task_definition_arn = task_definition.get('taskDefinitionArn', '')
    alert_violations = []
    terminate_violations = []
    logger.info("Enforcing task policy for task {} and task definition {}".format(task_arn, task_definition_arn))
    
    for p in policy:
        attribute = p.get('attribute', '')
        allowed_values = p.get('allowed_values', [])
        check_type = p.get('type', 'exact')
        action = p.get('action', '') 
        policy_violations = []
        match attribute:
            case "subnet":
                if "private" in allowed_values and "public" in allowed_values:
                    logger.info("Both private and public subnets are allowed. Skipping subnet policy check")
                    continue
                policy_violations = get_subnet_violations(region_name, task, allowed_values)
                             
            case "ip":
                if "private" in allowed_values and "public" in allowed_values:
                    logger.info("Both private and public IPs are allowed. Skipping IP policy check")
                    continue
                policy_violations = get_ip_violations(region_name, task, allowed_values)
            
            case "image":
                policy_violations = get_image_violations(task, allowed_values, check_type)
            
            case _:
                policy_violations = get_task_attribute_violations(task, attribute, allowed_values, check_type)
        
        if len(policy_violations) <= 0: continue
        # log the violations
        for pv in policy_violations:
            logger.warning("Found policy violation. {}".format(pv))
        if action == "alert":
            alert_violations += policy_violations
            continue
        if action == "terminate":
            terminate_violations += policy_violations
            break
    
    # send all the alert violations + terminate violations
    alert_violations += terminate_violations
    if len(alert_violations) > 0:
        handle_webhook_alert([task_arn, task_definition_arn], alert_violations)
    if len(terminate_violations) > 0:
        handle_task_termination(task, task_definition_arn, terminate_violations)
    return



##############################################################
# Wrapper for task policy handling 
# gets the task and task definition
# invokes enforce policy
##############################################################

def task_policy_handler(event_detail, policy):
    
    key_attributes = ["clusterArn", "taskArn", "taskDefinitionArn", "region"]
    for key_attribute in key_attributes:
        if event_detail.get(key_attribute) is None:
            logger.warning("Can't enforce policy. No {} in event detail".format(key_attribute))
            return
    
    cluster_arn = event_detail.get("clusterArn")
    cluster_name = cluster_arn.split("/")[-1]
    region_name = event_detail.get("region")
    task_arn = event_detail.get("taskArn")
    task_definition_arn = event_detail.get("taskDefinitionArn")

    task_list = get_resource.get_ecs_task(region_name, cluster_name, [task_arn])
    task_definition = get_resource.get_ecs_task_definition(region_name, task_definition_arn)

    if task_list is None or len(task_list) <= 0:
        logger.warning("Can't enforce policy. No task found for taskArn {}".format(task_arn))
        return
    task = task_list[0]
    if task_definition is None or len(task_definition) <= 0:
        logger.warning("Can't enforce policy. No task definition found for taskDefinitionArn {}".format(task_definition_arn))
        return
    enforce_task_policy(region_name, policy, task, task_definition)



