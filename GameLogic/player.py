from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading


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

            if action is Act.PASS:
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
        time.sleep(0.25)
    else:
        name = input("Please enter your name: ")

    print("Listening...")
    client.loop_start()

    ### TODO: Have laptop setup player
    # client.publish(TOPIC_SETUP, name)

    A_LOCK.wait()
    while not GAME_OVER:

        ################
        ### EDIT HERE FOR GESTURE RECOGNITION
        actions = register_actions_commandline()
        ### EDIT HERE FOR GESTURE RECOGNITION
        ################################
        for action in actions:
            send_action(client, name, action)

        if not GAME_OVER:
            A_LOCK.clear()
        A_LOCK.wait()

    print("Finished game!")

if __name__ == '__main__':
    main()
