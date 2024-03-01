import threading
import queue
import logging

logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(self):
        self.subscribers = {}
        self.message_queue = queue.Queue()

    def subscribe(self, topic, callback):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        logger.debug(f"Subscribed {callback} to {topic}")

    def publish(self, topic, message):
        self.message_queue.put((topic, message))
        logger.debug(f"Published message to {topic}")

    def _process_messages(self):
        logger.debug("Starting message processing loop")
        while True:
            topic, message = self.message_queue.get()
            if topic in self.subscribers:
                logger.debug(f"Processing message for {topic}")
                for callback in self.subscribers[topic]:
                    callback(message)

    def start(self):
        logger.info("Starting message processing thread")
        threading.Thread(target=self._process_messages, daemon=True).start()


message_bus = MessageBus()

# Example usage
# def worker1_callback(message):
#     print(f"Worker 1 received: {message}")

# def worker2_callback(message):
#     print(f"Worker 2 received: {message}")

# # Create a MessageBus instance
# message_bus = MessageBus()

# # Subscribe workers to topics
# message_bus.subscribe("topic1", worker1_callback)
# message_bus.subscribe("topic2", worker2_callback)

# # Start the message processing thread
# message_bus.start()

# # Workers publish messages
# message_bus.publish("topic1", "Hello from Worker 1!")
# message_bus.publish("topic2", "Greetings from Worker 2!")

# # Sleep to allow processing time
# time.sleep(1)
