import json 
import urllib3
import os
import json

from task_check import task_policy_handler

# Code snippet from lambda_handler.py
# import boto3
import logging
import logging.config
LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': { 
        'standard': { 
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': { 
        'default': { 
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': { 
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    } 
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# get task policy from ssm using lambda extensions

def retrieve_extension_value(url): 
    http = urllib3.PoolManager()
    url = ('http://localhost:' + os.environ['PARAMETERS_SECRETS_EXTENSION_HTTP_PORT'] + url)
    headers = { "X-Aws-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN') }
    response = http.request("GET", url, headers=headers)
    response = json.loads(response.data)   
    return response

def get_policy_from_ssm_parameter(policy_ssm_param_env_var):
    policy = {}
    policy_ssm_param = os.environ.get(policy_ssm_param_env_var,"")
    if len(policy_ssm_param) <= 0:
        logger.warning("No policy SSM parameter set for {}".format(policy_ssm_param_env_var))
        return policy
    policy_ssm_url = ('/systemsmanager/parameters/get/?name=/' + policy_ssm_param)
    policy_ssm = retrieve_extension_value(policy_ssm_url)
    parameter = policy_ssm.get("Parameter", {})
    if parameter is None or len(parameter) <= 0:
        logger.warning("No parameter in task policy SSM {}".format(json.dumps(policy_ssm)))
        return policy
    
    policy = json.loads(parameter.get("Value", {}))     
    return policy

def lambda_handler(event, context):
    """
    Create a lambda function that is triggered 
    from eventbridge event whenever an ECS task is created
    print the task ARN and task definition ARN
    """
    logger.info("Event: {}".format(json.dumps(event)))
    region = event.get("region")
    if region is None:
        logger.warning("No region")
        return
    event_detail = event.get("detail")
    if event_detail is None:
        logger.warning("No event detail")
        return
    detail_type = event.get("detail-type")
    if detail_type is None:
        logger.warning("No detail type")
        return
    event_detail["region"] = region 
    if detail_type == "ECS Task State Change":
        logger.info("Task State Change")
        policy = get_policy_from_ssm_parameter("TASK_POLICY_SSM")
        if policy is None or len(policy) <= 0:
            logger.warning("No task policy found")
            return
        task_policy = policy.get("task", [])
        if task_policy is None or len(task_policy) <= 0:
            logger.warning("No task policy found")
            return
        task_policy_handler(event_detail, task_policy)
        

