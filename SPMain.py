# Written by Jorge Miranda. Originally named Cep2Main.py. Available on Blackboard for CE students. Modified to fit our needs.

from time import sleep
from SPController import SPController
from SPModel import SPModel, SPZigbeeDevice

if __name__ == "__main__":
    devices_model = SPModel()
    devices_model.add([SPZigbeeDevice(id_ = "LED1", type_ = "led"),  # Add devices to model
                       SPZigbeeDevice(id_ = "LED2", type_ = "led"),
                       SPZigbeeDevice(id_ = "NEO", type_ = "power plug"),
                       SPZigbeeDevice(id_ = "PIR1", type_ = "pir", LED_friend="LED1"), # Associate PIR with LED
                       SPZigbeeDevice(id_ = "PIR2", type_ = "pir", LED_friend="LED2"),
                       SPZigbeeDevice(id_ = "PIR3", type_ = "pir")])

    # Create a controller and give it the data model that was instantiated.
    controller = SPController(devices_model)
    controller.start()

    print("Waiting for events...")

    while True:
        sleep(1)

    controller.stop()
