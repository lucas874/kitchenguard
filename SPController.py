# Majority written by Jorge Miranda. Modified to fit our needs.

from __future__ import annotations
from SPModel import SPModel
from SPZigbee2mqttClient import (SPZigbee2mqttClient,
                                   SPZigbee2mqttMessage, SPZigbee2mqttMessageType)

from dataclasses import dataclass
from SPmqttClient import SPmqttClient
from datetime import datetime
from transitions import Machine
import threading
import time
import json
import heucod
from SPControllerStateMachine import ControllerStateMachine

from typing import Dict, Union, Any, List


""" The controller is responsible for managing events received from zigbee2mqtt and handle them.
By handle them it can be process, store and communicate with other parts of the system. In this
case, the class listens for zigbee2mqtt events, processes them (turn on another Zigbee device)
and send an event to a remote HTTP server.
"""

class SPController:

    MQTT_BROKER_HOST = "localhost"
    MQTT_BROKER_PORT = 1883

    def __init__(self, devices_model: SPModel) -> None:
        """ Class initializer. The actuator and monitor devices are loaded (filtered) only when the
        class is instantiated. If the database changes, this is not reflected.

        Args:
            devices_model (SPModel): the model that represents the data of this application
        """
        self.__z2m_client = SPZigbee2mqttClient(host=self.MQTT_BROKER_HOST,
                                        port=self.MQTT_BROKER_PORT,
                                        on_message_clbk=self.__zigbee2mqtt_event_received)

        self.__devices_model = devices_model

        self.state_machine = ControllerStateMachine(self.__z2m_client, self.__devices_model) # Instantiate state machine

    def start(self) -> None:
        """ Start listening for zigbee2mqtt events.
        """
        self.__z2m_client.connect()
        print(f"Zigbee2Mqtt is {self.__z2m_client.check_health()}")
        for a in self.__devices_model.actuators_list:
            self.__z2m_client.change_state(a.id_, "OFF") # Turn off actuators upon boot
            if a.type_ == "led":
                self.__z2m_client.change_color(a.id_, 0, 100, 0) # Make light of LED green

    def stop(self) -> None:
        """ Stop listening for zigbee2mqtt events.
        """
        self.__z2m_client.disconnect()

    def __zigbee2mqtt_event_received(self, message: SPZigbee2mqttMessage) -> None:
        """ Process an event received from zigbee2mqtt. This function given as callback to
        SPZigbee2mqttClient, which is then called when a message from zigbee2mqtt is received.

        Args:
            message (SPZigbee2mqttMessage): an object with the message received from zigbee2mqtt
        """
        # If message is None (it wasn't parsed), then don't do anything.
        if not message:
            return

        print(
            f"zigbee2mqtt event received on topic {message.topic}: {message.data}")

        # If the message is not a device event, then don't do anything.
        if message.type_ != SPZigbee2mqttMessageType.DEVICE_EVENT:
            return

        # If the device ID is known, then process the device event and send a message to the remote
        # web server.

        self.state_machine.trigger(message) # Hand over message to state machine

