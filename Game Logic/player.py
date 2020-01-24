from config import *
import paho.mqtt.client as mqtt
import sys
import time

def send_msg(client, name, action, target=""):
    if action is Act.PASS:
        print("Not taking any action")
        return

    print("Sending message...")

    topic = "ee180d/hp_shotgun"
    message = '_'.join([name, action.name, target])
    ret = client.publish(topic, message)

    # print(topic)
    print(message)
    # print(ret.is_published())
    # print(ret.rc == mqtt.MQTT_ERR_SUCCESS)

    return ret

def register_action():
    msg = input("Enter the desired action: ").upper()
    if msg in Act.__members__.keys():
        action = Act.__members__[msg]
        return action
    else:
        print("That's not an action!")
        return Act.PASS

def main():
    client = mqtt.Client()
    client.connect("broker.hivemq.com")

    if len(sys.argv) == 2:
        # Sleep necessary if no code present before publish
        time.sleep(0.5)
        name = sys.argv[1]
    else:
        name = input("Please enter your name: ")
    client.publish("ee180d/hp_shotgun/setup", name)

    while True:
        # Extend loop to register detected actions
        action = register_action()
        send_msg(client, name, action)

if __name__ == '__main__':
    main()
