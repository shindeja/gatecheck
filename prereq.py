import sys
import os
import json
import boto3
import botocore
import random
from botocore.config import Config
import click
from dotenv import load_dotenv

def delete_iam_policy_and_role(iam_role_arn):
    role_name = iam_role_arn.split('/')[-1]
    iam = boto3.client('iam')
    try:
        response = iam.list_role_policies(RoleName=role_name)
    except botocore.exceptions.ClientError as e:
        print(e)
        return
    for policy in response.get('PolicyNames',[]):
        print(f"Deleting policy {policy}")
        try:
            resp = iam.delete_role_policy(RoleName=role_name, PolicyName=policy)
        except botocore.exceptions.ClientError as e:
            print(e)
            continue
    print(f"Deleting role {role_name}")
    try:
        resp = iam.delete_role(RoleName=role_name)
    except botocore.exceptions.ClientError as e:
        print(e)
    return
    

def delete_ssm_parameter(region, name):
    ssm = boto3.client('ssm', config=Config(region_name=region))
    print(f"Deleting SSM parameter {name}")
    try:
        ssm.delete_parameter(Name=name)
    except botocore.exceptions.ClientError as e:
        print(e)
    return

def append_to_env_file(env_file, key, value):
    with open(env_file, "a") as f:
        f.write(f"{key}={value}\n")

def create_iam_role(iam_policy_file, role_name):
    role_arn = ""
    lambda_trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    iam = boto3.client('iam')
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(lambda_trust_policy)
        )
    except botocore.exceptions.ClientError as e:
        print(e)
        return role_arn
    with open(iam_policy_file) as f:
        iam_policy = json.load(f)
        for policy_name, value in iam_policy.items():
            print(f"Creating policy {policy_name}")
            try:
                resp = iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(value)
                )
            except botocore.exceptions.ClientError as e:
                print(e)
                continue
    role_arn = response.get('Role',{}).get('Arn',"")
    return role_arn

def store_policy_in_ssm(region, policy_json_file, name):
    ssm = boto3.client('ssm', config=Config(region_name=region))
    with open(policy_json_file) as f:
        policy_json = json.load(f)
    try:
        ssm.put_parameter(
            Name=name,
            Value=json.dumps(policy_json),
            Type='String',
            Overwrite=True
        )
    except botocore.exceptions.ClientError as e:
        print(e)
    return

@click.group()
def prereq():
    pass

@prereq.command()
@click.option('-r','--region', default='', help='AWS Region')
@click.option('-f','--task_policy_json_file', default='', help='Path to policy json file')
@click.option('-n','--name', default='/gatecheck/ecs-task-policy', help='SSM parameter name')
def ssm(region, task_policy_json_file, name):
    if len(region) <=0:
        region = os.environ['AWS_REGION']
        if len(region) <=0:
            print("Please set AWS_REGION environment variable or provide -r/--region parameter")
            sys.exit(1)
        print(f"Using region {region}")
    if len(task_policy_json_file) <=0:
        print("Please provide -f/--task_policy_json_file parameter")
        sys.exit(1)
    # check if task_policy_json_file exists
    if not os.path.isfile(task_policy_json_file):
        print(f"File {task_policy_json_file} does not exist")
        sys.exit(1)

    store_policy_in_ssm(region, task_policy_json_file, name)
    append_to_env_file(".env","GATECHECK_TASK_POLICY_SSM_PARAMETER", name)
    print(f"Stored SSM parameter {name} in .env file")


@prereq.command()
@click.option('-f','--iam_policy_json_file', default='', help='Path to policy json file')
@click.option('-n','--name', default='gatecheck-lambda-role', help='IAM role name for gatecheck')
def iam(iam_policy_json_file, name):
    iam_salt = "-"+str(random.randint(1000,9999))
    if len(iam_policy_json_file) <=0:
        print("Please provide -f/--iam_policy_json_file parameter")
        sys.exit(1)
    # check if task_policy_json_file exists
    if not os.path.isfile(iam_policy_json_file):
        print(f"File {iam_policy_json_file} does not exist")
        sys.exit(1)
    name = name+iam_salt
    role_arn = create_iam_role(iam_policy_json_file, name)
    append_to_env_file(".env","GATECHECK_IAM_ROLE", role_arn)
    print(f"Created IAM role {role_arn} and stored ARN in .env file")

