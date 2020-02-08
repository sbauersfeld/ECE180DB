from enum import Enum

class Act(Enum):
    PASS = 0
    RELOAD = 1
    SHOOT = 2
    BLOCK = 3
    HIT = 4
    DIST = 5

TOPIC_GLOBAL = "ee180d/hp_shotgun"
TOPIC_SETUP = TOPIC_GLOBAL + "/setup" # For registering players and laptops to server
TOPIC_PLAYER = TOPIC_GLOBAL + "/player" # For notifying players to start and action; server to player
TOPIC_STATUS = TOPIC_GLOBAL + "/status" # For updating laptops on the state of the game; server to laptop
TOPIC_ACTION = TOPIC_GLOBAL + "/action" # For actions done by players; player to server
