from os import environ

import requests
from boto3 import Session
from demo1.api.demo1_error import Demo1Error
from demo1.api.tasks.basic_task import BasicTask


class UpdateRoute53Task(BasicTask):

    def execute(self):
        # CHECK ECS CONTAINER MODE
        if not environ.get('ECS_CONTAINER_METADATA_URI_V4'):
            self.logger.info(
                f'It is not a ECS container. The task (update route 53) is omit.')
            return

        self.logger.info(f'Execute update route53 task')

        session = Session(profile_name=environ.get(
            'AWS_PROFILE'), region_name=environ['AWS_REGION'])

        route53_client = session.client('route53')

        hosted_zone_id = 'Z046710430I8G35A8IVE4'
        domain_name = 'www.zefshar.com'

        response = route53_client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=domain_name)
        ip_address = response['ResourceRecordSets'][0]['ResourceRecords'][0]['Value']

        self.logger.info(f'IP ADDR for {domain_name} is {ip_address}')

        # REQUEST environ['ECS_CONTAINER_METADATA_URI_V4']
        ecs_container_metadata = requests.get(
            url=environ['ECS_CONTAINER_METADATA_URI_V4']).json()
        network_mode = ecs_container_metadata['Networks'][0]['NetworkMode']
        ecs_ip_address = ecs_container_metadata['Networks'][0]['IPv4Addresses'][0]
        container_arn = ecs_container_metadata['ContainerARN']

        if ip_address == ecs_ip_address:
            self.logger.info(
                f'Address of ECS container {ecs_ip_address} is the same as in route53 {ip_address}.')
            return
        result = route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Comment': f'Auto generated Record for ECS Fargate. Container arn is ${container_arn}',
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                            'Name': domain_name,
                            'Type': 'A',
                            'TTL': 180,
                            'ResourceRecords': [{
                                    'Value': ecs_ip_address
                            }]}
                }]
            }
        )
        self.logger.info(f'NEW IP ADDR for {domain_name} is {ecs_ip_address}')

