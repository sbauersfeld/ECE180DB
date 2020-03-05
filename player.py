from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
from sklearn.externals import joblib
from gesture_recognition import IMU
from gesture_recognition.detect_gesture import gesture_setup, get_gesture2
import board
import neopixel


####################
##  Classes
####################

class Player:
    def __init__(self, name="", LED=(127, 0, 0)):
        self.name = name
        self.leds = LED
        self.type = 0

    def update(self, LED, flash_type=0):
        self.leds = LED
        self.type = flash_type
        L_LOCK.set()


####################
##  Global Variables
####################

GAME_OVER = False
A_LOCK = threading.Event()
L_LOCK = threading.Event()
PLAYER = Player()
client = mqtt.Client()

# LED Board
num_pixels = 12
pixels = neopixel.NeoPixel(board.D18, num_pixels)
LED_OFF = (0, 0, 0)
LED_DIST = (127, 0, 0)
LED_ACTION = (0, 0, 127)
LED_HIT = (127, 127, 0)


####################
##  Functions
####################

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received unexpected message: " + message)

def on_message_player(client, userdata, msg):
    message = msg.payload.decode()

    try:
        msg_list = message.split(SEP)
        order = msg_list[0]
        value1 = msg_list[1]
        value2 = msg_list[2]
    except (IndexError):
        print("Unexpected message: {}".format(message))
        return

    process_orders(order, value1, value2)

def send_action(action, value=""):
    message = SEP.join([PLAYER.name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret

def process_orders(order, value1, value2):
    if order == DIST:
        PLAYER.update(LED_DIST)

    if order == ACTION:
        A_LOCK.set()
        PLAYER.update(LED_ACTION, 2)

    if order == STOP_GAME:
        global GAME_OVER
        GAME_OVER = True
        A_LOCK.set()

    if order == PLAYER.name:
        if value1 == HIT:
            PLAYER.update(LED_HIT, 1)


####################
##  LED Functions
####################

def LED_show():
    pixels.fill(PLAYER.leds)
    pixels.show()

### Make the following two last for as long as "___" ###
### Maybe change to have update accept a single "command" variable?
def LED_flash():
    t_end = time.time() + 1.5
    while time.time() < t_end:
        pixels.fill(PLAYER.leds)
        pixels.show()
        time.sleep(.1)
        pixels.fill(LED_OFF)
        pixels.show()
        time.sleep(.1)
    LED_show()

def LED_snake():
    t_end = time.time() + 3
    while time.time() < t_end:
        for i in range(num_pixels):
            pixels.fill(LED_OFF)
            pixels[i-2] = (PLAYER.leds)
            pixels[i-1] = (PLAYER.leds)
            pixels[i] = (PLAYER.leds)
            pixels.show()
            time.sleep(.05)
    LED_show()


####################
##  Threads
####################

def control_LED():
    while not GAME_OVER:
        if PLAYER.type == 0:
            LED_show()
        elif PLAYER.type == 1:
            LED_flash()
        elif PLAYER.type == 2:
            LED_snake()

        if not GAME_OVER:
            L_LOCK.clear()
        L_LOCK.wait()

def handle_gesture():
    print("Setting up sensors")
    model, scaler = gesture_setup("scott", "ft4", "sft4", prefix="gesture_recognition/")

    print("Gesture detection active!")
    A_LOCK.wait()
    while not GAME_OVER:
        print("START ACTION")

        gesture = get_gesture2(model, scaler).upper()
        send_action(Act[gesture])
        time.sleep(0.5)

        if not GAME_OVER:
            A_LOCK.clear()
        A_LOCK.wait()


####################
##  Main function
####################

def main():
    client.on_message = on_message
    client.message_callback_add(TOPIC_PLAYER, on_message_player)
    client.connect("broker.hivemq.com")
    client.subscribe(TOPIC_GLOBAL)
    client.subscribe(TOPIC_PLAYER)

    if len(sys.argv) == 2:
        name = sys.argv[1].lower()
    else:
        name = input("Please enter your name: ")
    PLAYER.name = name

    print("Listening...")
    client.loop_start()

    threads = []
    t_args = {
        control_LED : [],
        handle_gesture : [],
    }
    for func, args in t_args.items():
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()
        threads.append(t)

    ### TODO: Have laptop setup player
    client.publish(TOPIC_LAPTOP, name)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        pass

    print("Finished game!")
    pixels.fill(LED_OFF)
    pixels.show()

if __name__ == '__main__':
    main()
