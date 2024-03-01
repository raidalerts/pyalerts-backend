import logging
import time
from message_bus import message_bus

logger = logging.getLogger(__name__)


def configure_logging(log_level=logging.INFO):
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process command line arguments')
    parser.add_argument('--settings', type=str, help='Path to settings.yaml file', default='/etc/pyalerts/settings.yaml')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Log level')

    args = parser.parse_args()

    settings_path = args.settings
    log_level = args.log_level
    configure_logging()
    message_bus.start()

    while True:
        time.sleep(1)
