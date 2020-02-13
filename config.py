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

# Standard Messages
START_ACTION = "START_ACTION"
START_DIST = "START_DIST"
START_HIT = "START_HIT"
STOP_GAME = "STOP_GAME"


####################
##  Classes
####################

class Act(Enum):
    PASS = 0
    RELOAD = 1
    SHOOT = 2
    BLOCK = 3
    HIT = 4
    DIST = 5
