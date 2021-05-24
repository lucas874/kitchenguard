from transitions import Machine
from datetime import datetime
import threading
import time
import json
from SPmqttClient import SPmqttClient
from SPZigbee2mqttClient import (SPZigbee2mqttMessage, SPZigbee2mqttMessageType)
import multiprocessing
import heucod

class ControllerStateMachine:
    states = ['stove_off', 'stove_on', 'unattended']             # Define states

    start_time : str                                           # Start time of stove operation. Assigned when state 'stove_on' is entered. Eventually uploaded to server.
    stop_time : str                                            # Stop time of stove operation.
    time_total = 0                                             # 'timer_begin' and 'timer_end' used to calculate total time spent by stove in seconds.
    timer_begin = 0.
    timer_end = 0.
    frq = 0                                                    # Number of times pr. stove session user left kitchen while stove on
    timer_counter = 0                                          # Used for timing reminders and alerts
    last_pir = None                                            # Points to last pir that sensed presence of user. Use this knowledge to transition between states, blink led in that room etc.
    duration = 10.0                                            # Duration for timer. Timer starts when 'unattended' state is entered. When a timer ends a new is started. Happens 4 times
                                                               # before stove is turned off if user does not re-enter kitchen.
    def __init__(self, z2m_client, devices_model):

        self.mqtt_client = SPmqttClient("192.168.0.144", 1883) # Set up connection to server. Address depends on network environment of system.
                                                               # Run 'hostname -I' or similar on machine running server to get currently leased address.
        self.machine = Machine(                                # Instantiate FSM implemented in transitions module.
            model=self,
            states=self.states,
            initial='stove_off',
        )
        self.__z2m_client = z2m_client
        self.__devices_model = devices_model

        # Add a transition to FSM like this add_transition(trigger, source, dest, optional: before after function)

        # from stove_off to other states
        self.machine.add_transition('stove_turned_on',      'stove_off',      'stove_on',     after='on_turn_on_stove') # transition to stove_on when power > 0

        # from stove_on to other states
        self.machine.add_transition('stove_turned_off',     'stove_on',     'stove_off',      after='on_turn_off_stove_user') # stove turned, off go back to stove_off
        self.machine.add_transition('user_left',            'stove_on',     'unattended',   after='register_unattended')    # user left, enter unattended, start timer

        # from stove_off
        self.machine.add_transition('user_enters_kitchen',  'unattended',    'stove_on',    after='timer_cancel')   # user returns to kitchen, cancel timer go to stove_on
        self.machine.add_transition('timer_expired',        'unattended',    'stove_off',     after='on_turn_off_stove_ctl') # timer expires, enter alerted state

    def trigger(self, message : SPZigbee2mqttMessage):
        # Parse the topic to retreive the device ID. If the topic only has one level, don't do anything.
        tokens = message.topic.split("/")
        if len(tokens) <= 1:
            return

        # Retrieve the device ID from the topic.
        device_id = tokens[1]

        device = self.__devices_model.find(device_id)
        if(not device):
            return
        if device.type_ == "led": # message from led: do nothing
            return

        if device.type_ == "pir" and message.event.get("occupancy"):
            if self.last_pir and self.last_pir.LED_friend:
                self.__z2m_client.change_state(self.last_pir.LED_friend, "OFF") # Make sure that LED's are not left on

            self.last_pir = device # Update last pir member

        print(message.event)

        if self.state == 'stove_off':             # Transitions from stove_off state
            if device.type_ == "power plug" and message.event.get("power") and message.event.get("state") == "ON":
                self.stove_turned_on()
        elif self.state == 'stove_on':          # Transitions from stove on state
            if device.type_ == "power plug" and not message.event.get("power"):
                self.stove_turned_off()
            elif device.type_ == "pir" and device.LED_friend:
                self.user_left()
        else:                                   # Transitions from stove_off state
            if device.type_ == "pir" and not device.LED_friend and message.event.get("occupancy"):
                self.user_enters_kitchen()
        print("Current state: ", self.state)  # Log current state to console

    def blink_led(self, times : int):
        for i in range(times+1): # Blink a number of times by sending publishing "ON" and "OFF" messages.
            self.__z2m_client.change_state(self.last_pir.LED_friend, "ON")
            time.sleep(1)
            self.__z2m_client.change_state(self.last_pir.LED_friend, "OFF")
            time.sleep(1)

    def start_timer(self):
        self.timer = threading.Timer(interval=self.duration, function=self.timer_done) # Create thread for timer. Run it for self.duration seconds. Call timer_done() when timer runs out.
        self.timer.start()


    def timer_done(self):
        print("Timer done") # Log to console when timer is done
        self.timer_counter += 1 # Increment timer counter when timer is done. Use this to call blink_led(timer_counter) and to change color of warning lights.
        if self.timer_counter == 4:
            self.__z2m_client.change_color(self.last_pir.LED_friend, 100, 0, 0) # Power if this piece of code is entered. Change LED light to red.
            self.timer_end = time.time() # Data about stove operation to published to server.
            self.time_total += self.timer_end - self.timer_begin
            self.timer_counter = 0 # Reset timer counter
            self.timer_expired()   # This call makes the FSM transition back to 'stove_off' and triggers a call to turn_stove_off_ctl() to turn off stove
        elif self.timer_counter == 3:
            self.__z2m_client.change_color(self.last_pir.LED_friend, 100, 100, 0)  # Change LED color to yellow.
            self.start_timer() # Start new timer
            self.blink_led(self.timer_counter) # Blink LED
        else:
            self.__z2m_client.change_color(self.last_pir.LED_friend, 0, 100, 0) # Turn light green
            self.start_timer() # Start new timer
            self.blink_led(self.timer_counter) # Blink LED


    def timer_cancel(self):  # Cancel timer. Called when user re-enters kitchen.
        self.timer.cancel()
        self.timer_end = time.time()
        self.time_total += self.timer_end - self.timer_begin  # Compute duration of stove operation
        self.timer_counter = 0 # Reset timer_counter

    def register_unattended(self): # Called upon transitions from stove_on to unattended
        self.frq += 1              # Increment frq member (number of times user left kitchen pr. stove operation)
        self.start_timer()         # Start timer
        self.timer_begin = time.time() # Note this point in time

    def on_turn_off_stove_user(self): # User turns off stove
        print("stove has been turned off") # Log to console
        self.log_stop_time() # Note this point in time
        # Cut the power, thus turning off the stove, but keep the NEO device in the "ON" state
        self.upload_to_server() # Publish information about stove operatioin to server.


    def on_turn_off_stove_ctl(self): # Controller cuts power to Immax Neo
        print("stove has been turned off") # Log to console
        self.log_stop_time()    # Note this point in time
        self.__z2m_client.change_state("NEO", "OFF") # Publish message meant for NEO telling it to change state to "OFF"
        self.upload_to_server() # Publish stove opearation data to server
        self.blink_led(5) # Blink LED 5 times

    def on_turn_on_stove(self):
        print("stove has been turned on") # Log to console
        self.log_start_time()    # Note this point in time

    def log_start_time(self):
        now = datetime.now()
        self.start_time = now.strftime("%H:%M:%S")

    def log_stop_time(self):
        now = datetime.now()
        self.stop_time = now.strftime("%H:%M:%S")

    def upload_to_server(self):
        mqtt_event = heucod.HeucodEvent() # Create heucod event
        mqtt_event.start_time = self.start_time # Set up fields in heucod event
        mqtt_event.end_time = self.stop_time
        mqtt_event.value = self.frq
        mqtt_event.value2 = round(self.time_total)
        print(mqtt_event.to_json()) # Log message to be published
        self.mqtt_client.publish_to_server(mqtt_event.to_json()) # Publish

        #reset values
        self.frq = 0
        self.time_total = 0.
        self.start_time = None
        self.stop_time = None

