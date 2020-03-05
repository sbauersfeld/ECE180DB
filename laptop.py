from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import json
import pygame
from pygame.locals import *
import numpy as np
import cv2
import imutils
from range_detection.range_detection import GetDistance
from speech_detection.speech_detection import speech_setup, get_speech


####################
##  Classes
####################

class Player:
    def __init__(self, name="", lives=150.0, ammo=0.0):
        # Status
        self.name = name
        self.lives = lives
        self.ammo = ammo
        self.defense = "?"

        # Display
        self.top = name
        self.bottom = ""
        self.temp_def = "?"

    def update_name(self, new_name):
        self.name = new_name
        self.top = new_name

    def update_top(self, new_msg):
        self.top = new_msg
        print("TOP: {}".format(new_msg))

    def update_bottom(self, new_msg):
        self.bottom = new_msg
        print("BOTTOM: {}".format(new_msg))

    def update_temp_def(self, new_def):
        self.temp_def = new_def
        self.update_bottom(new_def)

class Status(pygame.sprite.Sprite):
    def __init__(self, value="?", title=False, xpos=0, ypos=0, xval=None, yval=None):
        ### Status information ###
        self.value = str(value)

        ### Creating the object ###
        pygame.sprite.Sprite.__init__(self)
        font = font_small if title else font_large
        self.image = font.render(self.value, True, WHITE, BLACK)
        self.rect = self.image.get_rect()

        ### Establishing the location ###
        self.rect.centerx = main_origin.centerx if not xval else xval
        self.rect.centery = main_origin.centery if not yval else yval
        self.rect.centerx += xpos
        self.rect.centery += ypos


####################
##  Global Variables
####################

### GameStuff ###
GAME_OVER = False
D_LOCK = threading.Event()
V_LOCK = threading.Event()
PLAYER = Player()
client = mqtt.Client()

### Voice ###
start_phrase = ["start", "starch", "sparks", "fart", "darts", "spikes",
                "search", "bikes", "strikes", "starks"]
headset_map = {
    "scott" : "Headset (SoundBuds Slim Hands-F",
    "jon" : "SP620",
}

### Pygame ###
pygame.init()
clock = pygame.time.Clock()

### Creating the main surface ###
WIDTH = 0 # 1280
HEIGHT = 0 # 780
main_surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN) # Or FULLSCREEN
main_origin = main_surface.get_rect()

### Music ###
pygame.mixer.music.load("music/Nimbus2000.ogg")
sound_effect = pygame.mixer.Sound("music/SoundEffect.ogg")

### Misc ###
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
font_large = pygame.font.SysFont("Helvetica", 150)
font_big = pygame.font.SysFont("Helvetica", 72)
font_small = pygame.font.SysFont("Helvetica", 50)


####################
##  MQTT callback functions
####################

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received unexpected message: " + message)

def on_message_laptop(client, userdata, msg):
    message = msg.payload.decode()

    try:
        msg_list = message.split(SEP)
        order = msg_list[0]
        value1 = msg_list[1]
        value2 = msg_list[2]
    except (IndexError):
        print("Unexpected message: {}".format(message))
        return

    process_order(order, value1, value2)

def on_message_player(client, userdata, msg):
    message = msg.payload.decode()

    if message == ACTION:
        PLAYER.update_bottom("NOW")

    if message == STOP_GAME:
        global GAME_OVER
        GAME_OVER = True
        D_LOCK.set()
        V_LOCK.set()


####################
##  Functions
####################

