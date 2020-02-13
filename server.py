from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import json


####################
##  Global Variables
####################

players = {}
P_LOCK = threading.Event()
NUM_PLAYERS = 2
client = mqtt.Client()


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
        self.is_hit = False
        self.next_act = None

        # Action handling
        self.process = {
            Act.RELOAD : self.reload,
            Act.SHOOT : self.shoot,
            Act.BLOCK : self.block,
        }

        # Synchronization
        self.action_ready = threading.Event()
        self.distance_ready = threading.Event()

    def __str__(self):
        return "Player {}".format(self.name)

    ####################
    ##  Game State functions
    ####################

    def status(self, console_output=False):
        if console_output:
            output = "{} : {} l, {} a, {} d".format(self.name, self.lives, self.ammo, self.defense)
            return output

        status = {
            "name" : self.name,
            "lives" : self.lives,
            "ammo" : self.ammo,
            "defense" : self.defense,
        }

        output = SEP.join(["STATUS", json.dumps(status)])
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

        self.process.get(self.next_act, self.block)()
        if self.is_hit:
            self.get_hit()

        self.clear()
        print(self.status(True))
        if self.is_dead():
            print("{} has died!".format(self.name))

    def clear(self):
        self.is_blocking = False
        self.is_hit = False
        self.next_act = None

    ####################
    ##  Player Actions
    ####################

    def reload(self):
        print("ACTION: {} reloaded!".format(self.name))
        self.ammo = round(self.ammo + 25, 1)

    def shoot(self):
        required_ammo = self.defense
        if self.can_shoot():
            print("ACTION: {} shot his shot!".format(self.name))
            self.ammo = round(self.ammo - required_ammo, 1)
        else:
            print("ACTION: {} tried to shoot, but failed".format(self.name))

    def block(self):
        print("ACTION: {} blocked!".format(self.name))
        self.is_blocking = True

    def get_hit(self):
        if self.is_blocking:
            print("{} was shot but blocked it!".format(self.name))
        else:
            print("{} was shot and took damage!".format(self.name))
            self.lives = round(self.lives - (80.0 - self.defense), 1)

    ####################
    ##  Player Modifiers
    ####################

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

    def update_action(self, action):
        self.next_act = action

    def update_as_hit(self, was_hit=True):
        self.is_hit = was_hit

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
        self.distance_ready.wait()

    def listen_for_distance(self):
        self.distance_ready.clear()

    def finish_for_distance(self):
        self.distance_ready.set()

    def is_listening_to_distance(self):
        return not self.distance_ready.isSet()


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
        msg_list = message.split(SEP)

        name = msg_list[0]
        action = Act[msg_list[1]]
        value = msg_list[2]

        player = players[name]
    except (KeyError, IndexError):
        print("Unexpected message: {}".format(message))
        return

    if player.is_dead():
        return

    if player.is_listening_to_distance():
        process_distance(player, action, value)

    if player.is_listening_to_action():
        process_action(player, action, value)

####################
##  Functions
####################

def request_distance():
    for name, player in players.items():
        player.listen_for_distance()

    client.publish(TOPIC_LAPTOP, START_DIST)

    print("Waiting for distances...")
    for name, player in players.items():
        player.wait_for_distance()

def process_distance(player, action, value):
    if action in [Act.DIST]:
        player.update_distance(value)
        client.publish(TOPIC_LAPTOP, player.status())
        player.finish_for_distance()

def request_action():
    countdown = 3
    while countdown > 0:
        client.publish(TOPIC_LAPTOP, SEP.join(["COUNT",str(countdown)]))
        print("Do action in {}...".format(countdown))
        countdown -= 1
        time.sleep(1)

    for name, player in players.items():
        player.listen_for_actions()

    client.publish(TOPIC_PLAYER, START_ACTION)

    print("Waiting for actions...")
    for name, player in players.items():
        player.wait_for_actions()

def process_action(player, action, value):
    if action in [Act.RELOAD, Act.SHOOT, Act.BLOCK]:
        player.update_action(action)

    ### Addition just for demos, but can be used for a burst/grenade option ###
    if action in [Act.SHOOT] and player.can_shoot():
        for n, p in players.items():
            if p is player:
                continue
            p.update_as_hit()

    if action in [Act.PASS, Act.HIT]:
        if action in [Act.HIT]:
            player.update_as_hit()
        player.finish_for_actions()

def process_round(name):
    player = players[name]
    player.run()
    client.publish(TOPIC_LAPTOP, player.status())
    print("Finished processing " + name)


####################
##  Main function
####################

def main():
    client.on_message = on_message
    client.message_callback_add(TOPIC_SETUP, on_message_setup)
    client.connect("broker.hivemq.com")
    client.subscribe(TOPIC_GLOBAL)
    client.subscribe(TOPIC_SETUP)

    if len(sys.argv) == 2:
        global NUM_PLAYERS
        NUM_PLAYERS = int(sys.argv[1])

    print("Listening...")
    client.loop_start()

    print("Waiting to register {} players...\n".format(NUM_PLAYERS))
    P_LOCK.wait()
    client.subscribe(TOPIC_ACTION)
    client.message_callback_add(TOPIC_ACTION, on_message_action)

    round_num = 0
    while True:
        # Start new round
        ### SPEECH DETECTION STUFF HERE ###
        input("Press Enter to continue...")

        round_num += 1
        print("\nStarting round {0}".format(round_num))

        # Ask for distance data
        request_distance()

        # Ask for player actions
        request_action()

        # Process received actions
        threads = []
        for name in players:
            t = threading.Thread(target=process_round, args=[name])
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
    time.sleep(1)

if __name__ == '__main__':
    main()
