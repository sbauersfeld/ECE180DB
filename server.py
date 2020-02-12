from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import queue
import json


####################
##  Global Variables
####################

players = {}
P_LOCK = threading.Event()
NUM_PLAYERS = 2


####################
##  Classes
####################

class Player:
    def __init__(self, name, lives=150.0, ammo=0.0, q_size=0):
        self.name = name
        self.lives = lives
        self.ammo = ammo
        self.defense = 25.0

        # Variables
        self.is_blocking = False
        self.curr_acts = {}
        self.actions = queue.Queue(q_size)

        # Synchronization
        self.action_ready = threading.Event()
        self.listen_ready = threading.Event()

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

    def can_shoot(self):
        required_ammo = self.defense
        if self.ammo >= required_ammo:
            return True
        
        return False

    def run(self):
        if self.is_dead():
            return

        if not self.curr_acts:
            print("No actions taken by player {}".format(self.name))
        elif Act.BLOCK in self.curr_acts:
            self.block()
        elif Act.RELOAD in self.curr_acts:
            self.reload()
        elif Act.SHOOT in self.curr_acts:
            self.shoot()

        if Act.HIT in self.curr_acts:
            self.get_hit()

        self.clear()
        print(self.status(True))
        if self.is_dead():
            print("{} has died!".format(self.name))

    def clear(self):
        self.is_blocking = False
        self.curr_acts.clear()

    ####################
    ##  Player Actions
    ####################

    def reload(self):
        print("Action: {} reloaded!".format(self.name))
        self.ammo += 25

    def shoot(self):
        required_ammo = self.defense
        if self.can_shoot():
            print("Action: {} shot his shot!".format(self.name))
            self.ammo -= required_ammo
        else:
            print("Action: {} tried to shoot, but failed".format(self.name))

    def block(self):
        print("Action: {} tried to block!".format(self.name))
        self.is_blocking = True

    def get_hit(self):
        print("{} was shot at!".format(self.name))
        if self.is_blocking:
            print("{} managed to avoid the shot!".format(self.name))
        else:
            print("{} took damage!".format(self.name))
            self.lives -= (80.0 - self.defense)

    def update_distance(self, val_string):
        try:
            new_defense = float(val_string)
            if new_defense > 50.0:
                new_defense = 50.0
            elif new_defense < 10.0:
                new_defense = 10.0

            self.defense = new_defense
            print("{}'s defense updated to {}".format(self.name, self.defense))
        except ValueError:
            print("DIST message for {} had non-float value".format(self.name))

    ####################
    ##  Wrapper functions
    ####################

    def wait_for_actions(self):
        if self.is_dead():
            return
        self.action_ready.wait()

    def listen_for_actions(self):
        self.action_ready.clear()

    def finish_for_actions(self):
        self.action_ready.set()

    def is_listening_to_action(self):
        return not self.action_ready.isSet()

    def wait_for_distance(self):
        if self.is_dead():
            return
        self.listen_ready.wait()

    def listen_for_distance(self):
        self.listen_ready.clear()

    def finish_for_distance(self):
        self.listen_ready.set()

    def is_listening_to_distance(self):
        return not self.listen_ready.isSet()


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
        print("All players already registered")
        return

    print("Received for setup: " + name)
    players[name] = Player(name)

    if len(players) >= NUM_PLAYERS:
        P_LOCK.set()

def on_message_action(client, userdata, msg):
    message = msg.payload.decode()
    print("Action received!")

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

    if action in [Act.RELOAD, Act.SHOOT, Act.BLOCK, Act.HIT]:
        if player.is_listening_to_action():
            try:
                player.actions.put_nowait([action, value])
            except queue.Full:
                print("Extra action received for {}: {}".format(name, action))
        else:
            print("Player {}'s actions already chosen".format(name))

    ### Addition just for demos ###
    # Can be used for a burst/grenade option
    ### NOTE: in the case of multiple actions being registered for some reason
    ###       this assume you always shot, even if the actual action according
    ###       to priority would be any other action
    if action in [Act.SHOOT] and player.can_shoot():
        for n, p in players.items():
            if p is player:
                continue
            try:
                p.actions.put_nowait([Act.HIT, ""])
            except queue.Full:
                print("Error while processing shoot for {}".format(name))

    if action in [Act.DIST]:
        if player.is_listening_to_distance():
            player.update_distance(value)
            client.publish(TOPIC_LAPTOP, player.status())
            player.finish_for_distance()
        else:
            print("Player {}'s distance already chosen".format(name))

    if action in [Act.PASS, Act.HIT] or player.actions.full():
        player.finish_for_actions()


####################
##  Functions
####################

def request_distance(client):
    for name, player in players.items():
        player.listen_for_distance()

    client.publish(TOPIC_LAPTOP, START_DIST)

    print("Waiting for distances...")
    for name, player in players.items():
        player.wait_for_distance()

def request_action(client):
    remaining_time = 3
    while remaining_time > 0:
        client.publish(TOPIC_LAPTOP, "doAction_{}".format(remaining_time))
        print("Do action in {}...".format(remaining_time))
        remaining_time -= 1
        time.sleep(1)

    for name, player in players.items():
        player.listen_for_actions()

    client.publish(TOPIC_PLAYER, START_ACTION)

    print("Waiting for actions...")
    for name, player in players.items():
        player.wait_for_actions()

def process_actions(client, name):
    player = players[name]
    actions = player.actions
    try:
        while True:
            item = actions.get_nowait()

            print("Player {} with {}".format(name,item))
            player.curr_acts[item[0]] = item[1]
            ### Figure out better action processing here ###

            actions.task_done()
    except queue.Empty:
        player.run()
        client.publish(TOPIC_LAPTOP, player.status())
        print("Finished processing " + name)


####################
##  Main function
####################

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.message_callback_add(TOPIC_SETUP, on_message_setup)
    client.message_callback_add(TOPIC_ACTION, on_message_action)
    client.connect("broker.hivemq.com")
    client.subscribe(TOPIC_GLOBAL)
    client.subscribe(TOPIC_SETUP)
    client.subscribe(TOPIC_ACTION)

    if len(sys.argv) == 2:
        global NUM_PLAYERS
        NUM_PLAYERS = int(sys.argv[1])

    print("Listening...")
    client.loop_start()

    print("Waiting to register {} players...\n".format(NUM_PLAYERS))
    P_LOCK.wait()

    round_num = 0
    while True:
        # Start new round
        ### SPEECH DETECTION STUFF HERE ###
        input("Press Enter to continue...")

        round_num += 1
        print("\nStarting round {0}".format(round_num))

        # Ask for distance data
        request_distance(client)

        # Ask for player actions
        request_action(client)

        # Process received actions
        threads = []
        for name in players:
            t = threading.Thread(target=process_actions, args=[client, name])
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # Check game state
        alive = [player for (name,player) in players.items() if not player.is_dead()]
        if len(alive) == 1:
            print("\nWINNER! {} has won the game!".format(alive[0]))
            break
        elif len(alive) <= 0:
            print("\nDRAW! There are no remaining players.")
            break

        ### Players should move to their preferred distance here ###
        print("Move to a new distance before starting next round!")

    # End Game
    client.publish(TOPIC_PLAYER, STOP_GAME)

if __name__ == '__main__':
    main()
