import os
import json
from datetime import datetime
from dataclasses import dataclass
from collections import deque
from threading import Lock
from typing import List
from openai import OpenAI
from pytz import timezone
from telegram import Message
from message_bus import message_bus
from config import Settings
import app_logger

logger = app_logger.get(__name__)
persistent_logger = app_logger.get_persistent('ai_worker_persistent')


@dataclass
class AiAlert:
    alert: bool
    attacker: str = "UNKNOWN"
    text: str = None
    confidence: float = None
    original_text: str = None

    @staticmethod
    def from_dict(data: dict):
        return AiAlert(
            alert=data.get('alert'),
            attacker=data.get('attacker', "UNKNOWN"),
            text=data.get('trigger', "<No text>"),
            confidence=data.get('risk', 0.0),
            original_text=data.get('trigger', "<No original text>"),
        )


class AiWorker:
    def __init__(self, settings: Settings):
        self.history = deque(maxlen=10)
        self.state_lock = Lock()
        self.ai_enabled = False
        self.system_prompt = settings.analyzer_prompt
        self.target_timezone = timezone(settings.timezone_name)
        self.chatgpt_api = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    def start(self):
        message_bus.subscribe('new_messages', self.process_messages)
        message_bus.subscribe('alert', self.process_alert_event)
        message_bus.subscribe('clear', self.process_clear_event)
        logger.info('AiWorker started')

    def process_alert_event(self, _):
        with self.state_lock:
            self.history.clear()
            self.ai_enabled = True
            logger.debug("AI analyzer enabled")

    def process_clear_event(self, _):
        with self.state_lock:
            self.history.clear()
            self.ai_enabled = False
            logger.debug("AI analyzer disabled")

    def process_messages(self, messages: List[Message]):
        with self.state_lock:
            if not self.ai_enabled:
                return

        system_messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        history_messages = [
            {"role": "user", "content": f"> HISTORY {msg.date.astimezone(self.target_timezone).strftime('%H:%M:%S')} {msg.author}: {msg.text}"} for msg in self.history
        ]

        new_messages = [
            {"role": "user", "content": f"> NEW {msg.date.astimezone(self.target_timezone).strftime('%H:%M:%S')} {msg.author}: {msg.text}"} for msg in messages
        ]

        for message in messages:
            self.history.append(message)

        history_string = "\n".join([msg['content'] for msg in history_messages])
        new_string = "\n".join([msg['content'] for msg in new_messages])
        all_messages = "\n".join([history_string, new_string])
        debug_log_message = f"Sending messages to AI:\n\n{all_messages}\n"
        logger.debug(debug_log_message)
        persistent_logger.debug(debug_log_message)
        try:
            ai_response = self.chatgpt_api.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=system_messages + history_messages + new_messages + [
                    {
                        "role": "assistant",
                        "content": f"Local time: {datetime.utcnow().astimezone(self.target_timezone).isoformat()}"
                    }
                ],
                temperature=0.01,
                max_tokens=4096,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            persistent_logger.debug(f"AI response:\n\n{ai_response}\n")
            response = json.loads(ai_response.choices[0].message.content)
            persistent_logger.debug(f"AI response payload:\n\n{json.dumps(response, indent=2, ensure_ascii=False)}\n")
            ai_response = AiAlert.from_dict(response)
            if ai_response.alert:
                logger.info(f"AI detected an alert: {ai_response}")
                message_bus.publish('ai_alert', ai_response)
        except Exception as e:
            logger.error(f"Error processing messages with AI: {e}")
