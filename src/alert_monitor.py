import threading
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from telegram import fetch_latest_messages
from message_bus import message_bus
from config import Settings
import app_logger

logger = app_logger.get(__name__)


@dataclass
class Region:
    id: int
    name: str
    name_en: str
    alert: bool
    changed: datetime


class AlertMonitor:
    def __init__(self, settings: Settings):
        self.channel_name = settings.alert_channel
        self.interval = settings.alert_polling_interval
        self.backoff_interval = settings.alert_backoff_polling_interval
        self.last_checked = None
        self.region_id = settings.region_to_monitor
        self.alert = False
        self.regions = [
            Region(id=1, name="Вінницька область", name_en="Vinnytsia oblast", alert=False, changed=None),
            Region(id=2, name="Волинська область", name_en="Volyn oblast", alert=False, changed=None),
            Region(id=3, name="Дніпропетровська область", name_en="Dnipropetrovsk oblast", alert=False, changed=None),
            Region(id=4, name="Донецька область", name_en="Donetsk oblast", alert=False, changed=None),
            Region(id=5, name="Житомирська область", name_en="Zhytomyr oblast", alert=False, changed=None),
            Region(id=6, name="Закарпатська область", name_en="Zakarpattia oblast", alert=False, changed=None),
            Region(id=7, name="Запорізька область", name_en="Zaporizhzhia oblast", alert=False, changed=None),
            Region(id=8, name="Івано-Франківська область", name_en="Ivano-Frankivsk oblast", alert=False, changed=None),
            Region(id=9, name="Київська область", name_en="Kyiv oblast", alert=False, changed=None),
            Region(id=10, name="Кіровоградська область", name_en="Kirovohrad oblast", alert=False, changed=None),
            Region(id=11, name="Луганська область", name_en="Luhansk oblast", alert=False, changed=None),
            Region(id=12, name="Львівська область", name_en="Lviv oblast", alert=False, changed=None),
            Region(id=13, name="Миколаївська область", name_en="Mykolaiv oblast", alert=False, changed=None),
            Region(id=14, name="Одеська область", name_en="Odesa oblast", alert=False, changed=None),
            Region(id=15, name="Полтавська область", name_en="Poltava oblast", alert=False, changed=None),
            Region(id=16, name="Рівненська область", name_en="Rivne oblast", alert=False, changed=None),
            Region(id=17, name="Сумська область", name_en="Sumy oblast", alert=False, changed=None),
            Region(id=18, name="Тернопільська область", name_en="Ternopil oblast", alert=False, changed=None),
            Region(id=19, name="Харківська область", name_en="Kharkiv oblast", alert=False, changed=None),
            Region(id=20, name="Херсонська область", name_en="Kherson oblast", alert=False, changed=None),
            Region(id=21, name="Хмельницька область", name_en="Khmelnytskyi oblast", alert=False, changed=None),
            Region(id=22, name="Черкаська область", name_en="Cherkasy oblast", alert=False, changed=None),
            Region(id=23, name="Чернівецька область", name_en="Chernivtsi oblast", alert=False, changed=None),
            Region(id=24, name="Чернігівська область", name_en="Chernihiv oblast", alert=False, changed=None),
            Region(id=25, name="м. Київ", name_en="Kyiv", alert=False, changed=None),
        ]

    def check_alerts(self):
        logger.debug("Checking for alerts")
        while True:
            try:
                messages = fetch_latest_messages(self.channel_name, newer_than=self.last_checked)
                self.last_checked = datetime.utcnow().replace(tzinfo=timezone.utc)
                for message in messages:
                    # Parse the message to identify whether an alert is active for one of the predefined regions
                    # Update the alert status and changed time for the corresponding region

                    if "Повітряна тривога" in message.text:
                        alert = True
                    elif "Відбій" in message.text:
                        alert = False
                    else:
                        continue

                    for region in self.regions:
                        if region.name in message.text:
                            region.alert = alert
                            region.changed = message.date
                            logger.debug(f"Alert status for {region.name} is {alert}")
                            if self.region_id == region.id:
                                if alert:
                                    message_bus.publish("alert", region)
                                    self.alert = True
                                else:
                                    message_bus.publish("clear", region)
                                    self.alert = False
                            break
            except Exception as e:
                logger.error(f"Error checking for alerts: {e}")

            if self.alert:
                time.sleep(self.backoff_interval)
            else:
                time.sleep(self.interval)

    def start(self):
        logger.info("Starting alert monitor")
        threading.Thread(target=self.check_alerts, daemon=True).start()
