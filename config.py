from enum import Enum


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
SIGFIG = 1

# Standard Messages
DIST = "START_DIST"
ACTION = "START_ACTION"
VOICE = "START_VOICE"

STOP_GAME = "STOP_GAME"
STATUS = "STATUS"
ACTION_COUNT = "ACTION_COUNT"
HIT = "GOT_HIT"
DISPLAY = "DISPLAY"

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
