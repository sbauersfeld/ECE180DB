from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading


####################
##  Classes
####################

class Player:
    def __init__(self, name=""):
        self.name = name


####################
##  Global Variables
####################

GAME_OVER = False
A_LOCK = threading.Event()
PLAYER = Player()
client = mqtt.Client()


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
        pass

    if order == ACTION:
        A_LOCK.set()

    if order == STOP_GAME:
        global GAME_OVER
        GAME_OVER = True
        A_LOCK.set()

    if order == PLAYER.name:
        if value1 == HIT:
            pass

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

def control_LED():
    pass

def handle_gesture():
    print("Gesture detection active!")
    A_LOCK.wait()
    while not GAME_OVER:
        print("START ACTION")
        gesture = register_actions_commandline()
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
