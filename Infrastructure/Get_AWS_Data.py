import boto3
from typing import List
import logging
import configparser
from os import path
from Helper.AWS_And_DB_Config_Schema import AWSConfig


class Get_AWS_Data:
    def __init__(self,region_name:str='eu-central-1'):
        # Load config.ini
        config = configparser.ConfigParser()
        config.read(path.join('Config', 'config.ini'))
        self.logger=logging.getLogger('infrastructure_log')
        try:
            configuration_dict=dict(config['AWS_General'])
            self.aws_configuration = AWSConfig(**configuration_dict)
        except Exception as e:
            self.logger.error(f"Invalid config: {e}")
            raise

        self.logger=logging.getLogger('infrastructure_log')
        self.region_name=region_name
        self.ec2 = boto3.client('ec2',region_name=self.region_name)
        self.rds = boto3.client('rds',region_name=self.region_name)
        self.cf=boto3.client('cloudformation',region_name=self.region_name)

    def get_default_VPCID(self)->str:
        # Get default VPC
        vpcs = self.ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        try:
            default_vpc_id = vpcs['Vpcs'][0]['VpcId']
            return default_vpc_id
        except IndexError:
            self.logger.error('We cant get the default VPCID please be sure you have a Default VPCID in {elf.region_name}')
            return None

    def get_subnets(self,VPCID:str=None,length_of_subntes:int=None)->List[str]:
        if (length_of_subntes or VPCID) is None:
            self.logger.error('You must provide VPCID and lenth of iutput in the while calling the method.')
            return None
        self.VPCID=VPCID
        self.length_of_subntes=length_of_subntes
        subnets=self.ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [self.VPCID]}])
        list_of_subnets=[]
        for subnet in subnets['Subnets']:
            list_of_subnets.append(subnet['SubnetId'])
        result=list_of_subnets[:self.length_of_subntes]
        return ','.join(result)

    def list_database_instances(self)->List[str]:
        try:
            response=self.rds.describe_db_instances()
        except Exception as e:
            self.logger.error('We couldnt get the Instances, and exception raised at rds get instances')
            raise e
        result=[]
        for instance in response['DBInstances']:
            result.append(instance['DBInstanceIdentifier'])
        return result

    def list_vpc_names(self) -> List[str]:
        """
        Returns a list of VPC names (based on the 'Name' tag).
        """
        try:
            vpcs = self.ec2.describe_vpcs()
        except Exception as e:
            self.logger.error('We couldnt List VPC, and exception raised at get list of VPC Details: {e}')
            raise e

        vpc_names = []
        for vpc in vpcs['Vpcs']:
            name_tag = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), None)
            if name_tag:
                vpc_names.append(name_tag)
        return vpc_names

    def list_key_pairs(self) -> List[str]:
        """
        Returns a list of key pair names in the region.
        """
        try:
            key_pairs = self.ec2.describe_key_pairs()
        except Exception as e:
            self.logger.error('We couldnt List Key pairs, and exception raised at describe_key_pairs Details: {e}')
            raise e

        return [key['KeyName'] for key in key_pairs['KeyPairs']]

    def list_ec2_instance_names(self) -> List[str]:
        """
        Returns a list of EC2 instance names (based on 'Name' tag).
        """
        try:
            instances = self.ec2.describe_instances()
        except Exception as e:
            self.logger.error('We couldnt List EC2 Instance Pairs, and exception raised at describe_instances Details: {e}')
            raise e
        names = []
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), None)
                if name_tag:
                    names.append(name_tag)
        return names
    
    def list_cf_stacks_names(self):
        try:
            stacks=self.cf.describe_stacks()
        except Exception as e:
            self.logger.error('We couldnt List CloudFormations Names, and exception raised at describe_stacks Details: {e}')
            raise e
        if stacks.get('Stacks') is not None and len(stacks.get('Stacks'))>0:
            return [stack.get('StackName','') for stack in stacks.get('Stacks')]
        else:
            return []
    
    def get_endpoint_of_dbinstanceidentifier(self,db_instance_id:str=None):
        if db_instance_id is None:
            self.logger.error('you must provide RDS DBidentifiername to get the corresponding Endpoint.')
            raise ValueError('you must provide RDS DBidentifiername to get the corresponding Endpoint.')

        self.db_instance_id =db_instance_id
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=self.db_instance_id)
            endpoint = response['DBInstances'][0]['Endpoint']['Address']
            if endpoint:
                return endpoint
        except Exception as e:
            self.logger.error(f'We couldnt get the Endpoint of database {db_instance_id} as exception was raised Details:{e}')
            raise e
        return []



if __name__=='__main__':
    fetch=Get_AWS_Data()
    vpcid=fetch.get_default_VPCID()
    database=fetch.list_database_instances()
    vpcz=fetch.list_vpc_names()
    keyz=fetch.list_key_pairs()
    ec2z=fetch.list_ec2_instance_names()
    print(vpcid)
    print(database)
    print(vpcz)
    print(keyz)
    print(ec2z)


