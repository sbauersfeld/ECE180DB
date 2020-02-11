from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
from sklearn.externals import joblib
from gesture_recognition import IMU
from gesture_recognition.detect_gesture import gesture_setup, get_gesture

####################
##  Global Variables
####################

GAME_OVER = False
A_LOCK = threading.Event()


####################
##  Functions
####################

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received unexpected message: " + message)

def on_message_player(client, userdata, msg):
    message = msg.payload.decode()
    print("Order: " + message)

    if message == START_ACTION:
        A_LOCK.set()
    elif message == STOP_GAME:
        global GAME_OVER
        GAME_OVER = True
        A_LOCK.set()

def send_action(client, name, action, value=""):
    message = '_'.join([name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret

def register_actions_commandline():
    actions = []
    while True:
        msg = input("Enter action: ").upper()
        if msg in Act.__members__.keys():
            action = Act.__members__[msg]
            actions.append(action)

            # if action is Act.PASS or action is Act.HIT:
            #     break
            actions.append(Act.PASS)
            break
        else:
            print("That's not an action!")

    return actions


####################
##  Main function
####################

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.message_callback_add(TOPIC_PLAYER, on_message_player)
    client.connect("broker.hivemq.com")
    client.subscribe(TOPIC_GLOBAL)
    client.subscribe(TOPIC_PLAYER)

    if len(sys.argv) == 2:
        name = sys.argv[1]
    else:
        name = input("Please enter your name: ")

    model, scaler = gesture_setup("wilson", prefix="gesture_recognition/")

    print("Listening...")
    client.loop_start()

    ### TODO: Have laptop setup player
    client.publish(TOPIC_LAPTOP, name)

    A_LOCK.wait()
    while not GAME_OVER:
        gesture = get_gesture(model, scaler).upper()
        if gesture in Act.__members__.keys():
            action = Act.__members__[gesture]
        else:
            action = Act.PASS

        actions = [action]
        for action in actions:
            send_action(client, name, action)

        if not GAME_OVER:
            A_LOCK.clear()
        A_LOCK.wait()

    print("Finished game!")

if __name__ == '__main__':
    main()
