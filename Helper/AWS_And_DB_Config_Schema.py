from pydantic import BaseModel, Field

class AWSConfig(BaseModel):
    region_name: str
    stackname: str
    #Database Configuration
    dbinstanceidentifier: str
    masterusername: str
    masteruserpassword: str
    dbname: str
    engine_version:float
    db_port:int
    db_host:str
    #EC2 Configuratoin
    ec2_instance_name:str
    linux_image:str
    #VPC Name
    vpc_name:str
    #RSA Key
    rsa_key_name:str