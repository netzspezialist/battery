import random
import paho.mqtt.client as mqtt

from config import mqtt as mqttConfig

class BatteryMqtt:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info('Creating mqtt client ...')
        client_id = mqttConfig[f"client_id"]
        client_id += f'_{random.randint(0, 1000)}' 
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
  
        self.topic = mqttConfig["topic"]
        self.enabled = mqttConfig["enabled"]

        self.logger.info(f'Mqtt enabled: {self.enabled} topic: {self.topic}')

    def connect(self):
        if not self.enabled:
            return

        def on_connect(client, userdata, flags, rc, properties):
            if rc == 0:
                self.logger.info("Connected to MQTT Broker!")
            else:
                self.logger.error(f"Failed to connect, return code [{rc}]")

        #self.client.username_pw_set(mqttConfig["username"], mqttConfig["password"])
        broker_address = mqttConfig["broker_address"]
        port = mqttConfig["port"]
        self.logger.info(f'Connecting to mqtt broker {broker_address}:{port}')

        self.client.on_connect = on_connect
        self.client.connect(broker_address, port)
        self.client.loop_start()

    def publish_message(self, command, data):
        if not self.enabled:
            return
        topic = f"{self.topic}/{command}"
        self.logger.debug(f'Publishing to [{topic}] data [{data}]')
        self.client.publish(topic, data, qos=1, retain=True)

    def disconnect(self):
        if not self.enabled:
            return
        self.logger.info('Disconnecting from MQTT broker')
        self.client.loop_stop()
        self.client.disconnect()