from boto3 import Session
from demo1.api.demo1_error import Demo1Error
from demo1.api.tasks.basic_task import BasicTask


class UpdateRoute53Task(BasicTask):

    def execute(self):
        self.logger.info(f'Execute update route53 task')
        # TODO CHECK ENVIRONMENT
        # REQUEST ROUTE53
        # REQUEST IP ADDRESS
        # IF ROUTE53 HAS DIFFERENCE UPDATE ROUTE53
        session = Session(profile_name='i.usalko', region_name='us-east-2')

        route53_client = session.client('route53')

        response = route53_client.list_resource_record_sets(
            HostedZoneId='Z046710430I8G35A8IVE4',
            StartRecordName='www.zefshar.com')
        ip_address = response['ResourceRecordSets'][0]['ResourceRecords'][0]['Value']

        print(f'OK IP ADDR for www.zefshar.com is {ip_address}')

        #ecs_client = session.client('ecs')
        #ec2_client = session.client('ec2')
