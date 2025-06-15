from Helper.logger_setup import setup_logger
import configparser
from time import sleep
from os import path
from Infrastructure.Create_AWS_Environment import Create_AWS_Environment


logger = setup_logger('infrastructure_log', 'infrastructure.log')


def main():
    try:
        logger.info("Starting AWS infrastructure provisioning...")

        aws_env = Create_AWS_Environment()
        aws_env.setup_environment()

        # Monitor stack status
        while True:
            status, reason = aws_env.check_stack_status()
            logger.info(f"AWS Stack Status: {status} - {reason}")
            print(f"Status: {status} -> {reason}")

            if status == 'CREATE_COMPLETE':
                logger.info("Stack creation completed successfully.")
                break
            elif status == 'ROLLBACK_COMPLETE':
                logger.error("Stack creation failed. Deleting stack...")
                aws_env.delete_stack()
                return
            sleep(10)

        # Load symbol from config
        config = configparser.ConfigParser()
        config.optionxform = str  # preserve case
        config.read(path.join('Config', 'config.ini'))

        #symbol = config.get('AWS_General', 'symbol', fallback='BTC/USDT')

    except Exception as e:
        logger.exception(f"Exception occurred during infrastructure setup: {e}")
        print("An error occurred. Check logs for details.")

if __name__ == '__main__':
    main()
