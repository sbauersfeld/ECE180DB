from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading


####################
##  Global Variables
####################

GAME_OVER = False
IR_HIT = False
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
        H_LOCK.set()

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
    print("Waiting to start action...")
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
        name = sys.argv[1]
    else:
        name = input("Please enter your name: ")

    print("Listening...")
    client.loop_start()

    threads = []
    for func in [control_IR_sensor, control_LED, handle_gesture, handle_hit]:
        t = threading.Thread(target=func, args=[name], daemon=True)
        t.start()
        threads.append(t)

    ### TODO: Have laptop setup player
    client.publish(TOPIC_LAPTOP, name)
    
    for t in threads:
        t.join()
    print("Finished game!")

if __name__ == '__main__':
    main()
