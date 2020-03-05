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

def handle_gesture(name):
    while not GAME_OVER:
        gesture = register_actions_commandline()
        send_action(name, Act[gesture])
        time.sleep(0.5)


####################
##  Main function
####################

def main():
    client.connect("broker.hivemq.com")

    if len(sys.argv) == 2:
        name = sys.argv[1].lower()
    else:
        name = input("Please enter your name: ")

    threads = []
    t_args = {
        handle_gesture : [name],
    }
    for func, args in t_args.items():
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    print("Finished game!")

if __name__ == '__main__':
    main()
