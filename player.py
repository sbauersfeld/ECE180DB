from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
from sklearn.externals import joblib
from gesture_recognition import IMU
from gesture_recognition.detect_gesture import gesture_setup, get_gesture2


####################
##  Global Variables
####################

GAME_OVER = False
A_LOCK = threading.Event()
client = mqtt.Client()


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

def send_action(name, action, value=""):
    message = SEP.join([name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret

def register_actions_commandline():
    actions = []
    while True:
        action_str = input("Enter action: ").upper()
        if action_str in Act.__members__.keys():
            return action_str
        else:
            print("That's not an action!")

    return actions


####################
##  Threads
####################

def control_LED(name):
    pass

def handle_gesture(name):
    print("Setting up sensors")
    model, scaler = gesture_setup("scott", "ft4", "sft4", prefix="gesture_recognition/")

    print("Gesture detection active!")
    A_LOCK.wait()
    while not GAME_OVER:
        print("START ACTION")
        gesture = get_gesture2(model, scaler).upper()
        send_action(name, Act[gesture])
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

    print("Listening...")
    client.loop_start()

    threads = []
    t_args = {
        control_LED : [name],
        handle_gesture : [name],
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