@prereq.command()
@click.option('-r','--region', default='', help='AWS Region')
@click.option('-f','--ssm-lambda-extension-json-file', default='ssm-lambda-extensions.json', help='Path JSON file container region to SSM Lambda extension ARN mapping')
@click.option('-a','--architecture', default='x86_64', type=click.Choice(['x86_64', 'arm64']), help='Architecture of the Lambda function')
def extension(region, ssm_lambda_extension_json_file, architecture):
    if len(region) <=0:
        region = os.environ['AWS_REGION']
        if len(region) <=0:
            print("Please set AWS_REGION environment variable or provide -r/--region parameter")
            sys.exit(1)
        print(f"Using region {region}")
    if not os.path.isfile(ssm_lambda_extension_json_file):
        print(f"File {ssm_lambda_extension_json_file} does not exist")
        sys.exit(1)
    with open(ssm_lambda_extension_json_file) as f:
        ssm_lambda_extensions = json.load(f)
        arch_ext_map = ssm_lambda_extensions.get(architecture,{})
        if len(arch_ext_map) <=0:
            print(f"No SSM Lambda extension found for architecture {architecture} in {ssm_lambda_extension_json_file}")
            sys.exit(1)
        lambda_ext_arn = arch_ext_map.get(region,"")
        if len(lambda_ext_arn) <=0:
            print(f"No SSM Lambda extension found for region {region} in {ssm_lambda_extension_json_file} for architecture {architecture}")
            sys.exit(1)
        append_to_env_file(".env", "GATECHECK_SSM_LAMBDA_EXTENSION", lambda_ext_arn)
        print(f"Stored SSM Lambda extension ARN {lambda_ext_arn} in .env file")
        append_to_env_file(".env", "GATECHECK_ARCHITECTURE", architecture)
        print(f"Stored architecture {architecture} in .env file")


@prereq.command()
@click.option('-e','--env_file', default='.env', help='Path to env file')
@click.option('-f','--template_file', default='.example_template.yaml', help='Path to sample SAM template file')
def sam(env_file, template_file):
    if not os.path.isfile(env_file):
        print(f"File {env_file} does not exist")
        sys.exit(1)
    if not os.path.isfile(template_file):
        print(f"File {template_file} does not exist")
        sys.exit(1)
    load_dotenv()
    req_input = [ "GATECHECK_IAM_ROLE", "GATECHECK_TASK_POLICY_SSM_PARAMETER", "GATECHECK_SSM_LAMBDA_EXTENSION", "GATECHECK_ARCHITECTURE"]
    for k in req_input:
        if not os.getenv(k):
            print(f"Environment variable {k} is not set in {env_file}")
            sys.exit(1)
    with open(template_file) as f:
        data = f.read()
        for k in req_input:
            value = os.getenv(k)
            data = data.replace(f"<{k}>", value)
        with open("template.yaml", "w") as tf:
            tf.write(data)
            print("Wrote template.yaml")

@prereq.command()
@click.option('-e','--env_file', default='.env', help='Path to env file')
def cleanup(env_file):
    if not os.path.isfile(env_file):
        print(f"File {env_file} does not exist")
        sys.exit(1)
    load_dotenv()
    req_input = [ "GATECHECK_IAM_ROLE", "GATECHECK_TASK_POLICY_SSM_PARAMETER", "AWS_REGION"]
    for k in req_input:
        if not os.getenv(k):
            print(f"Environment variable {k} is not set in {env_file}")
            sys.exit(1)
    delete_iam_policy_and_role(os.getenv("GATECHECK_IAM_ROLE"))
    delete_ssm_parameter(os.getenv("AWS_REGION"), os.getenv("GATECHECK_TASK_POLICY_SSM_PARAMETER"))


if __name__ == '__main__':
    prereq()