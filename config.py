from enum import Enum
import trace
import threading
import sys


####################
##  Global Variables
####################

# Topics
TOPIC_GLOBAL = "ee180d/hp_shotgun"
TOPIC_SETUP = TOPIC_GLOBAL + "/setup" # For registering players and laptops to server
TOPIC_PLAYER = TOPIC_GLOBAL + "/player" # For notifying players to start and action; server to player
TOPIC_LAPTOP = TOPIC_GLOBAL + "/laptop" # For updating laptops on the state of the game; server to laptop
TOPIC_ACTION = TOPIC_GLOBAL + "/action" # For actions done by players; player to server

# Variables
SEP = "___"
SIGFIG = None

# Game Labels
AMMO = "energy"
LIVES = "health"
DEFENSE = "distance"

# Game Variables
LIVES_MAX = round(150.0, SIGFIG)
DAMAGE_MAX = round(100.0, SIGFIG)
DIST_MAX = round(100.0, SIGFIG)
DIST_MIN = round(0.0, SIGFIG)
AMMO_RELOAD = round(50.0, SIGFIG)

# Phases
DIST = "START_DIST"
ACTION = "START_ACTION"
VOICE = "START_VOICE"

# Other Messages
ACTION_COUNT = "ACTION_COUNT"
HIT = "GOT_HIT"
STATUS = "STATUS"
DISPLAY = "DISPLAY"
STOP_GAME = "STOP_GAME"


####################
##  Classes
####################

class Act(Enum):
    PASS = 0
    RELOAD = 1
    SHOOT = 2
    BLOCK = 3
    DIST = 4
    VOICE = 5

class Text(Enum):
	NUM = 0
	TEXT = 1
	ENEMY = 2
	LABEL = 3
	TUTORIAL = 4

class thread_with_trace(threading.Thread): 
    def __init__(self, *args, **keywords): 
        threading.Thread.__init__(self, *args, **keywords) 
        self.killed = False

    def start(self): 
        self.__run_backup = self.run 
        self.run = self.__run       
        threading.Thread.start(self) 

    def __run(self): 
        sys.settrace(self.globaltrace) 
        self.__run_backup() 
        self.run = self.__run_backup 

    def globaltrace(self, frame, event, arg): 
        if event == 'call': 
            return self.localtrace 
        else: 
            return None

    def localtrace(self, frame, event, arg): 
        if self.killed: 
            if event == 'line': 
                raise SystemExit() 
        return self.localtrace 
  
    def kill(self): 
        self.killed = True
