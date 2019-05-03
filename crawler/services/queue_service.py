
import pika
import json


class QueueService(object):
    def __init__(self, host, port, queue):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port))
        self.channel = self.connection.channel()
        self.queue = queue
        self.channel.queue_declare(queue=self.queue)

    def publish(self, msg):
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=json.dumps(msg))

    def disconnect(self):
        if not self.connection.is_closed:
            self.connection.close()
