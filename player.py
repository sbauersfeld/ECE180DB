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
##  Global Variables
####################

GAME_OVER = False
A_LOCK = threading.Event()
L_LOCK = threading.Event()
client = mqtt.Client()

# LED Board
num_pixels = 12
pixels = neopixel.NeoPixel(board.D18, num_pixels)
LED_OFF = (0, 0, 0)
LED_DIST = (127, 0, 0)
LED_ACTION = (0, 0, 127)
LED_HIT = (127, 127, 0)

# Commands
default_command = (LED_show, [LED_DIST])
command_map = {
    DIST : default_command,
    ACTION : (LED_snake, [LED_ACTION]),
    HIT : (LED_flash, [LED_HIT]),
}

####################
##  Classes
####################

class Player:
    def __init__(self, name=""):
        self.name = name
        self.threads = []

    def update(self, command):
        L_LOCK.Set()
        for t in threads:
            t.join()

        for func, args in command_map.get(command, default_command):
            t = threading..Thread(target=func, args=args)
            t.start()
            threads.append(t)

PLAYER = Player()


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

def LED_show(LED):
    pixels.fill(LED)
    pixels.show()

def LED_flash(LED):
    while True:
        pixels.fill(LED)
        pixels.show()
        time.sleep(.1)
        pixels.fill(LED_OFF)
        pixels.show()
        time.sleep(.1)

        if L_LOCK.isSet():
            L_LOCK.clear()
            break

def LED_snake(LED):
    while True:
        for i in range(num_pixels):
            pixels.fill(LED_OFF)
            pixels[i-2] = (LED)
            pixels[i-1] = (LED)
            pixels[i] = (LED)
            pixels.show()
            time.sleep(.05)

        if L_LOCK.isSet():
            L_LOCK.clear()
            break


####################
##  Threads
####################

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
