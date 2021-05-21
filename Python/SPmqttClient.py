# Written from SPhttpClient.py. Modified to use mqtt instead of http

import json
from dataclasses import dataclass
from typing import Any
from paho.mqtt.client import Client as MqttClient, MQTTMessage
from paho.mqtt import publish, subscribe

@dataclass
class SPWebDeviceEvent:
    """ Represents a device event that is sent to the remote web service.
    """
    device_id: str
    device_type: str
    measurement: Any

    def to_json(self) -> str:
        """ Serializes the object to a JSON string.

        Returns:
            str: the event in JSON format
        """
        # The dumps() function serializes an object to a JSON string. In this case, it serializes a
        # dictionary.
        return json.dumps({"deviceId": self.device_id,
                           "deviceType": self.device_type,
                           "measurement": self.measurement})


class SPmqttClient:
    """ Represents a local web client that sends events to a remote web service.
    """

    def __init__(self, host: str, port: int) -> None:
        """ Default initializer.

        Args:
            host (str): an URL with the address of the remote web service
        """
        self.__client = MqttClient()
        self.__host = host
        self.__port = port



    def publish_to_server(self, event: str) -> None:
        try:
            self.__client.connect(self.__host, self.__port, 60)
            self.__client.publish(topic=f"server", payload=event)
            self.__client.disconnect()
            print("Published to server topic")
        except ConnectionError as ex:
            print(ex)
        else:
            pass


    def publish_to_server1(self, event: str) -> None:
        try:
            self.__client.connect(self.__host, self.__port, 60)
            self.__client.publish(topic=f"server/config", payload=event)
            self.__client.disconnect()
            print("Published to server topic")
        except ConnectionError as ex:
            print(ex)
        else:
            pass
