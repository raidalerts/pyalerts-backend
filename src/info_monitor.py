import threading
import time
from datetime import timedelta, timezone, datetime
from telegram import fetch_latest_messages
from message_bus import message_bus
from config import Settings
import app_logger

logger = app_logger.get(__name__)


class InfoMonitor:
    def __init__(self, settings: Settings):
        self.channel_names = settings.info_channels
        self.interval = settings.info_polling_interval
        self.stop_list = settings.stop_list
        self.channel_last_fetched = {channel_name: None for channel_name in self.channel_names}
        self.sync_event = threading.Event()

    def start(self):
        message_bus.subscribe('alert', self.process_alert_event)
        message_bus.subscribe('clear', self.process_clear_event)
        threading.Thread(target=self.fetch_messages_thread, daemon=True).start()
        logger.info('InfoMonitor started')

    def process_alert_event(self, region):
        for channel_name in self.channel_names:
            self.channel_last_fetched[channel_name] = region.changed - timedelta(minutes=5)
        self.sync_event.set()
        logger.info('Alert event received, fetching new messages')

    def process_clear_event(self, _):
        self.sync_event.clear()
        logger.info('Clear event received, stopping fetching new messages')

    def fetch_messages_thread(self):
        while self.sync_event.wait():
            messages = []
            for channel_name in self.channel_names:
                logger.debug(f'Fetching messages from {channel_name}')
                channel_messages = fetch_latest_messages(channel_name, newer_than=self.channel_last_fetched[channel_name], stop_list=self.stop_list)
                self.channel_last_fetched[channel_name] = datetime.utcnow().replace(tzinfo=timezone.utc)
                if len(channel_messages) > 0:
                    logger.info(f'Fetched {len(channel_messages)} messages from {channel_name}')
                messages.extend(channel_messages)
                time.sleep(0.3)

            sorted_messages = sorted(messages, key=lambda m: m.date)

            if sorted_messages:
                message_bus.publish('new_messages', sorted_messages)

            time.sleep(self.interval)
