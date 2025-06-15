import boto3
from os import path
from Infrastructure.Validate_AWSAccount_NoResource_Duplication import ValidateAWSAccountNoResourceDuplication
from Helper.AWS_And_DB_Config_Schema import AWSConfig
import configparser
import logging
import botocore.exceptions
from time import sleep

TEMPLATE_FILE_PATH = path.join('Infrastructure', 'CloudFormation_files', 'EC2_RDS_full_Infrastructure.yml')

class Create_AWS_Environment:
    def __init__(self):
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

        # Initialize AWS data helper with region
        self.precheck_aws_environment=ValidateAWSAccountNoResourceDuplication(self.aws_configuration)
        self.cf = boto3.client('cloudformation', region_name=self.aws_configuration.region_name)

    def _prepare_cloudformation_file(self):
        try:
            with open(TEMPLATE_FILE_PATH, 'r') as file:
                template_body = file.read()
        except Exception as e:
            self.logger.error(f'Cloud Formation template file not exist, please doubel check that file exist and place hoolders are in place, more details: {e}')
            raise e

        # Replace placeholders
        template_body = template_body.format(
            dbinstanceidentifier=self.aws_configuration.dbinstanceidentifier,
            masterusername=self.aws_configuration.masterusername,
            masteruserpassword=self.aws_configuration.masteruserpassword,
            dbname=self.aws_configuration.dbname,
            engine_version=self.aws_configuration.engine_version,
            ec2_instance_name=self.aws_configuration.ec2_instance_name,
            linux_image=self.aws_configuration.linux_image,
            vpc_name=self.aws_configuration.vpc_name,
            rsa_key_name=self.aws_configuration.rsa_key_name)
        return template_body

    def setup_environment(self):
        self.template_body = self._prepare_cloudformation_file()
        stack_name = self.aws_configuration.stackname

        if self.precheck_aws_environment.validate():
            # Create CloudFormation stack
            self.response = self.cf.create_stack(
                StackName=stack_name,
                TemplateBody=self.template_body,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            )
            self.logger.info(f"Stack creation initiated: {self.response['StackId']}")
        else:
            self.logger.warning("Environment setup aborted due to validation failure.")

    def check_stack_status(self):
        """
        Checks the status of the CloudFormation stack and returns a tuple of (status, reason).
        Example: ('ROLLBACK_IN_PROGRESS', 'User initiated rollback')
        """
        stack_name = self.aws_configuration.stackname

        try:
            response = self.cf.describe_stacks(StackName=stack_name)
            stacks = response.get('Stacks', [])
            if not stacks:
                self.logger.error(f"No stack found in the response for '{stack_name}'.")
                return ('NotExist', 'No stack found in response.')

            status = stacks[0]
            return (status.get('StackStatus'),status.get('StackStatusReason',''))

        except botocore.exceptions.ClientError as e:
            self.logger.error(f"AWS ClientError when describing stack '{stack_name}': {e}")
            return ('ERROR', e.response['Error'].get('Message', 'Unknown ClientError'))
        except Exception as e:
            self.logger.error(f"Failed to retrieve stack status for '{stack_name}'. Details: {e}")
            return ('ERROR', str(e))

    def get_rollback_root_cause(self):
        """
        Retrieves the rollback root cause from failed CloudFormation stack events.
        Returns 'CLEAN' if no failed events are found.
        """
        stack_name = self.aws_configuration.stackname

        try:
            response = self.cf.describe_stack_events(StackName=stack_name)
            failed_events = [
                event for event in response.get('StackEvents', [])
                if 'FAILED' in event.get('ResourceStatus', '')
            ]

            if not failed_events:
                self.logger.info(f"No failed events found for stack '{stack_name}'. Stack is clean.")
                return "CLEAN"

            # If no "Likely root cause", return all failed reason
            errors=[]
            for error in failed_events:
                errors.append(error.get('ResourceStatusReason', 'Unknown failure reason.'))

            errors='|'.join(errors)
            self.logger.warning(f"Returning all failure with pipe seperated, Details:{errors}")
            return errors

        except botocore.exceptions.ClientError as e:
            self.logger.error(f"Failed to fetch stack events for '{stack_name}': {e}")
            return f"ERROR: {e.response['Error'].get('Message', str(e))}"

        except Exception as e:
            self.logger.error(f"Unexpected error while retrieving rollback reason: {e}")
            return f"ERROR: {str(e)}"


    def delete_stack(self):
        """
        Deletes the specified CloudFormation stack.
        Logs and returns a status message based on the operation outcome.
        """
        stack_name = self.aws_configuration.stackname

        try:
            self.logger.info(f"Attempting to delete CloudFormation stack: {stack_name}")
            self.cf.delete_stack(StackName=stack_name)
            self.logger.info(f"Delete initiated for stack: {stack_name}")
            return ('DELETE_IN_PROGRESS', f"Deletion started for stack: {stack_name}")

        except botocore.exceptions.ClientError as e:
            self.logger.error(f"AWS ClientError during deletion of stack '{stack_name}': {e}")
            return ('ERROR', e.response['Error'].get('Message', 'Unknown ClientError'))

        except Exception as e:
            self.logger.error(f"Unexpected error during deletion of stack '{stack_name}': {e}")
            return ('ERROR', str(e))
