from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import queue
import random
import json

players = {}
P_LOCK = threading.Event()
NUM_PLAYERS = 2


####################
##  Classes
####################

class Player:
    def __init__(self, name, lives=2, ammo=0, q_size=0):
        self.name = name
        self.lives = lives
        self.ammo = ammo
        self.defense = 0.75

        # Using a Queue here
        self.actions = queue.Queue(q_size)
        self.ready = threading.Event()

        # State variables
        self.is_hit = False
        self.is_blocking = False
        self.curr_acts = {}

    def __str__(self):
        return "Player {}".format(self.name)

    ####################
    ##  Game State functions
    ####################

    def status(self, console_output=False):
        if console_output:
            output = "{} : {} l, {} a, {} d".format(self.name, self.lives, self.ammo, self.defense)
            return output

        status = {}
        status["name"] = self.name
        status["lives"] = self.lives
        status["ammo"] = self.ammo
        status["defense"] = self.defense

        output = json.dumps(status)
        return output

    def is_dead(self):
        if self.lives <= 0:
            return True
        
        return False

    def run(self):
        if self.is_dead():
            return

        if Act.DIST in self.curr_acts:
            try:
                self.update_distance(self.curr_acts[Act.DIST])
            except ValueError:
                print("DIST message for {} had non-float value".format(self.name))

        if Act.BLOCK in self.curr_acts:
            self.block()
        elif Act.RELOAD in self.curr_acts:
            self.reload()
        elif Act.SHOOT in self.curr_acts:
            self.shoot()

        if Act.HIT in self.curr_acts:
            self.get_hit()
        if self.is_hit:
            if self.is_blocking and random.random() < self.defense:
                print("{} managed to avoid the shot!".format(self.name))
            else:
                print("{} took damage!".format(self.name))
                self.lives -= 1

        print(self.status(True))
        if self.is_dead():
            print("{} has died!".format(self.name))

    ####################
    ##  Player Actions
    ####################

    def reload(self):
        print("Action: {} reloaded!".format(self.name))
        self.ammo += 1

    def shoot(self):
        if self.ammo > 0:
            print("Action: {} shot his shot!".format(self.name))
            self.ammo -= 1
        else:
            print("Action: {} tried to shoot, but failed".format(self.name))

    def block(self):
        print("Action: {} tried to block!".format(self.name))
        self.is_blocking = True

    def get_hit(self):
        print("{} was shot at!".format(self.name))
        self.is_hit = True

    def update_distance(self, val_string):
        try:
            new_defense = float(val_string)
            self.defense = new_defense
            print("{}'s defense updated to {}".format(self.name, self.defense))
        except ValueError:
            print("DIST message for {} had non-float value".format(self.name))

    ####################
    ##  Event object wrapper functions
    ####################

    def wait_to_process(self):
        if self.is_dead():
            return
        self.ready.wait()

    def stop_processing(self):
        self.is_hit = False
        self.is_blocking = False
        self.curr_acts.clear()
        self.ready.clear()

    def start_processing(self):
        self.ready.set()

    def is_processing(self):
        return self.ready.isSet()


####################
##  MQTT callback functions
####################

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received unexpected message: " + message)

def on_message_setup(client, userdata, msg):
    message = msg.payload.decode()
    name = message

    if name in players:
        print("Player {} already set up".format(name))
        return
    if P_LOCK.isSet():
        print("Max number of players already registered")
        return

    print("Received for setup: " + name)
    players[name] = Player(name)

    if len(players) >= NUM_PLAYERS:
        P_LOCK.set()

def on_message_action(client, userdata, msg):
    message = msg.payload.decode()
    print("Received!")

    try:
        msg_list = message.split('_')

        name = msg_list[0]
        action = Act[msg_list[1]]
        value = msg_list[2]

        player = players[name]
    except (KeyError, IndexError):
        print("Unexpected message: {}".format(message))
        return

    if player.is_dead():
        return
    if player.is_processing():
        print("Player {}'s actions have already been chosen".format(name))
        return
    if action is Act.PASS:
        player.start_processing()
        return

    try:
        player.actions.put_nowait([action, value])
    except queue.Full:
        print("Extra action received for {}: {}".format(name, action))

    if player.actions.full():
        player.start_processing()


####################
##  Threaded function
####################

def process_actions(name, client):
    player = players[name]
    actions = player.actions
    try:
        while True:
            item = actions.get_nowait()

            print("Player {} with {}".format(name,item))
            player.curr_acts[item[0]] = item[1]

            actions.task_done()
    except queue.Empty:
        player.run()
        client.publish("ee180d/hp_shotgun/status", player.status())
        print("Finished processing " + name)


####################
##  Main function
####################

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.message_callback_add(TOPIC_ACTION, on_message_action)
    client.message_callback_add(TOPIC_SETUP, on_message_setup)
    client.connect("broker.hivemq.com")
    client.subscribe(TOPIC_GLOBAL)
    client.subscribe(TOPIC_ACTION)
    client.subscribe(TOPIC_SETUP)

    if len(sys.argv) == 2:
        global NUM_PLAYERS
        NUM_PLAYERS = int(sys.argv[1])

    print("Listening...")
    client.loop_start()

    print("Waiting to register {} players...\n".format(NUM_PLAYERS))
    P_LOCK.wait()

    round_num = 0
    while True:
        round_num += 1
        print("\nStarting round {0}".format(round_num))

        # Listen to players
        client.publish(TOPIC_PLAYER, "start_action")
        print("Waiting for input...")
        for name, player in players.items():
            player.wait_to_process()

        # Process received actions
        threads = []
        for name in players:
            t = threading.Thread(target=process_actions, args=[name, client])
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # Ask for distance data
        ### ADD DISTANCE DATA HERE ###

        # Check game state
        alive = [player for (name,player) in players.items() if not player.is_dead()]
        if len(alive) == 1:
            print("\nWINNER! {} has won the game!".format(alive[0]))
            break
        elif len(alive) <= 0:
            print("\nDRAW! There are no remaining players.")
            break

        # Prepare next round
        for name, player in players.items():
            player.stop_processing()

    client.publish(TOPIC_PLAYER, "stop_game")

if __name__ == '__main__':
    main()
