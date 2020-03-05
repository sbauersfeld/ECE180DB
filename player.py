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
        # Status
        self.name = name
        self.leds = LED


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


####################
##  Functions
####################

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received unexpected message: " + message)

def on_message_player(client, userdata, msg):
    message = msg.payload.decode()

    if message == ACTION:
        A_LOCK.set()

    if message == STOP_GAME:
        global GAME_OVER
        GAME_OVER = True
        A_LOCK.set()

def send_action(action, value=""):
    message = SEP.join([PLAYER.name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret

def process_orders(value1, value2):
    pass


####################
##  Threads
####################

def control_LED():
    while not GAME_OVER:
        pixels.fill(PLAYER.leds)
        pixels.show()

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
    
    for t in threads:
        t.join()
    print("Finished game!")

if __name__ == '__main__':
    main()
