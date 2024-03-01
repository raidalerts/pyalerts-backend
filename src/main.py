from datetime import datetime, timezone
import time
from message_bus import message_bus
from config import load_settings
from alert_monitor import AlertMonitor, Region
from info_monitor import InfoMonitor
from ai_worker import AiWorker
from notifications_sender import NotificationsSender
from telegram import Message
import app_logger

logger = app_logger.get(__name__)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process command line arguments')
    parser.add_argument('--settings', type=str, help='Path to settings.yaml file', default='/etc/pyalerts/settings.yml')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Log level')

    args = parser.parse_args()

    settings_path = args.settings
    log_level = args.log_level
    app_logger.set_log_level(log_level)
    settings = load_settings(settings_path)

    alert_monitor = AlertMonitor(settings)
    info_monitor = InfoMonitor(settings)
    ai_worker = AiWorker(settings)
    notifications_sender = NotificationsSender(settings)

    message_bus.start()
    alert_monitor.start()
    info_monitor.start()
    ai_worker.start()
    notifications_sender.start()

    while True:
        time.sleep(1)
