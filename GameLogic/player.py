from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading

P_LOCK = threading.Event()

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received message: " + message)

    if message == "start_action":
        P_LOCK.set()

def send_action(client, name, action, value=""):
    print("Sending message...")

    topic = "ee180d/hp_shotgun/action"
    message = '_'.join([name, action.name, value])
    ret = client.publish(topic, message)

    print(message)
    # print(ret.is_published())
    return ret

### REMOVE THIS AFTER GESTURE RECOGNTION ###
def register_action():
    actions = []

    while True:
        msg = input("Enter the desired action: ").upper()
        if msg in Act.__members__.keys():
            action = Act.__members__[msg]
            actions.append(action)

            if action is Act.PASS:
                break
        else:
            print("That's not an action!")

    return actions

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("broker.hivemq.com")
    client.subscribe("ee180d/hp_shotgun/player")

    if len(sys.argv) == 2:
        name = sys.argv[1]
        time.sleep(0.25)
    else:
        name = input("Please enter your name: ")
    client.publish("ee180d/hp_shotgun/setup", name)

    print("Listening...")
    client.loop_start()

    while True:
        P_LOCK.wait()
        
        ### EDIT HERE FOR GESTURE RECOGNITION ###
        actions = register_action()
        for action in actions:
            send_action(client, name, action)

        P_LOCK.clear()

if __name__ == '__main__':
    main()
