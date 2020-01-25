from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import queue

threads = []
players = {}
P_LOCK = threading.Event()
NUM_PLAYERS = 2

class Player:
    def __init__(self, name, lives=5, ammo=0):
        self.name = name
        self.lives = lives
        self.ammo = ammo
        self.defense = 0.5

        # Using a Queue here
        self.actions = queue.Queue()
        self.ready = threading.Event()

    def __str__(self):
        return "Player {} with lives: {} and ammo: {}".format(self.name, self.lives, self.ammo)

    def run(self, act_list):
        # TODO
        pass

    def reload(self):
        print("Action: Player {} reloaded!".format(self.name))
        ammo += 1

    def shoot(self):
        if self.ammo > 0:
            print("Action: Player {} shot his shot!".format(self.name))
            ammo -= 1
        else:
            print("Action: Player {} tried to shoot, but failed".format(self.name))

    def block(self):
        print("Action: Player {} blocked!".format(self.name))
        # TODO

    def get_hit(self):
        # TODO
        print("Action: Player {} was hit!".format(self.name))
        lives -= 1

        if (self.lives <= 0):
            # TODO
            pass

    def wait(self):
        self.ready.wait()

    def clear(self):
        self.ready.clear()

    def set(self):
        self.ready.set()

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received unexpected message: " + message)

def on_message_setup(client, userdata, msg):
    message = msg.payload.decode()
    if message in players:
        print("Player {} already set up".format(message))
        return
    elif P_LOCK.isSet():
        print("Max number of players already registered")
        return

    print("Received for setup: " + message)
    players[message] = Player(message)

    if len(players) >= NUM_PLAYERS:
        P_LOCK.set()

def on_message_action(client, userdata, msg):
    message = msg.payload.decode()
    print("Received!")

    msg_list = message.split('_')
    if msg_list[0] not in players or len(msg_list) != 3:
        print("Unexpected message: {}".format(message))
        return

    name = msg_list[0]
    action = Act[msg_list[1]]
    target = msg_list[2]

    if action is Act.PASS:
        players[name].set()
        return

    players[name].actions.put_nowait([action, target])

def process_actions(name):
    player = players[name]
    q = player.actions
    try:
        while True:
            item = q.get_nowait()

            # TODO: Compile actions here
            print("Player {} with {}".format(name,item))

            q.task_done()
    except queue.Empty:
        # TODO: Call Player.run() here
        print("Finished processing " + name)

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.message_callback_add("ee180d/hp_shotgun/action", on_message_action)
    client.message_callback_add("ee180d/hp_shotgun/setup", on_message_setup)
    client.connect("broker.hivemq.com")
    client.subscribe("ee180d/hp_shotgun")
    client.subscribe("ee180d/hp_shotgun/action")
    client.subscribe("ee180d/hp_shotgun/setup")

    if len(sys.argv) == 2:
        global NUM_PLAYERS
        NUM_PLAYERS = int(sys.argv[1])

    print("Listening...")
    client.loop_start()

    print("Waiting to register all {} players...\n".format(NUM_PLAYERS))
    P_LOCK.wait()

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