def send_action(action, value=""):
    message = SEP.join([PLAYER.name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret

def process_order(order, value1, value2):
    if order == DIST:
        print()
        PLAYER.update_top("Move to new distance!")
        D_LOCK.set()

    if order == VOICE:
        PLAYER.update_bottom("Say 'start' to continue...")
        V_LOCK.set()

    if order == ACTION_COUNT:
        PLAYER.update_bottom("action in {}".format(value1))

    if order == PLAYER.name:
        process_order_individual(value1, value2)

    if order == STATUS:
        status = json.loads(value1)
        print(status)

        if status["name"] == PLAYER.name:
            PLAYER.ammo = status["ammo"]
            PLAYER.lives = status["lives"]
            PLAYER.defense = status["defense"]

    if order == DISPLAY:
        PLAYER.update_bottom(value1)

def process_order_individual(value1, value2):
    if value1 == HIT:
        PLAYER.update_top("YOU GOT HIT")

    try:
        action = Act[value1]
        print("Received action: {}".format(action))
        if action in [Act.RELOAD, Act.BLOCK, Act.SHOOT]:
            PLAYER.update_bottom(action.name)
    except KeyError:
        pass

####################
##  Threads
####################

def detect_distance(headset):
    cap = cv2.VideoCapture(0)
    microphone = speech_setup(headset)

    print("Range detection active!")
    D_LOCK.wait()
    while not GAME_OVER:
        timer = threading.Timer(5, detect_voice_start, [microphone])
        timer.start()
        
        while timer.isAlive():
            new_val = GetDistance(cap, PLAYER.name, 0.6)
            PLAYER.update_temp_def(str(round(new_val, 1)))

        PLAYER.update_top("Voice registered")
        send_action(Act.DIST, PLAYER.temp_def)

        if not GAME_OVER:
            D_LOCK.clear()
        D_LOCK.wait()

    cap.release()
    cv2.destroyAllWindows()

def detect_voice(headset):
    microphone = speech_setup(headset)

    print("Speech detection active!")
    V_LOCK.wait()
    while not GAME_OVER:
        get_speech(microphone, start_phrase)

        PLAYER.update_bottom("Voice registered")
        send_action(Act.VOICE)

        if not GAME_OVER:
            V_LOCK.clear()
        V_LOCK.wait()

def detect_voice_start(microphone):
    PLAYER.update_top("Say 'start' to continue!")
    get_speech(microphone, start_phrase)


####################
##  Pygame Functions
####################

def draw_main():
    main_surface.fill(BLACK)

    top = Status(PLAYER.top, ypos=-275)
    bottom = Status(PLAYER.bottom, ypos=250)

    ammo = Status(PLAYER.ammo, xpos=-400, ypos=-0)
    lives = Status(PLAYER.lives, ypos=-0)
    defense = Status(PLAYER.defense, xpos=400, ypos=-0)

    l_ammo = Status("ammo", True, xpos=-400, ypos=-75)
    l_lives = Status("health", True, ypos=-75)
    l_defense = Status("defense", True, xpos=400, ypos=-75)

    all_sprites = pygame.sprite.RenderPlain(top, bottom, ammo, lives, defense, l_ammo, l_lives, l_defense)
    all_sprites.draw(main_surface)


####################
##  Main function
####################

def main():
    client.on_message = on_message
    client.message_callback_add(TOPIC_LAPTOP, on_message_laptop)
    client.message_callback_add(TOPIC_PLAYER, on_message_player)
    client.connect("broker.hivemq.com")
    client.subscribe(TOPIC_GLOBAL)
    client.subscribe(TOPIC_LAPTOP)
    client.subscribe(TOPIC_PLAYER)

    if len(sys.argv) == 2:
        time.sleep(0.25)
        name = sys.argv[1].lower()
    else:
        name = input("Please enter your name: ")
    PLAYER.update_name(name)
    headset = headset_map.get(name, "scott")

    print("Listening...")
    client.loop_start()

    ### Handle connection with player ###

    threads = []
    t_args = {
        detect_distance : [headset],
        # detect_voice : [headset],
    }
    for func, args in t_args.items():
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()
        threads.append(t)

    client.publish(TOPIC_SETUP, name)
    ### Have laptop repeatedly send this and wait for ACK from server ###


    ####################
    ##  Start Game
    ####################

    # pygame.mixer.music.play(-1, 0.5)

    player_win = False
    global GAME_OVER
    while not GAME_OVER:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                GAME_OVER = True
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                GAME_OVER = True
                player_win = True

        # Visuals
        draw_main()
        
        pygame.display.update()
        clock.tick(12)


    ####################
    ##  End Game
    ####################

    pygame.mixer.music.load("music/LeavingHogwarts.ogg")
    # pygame.mixer.music.play(-1, 0.5)

    # Visuals
    print("Finished game!")
    game_over = font_big.render("GAME OVER", True, WHITE, BLACK)
    g_o_rect = game_over.get_rect()
    g_o_rect.centerx = main_origin.centerx
    g_o_rect.centery = main_origin.centery - 50

    if player_win:
        winner = font_small.render("Player Wins!", True, WHITE, BLACK)
        win_rect = winner.get_rect()
        win_rect.centerx = g_o_rect.centerx
        win_rect.centery = g_o_rect.centery + 75

    main_surface.fill(BLACK)
    main_surface.blit(game_over, g_o_rect)
    if player_win:
        main_surface.blit(winner, win_rect)

    done = False
    while not done:
        # Quit conditions
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                done = True

        # Visuals
        pygame.display.update()

    pygame.quit()


if __name__ == '__main__':
    main()
