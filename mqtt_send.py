from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading


####################
##  Global Variables
####################

GAME_OVER = False
client = mqtt.Client()


####################
##  Functions
####################

def send_action(client, name, action, value=""):
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

def handle_gesture(name):
    while not GAME_OVER:
        gesture = register_actions_commandline()
        send_action(client, name, Act[gesture])


####################
##  Main function
####################

def main():
    client.connect("broker.hivemq.com")

    if len(sys.argv) == 2:
        name = sys.argv[1]
    else:
        name = input("Please enter your name: ")

    threads = []
    for func in [handle_gesture]:
        t = threading.Thread(target=func, args=[name], daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    print("Finished game!")

if __name__ == '__main__':
    main()
