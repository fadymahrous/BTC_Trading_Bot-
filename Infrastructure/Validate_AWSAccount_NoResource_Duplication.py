from Infrastructure.Get_AWS_Data import Get_AWS_Data
from Helper.AWS_And_DB_Config_Schema import AWSConfig
import logging


class ValidateAWSAccountNoResourceDuplication:
    def __init__(self, aws_configuration: AWSConfig):
        self.logger=logging.getLogger('infrastructure_log')
        if aws_configuration is None:
            self.logger.error("AWS Configuration Object is not passed to the class.")
            raise ValueError("AWS configuration Object is required.")
        
        self.aws_configuration = aws_configuration
        self.fetch_AWS_data = Get_AWS_Data(self.aws_configuration.region_name)

    def validate(self) -> bool:
        # Check for existing RDS instance
        databases_list = self.fetch_AWS_data.list_database_instances()
        if self.aws_configuration.dbinstanceidentifier.lower() in (db.lower() for db in databases_list):
            self.logger.error(f"An RDS instance with the name '{self.aws_configuration.dbinstanceidentifier}' already exists.")
            return False

        # Check if VPC already exists
        vpc_list = self.fetch_AWS_data.list_vpc_names()
        if self.aws_configuration.vpc_name in vpc_list:
            self.logger.error(f"A VPC with the name '{self.aws_configuration.vpc_name}' already exists.")
            return False

        # Check if KeyPair not exist, It must be pre created to save private_Key
        keypair_list = self.fetch_AWS_data.list_key_pairs()
        if self.aws_configuration.rsa_key_name not in keypair_list:
            self.logger.error(f"A Key Pair with the name '{self.aws_configuration.rsa_key_name}' Not exist please create it first and save the .pem key on your device.")
            return False

        # Check if EC2 instance already exists
        ec2instances_list = self.fetch_AWS_data.list_ec2_instance_names()
        if self.aws_configuration.ec2_instance_name in ec2instances_list:
            self.logger.error(f"An EC2 instance with the name '{self.aws_configuration.ec2_instance_name}' already exists.")
            return False

        # Check for existing CloudFormation stack
        if self.aws_configuration.stackname in self.fetch_AWS_data.list_cf_stacks_names():
            self.logger.error(f"A CloudFormation stack with the name '{self.aws_configuration.stackname}' already exists.")
            return False

        return True
