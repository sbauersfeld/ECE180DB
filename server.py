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
NUM_PLAYERS = 2
P_LOCK = threading.Event()
client = mqtt.Client()


####################
##  Classes
####################

class Player:
    def __init__(self, name, lives=LIVES_MAX, ammo=AMMO_RELOAD):
        self.name = name
        self.lives = lives
        self.ammo = ammo
        self.defense = AMMO_RELOAD

        # Variables
        self.is_blocking = False
        self.is_hit = False
        self.next_act = None
        self.damage = 0

        # Action handling
        self.process = {
            Act.RELOAD : self.reload,
            Act.SHOOT : self.shoot,
            Act.BLOCK : self.block,
        }

        # Synchronization
        self.sync = {
            DIST : threading.Event(),
            ACTION : threading.Event(),
            VOICE : threading.Event(),
        }

    def __str__(self):
        return "Player {}".format(self.name)

    ####################
    ##  Game State functions
    ####################

    def status(self, console_output=False, starting_round=False):
        if console_output:
            output = "{} : {} a, {} l, {} d".format(self.name, self.ammo, self.lives, self.defense)
            return output

        temp_defense = self.defense
        if starting_round:
            temp_defense = "?"

        status = {
            "name" : self.name,
            LIVES : self.lives,
            AMMO : self.ammo,
            DEFENSE : temp_defense,
        }

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
        self.damage = 0

    ####################
    ##  Player Actions
    ####################

    def reload(self):
        print("ACTION: {} reloaded!".format(self.name))
        self.ammo = round(self.ammo + AMMO_RELOAD, SIGFIG)

    def shoot(self):
        required_ammo = self.defense
        if self.can_shoot():
            print("ACTION: {} shot his shot!".format(self.name))
            self.ammo = round(self.ammo - required_ammo, SIGFIG)
        else:
            print("ACTION: {} tried to shoot, but failed".format(self.name))
            send_to_laptop(self.name, "Not enough {}".format(AMMO))

    def block(self):
        print("ACTION: {} blocked!".format(self.name))
        self.is_blocking = True

    def get_hit(self):
        if self.is_blocking:
            print("HIT: {} was shot but blocked it!".format(self.name))
        else:
            print("HIT: {} was shot and took damage!".format(self.name))
            new_lives = self.lives - max(self.damage - self.defense, 0)
            self.lives = round(max(new_lives, 0), SIGFIG)
            send_to_player(self.name, HIT)

    ####################
    ##  Player Modifiers
    ####################

    def update_distance(self, val_string):
        try:
            new_defense = round(float(val_string), SIGFIG)
            self.defense = min(max(new_defense, DIST_MIN), DIST_MAX)
            print("{}'s defense updated to {}".format(self.name, self.defense))
        except ValueError:
            print("DIST message for {} had non-float value".format(self.name))

    def update_action(self, action):
        self.next_act = action

    def update_as_hit(self, value, was_hit=True):
        self.is_hit = was_hit
        self.damage = max(DAMAGE_MAX-value, 0)

    ####################
    ##  Wrapper functions
    ####################

    def wait_for(self, val, TIMEOUT=None):
        if self.is_dead():
            return
        self.sync[val].wait(TIMEOUT)

    def listen_for(self, val):
        self.sync[val].clear()

    def finish_for(self, val):
        self.sync[val].set()

    def is_listening_to(self, val):
        return not self.sync[val].isSet()


####################
##  MQTT Functions
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

    try:
        msg_list = message.split(SEP)

        name = msg_list[0]
        action = Act[msg_list[1]]
        value = msg_list[2]

        player = players[name]
    except (KeyError, IndexError):
        print("Unexpected message: {}".format(message))
        return

    process_response(player, action, value)

def send_to_laptop(order, value1="", value2=""):
    message = SEP.join([order, value1, value2])
    ret = client.publish(TOPIC_LAPTOP, message)
    return ret

def send_to_player(order, value1="", value2=""):
    message = SEP.join([order, value1, value2])
    ret = client.publish(TOPIC_PLAYER, message)
    return ret


####################
##  Process Messages
####################

def process_response(player, action, value):
    if player.is_dead():
        return
    print("Received for {}: {} {}".format(player.name, action, value))

    if action in [Act.DIST] and player.is_listening_to(DIST):
        player.update_distance(value)
        send_to_laptop(STATUS, player.status())
        player.finish_for(DIST)

    if action in [Act.RELOAD, Act.SHOOT, Act.BLOCK] and player.is_listening_to(ACTION):
        player.update_action(action)
        send_to_laptop(player.name, action.name)

        ### Addition just for demos, but can be used for a burst/grenade option ###
        if action in [Act.SHOOT] and player.can_shoot():
            for n, p in players.items():
                if p is player:
                    continue
                p.update_as_hit(player.defense)
        player.finish_for(ACTION)

    if action in [Act.VOICE] and player.is_listening_to(VOICE):
        player.finish_for(VOICE)

def process_round(name):
    player = players[name]
    player.run()
    send_to_laptop(STATUS, player.status())
    print("Finished processing " + name)


####################
##  Functions
####################

def count_laptop(order, countdown, freq=1):
    while countdown > 0:
        send_to_laptop(order, str(countdown))
        print("Do {} in {}...".format(order, countdown))
        countdown -= freq
        time.sleep(freq)

def request_for(command):
    for name, player in players.items():
        player.listen_for(command)

    if command in [ACTION]:
        send_to_player(command)
    else:
        send_to_laptop(command)

    print("Waiting for {}...".format(command))
    for name, player in players.items():
        player.wait_for(command)


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


    ####################
    ##  Tutorial
    ####################

    print("Waiting to register {} players...\n".format(NUM_PLAYERS))
    P_LOCK.wait()
    client.subscribe(TOPIC_ACTION)
    client.message_callback_add(TOPIC_ACTION, on_message_action)


    ####################
    ##  Start Game
    ####################

    round_num = 0
    winner = ""
    while True:
        # Start new round
        for name, player in players.items():
            send_to_laptop(STATUS, player.status(starting_round=True))
        send_to_player(DIST)
        round_num += 1
        print("\nStarting round {0}".format(round_num))
        time.sleep(0.5) # For the "Voice registered" message

        # Ask for distance data
        request_for(DIST)

        # Ask for player actions
        count_laptop(ACTION_COUNT, 3)
        request_for(ACTION)

        # Process received actions
        threads = []
        for name in players:
            t = threading.Thread(target=process_round, args=[name])
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # Give time to process round
        time.sleep(3)

        # Check game state
        alive = [player for (name,player) in players.items() if not player.is_dead()]
        if len(alive) == 1 and NUM_PLAYERS > 1:
            print("\nWINNER! {} has won the game!".format(alive[0]))
            winner = alive[0].name
            break
        if len(alive) <= 0:
            print("\nDRAW! There are no remaining players.")
            winner = "Nobody"
            break


    ####################
    ##  End Game
    ####################

    # End Game
    send_to_player(STOP_GAME, winner)
    time.sleep(2)

if __name__ == '__main__':
    main()
