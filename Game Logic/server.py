from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import queue

# Currently using Queue, but should consider other data structures
threads = []
players = {}
actions = {}
TIMEOUT = 5

class Player:
    def __init__(self, name, lives=5, ammo=0):
        self.name = name
        self.ready = threading.Event()
        self.lives = lives
        self.ammo = ammo

    def __str__(self):
        return "Player " + str(self.name)

    def shoot(self):
        ammo = ammo - 1

    def get_hit(self):
        lives = lives - 1

    def wait(self):
        self.ready.wait()

    def clear(self):
        self.ready.clear()

    def set(self):
        self.ready.set()

def on_message_setup(client, userdata, msg):
    message = msg.payload.decode()
    print("Received for setup: " + message)
    players[message] = Player(message)
    actions[message] = queue.Queue()

def on_message(client, userdata, msg):
    message = msg.payload.decode().split('_')
    print("Received!")
    # print(message)
    actions[message[0]].put_nowait(message)
    players[message[0]].set()

def process_actions(name):
    player = players[name]
    q = actions[name]
    try:
        while True:
            item = q.get_nowait()

            # Process string here
            print(item)

            q.task_done()
    except queue.Empty:
        print("Finished processing " + name)

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.message_callback_add("ee180d/hp_shotgun/setup", on_message_setup)
    client.connect("broker.hivemq.com")
    client.subscribe("ee180d/hp_shotgun")
    client.subscribe("ee180d/hp_shotgun/setup")

    print("Listening...")
    client.loop_start()

    input("Please register all players...\n")

    round_num = 0
    while True:
        round_num += 1
        print("\nStarting round {0}".format(round_num))
        print("Waiting for input...")
        for name, player in players.items():
            player.wait()

        for name in players:
            t = threading.Thread(target=process_actions, args=[name])
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        for name, player in players.items():
            player.clear()

if __name__ == '__main__':
    main()
