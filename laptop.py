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


####################
##  Classes
####################

class Player:
    def __init__(self, name="", lives=150.0, ammo=0.0):
        # Variables
        self.name = name
        self.lives = lives
        self.ammo = ammo
        self.defense = "?"
        self.msg = ""

class Status(pygame.sprite.Sprite):
    def __init__(self, value=0, title=False, xpos=0, ypos=0, xval=None, yval=None):
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

    def update(self, new_val):
        self.value = new_val


####################
##  Global Variables
####################

### GameStuff ###
GAME_OVER = False
D_LOCK = threading.Event()
PLAYER = Player()
client = mqtt.Client()

### Pygame ###
pygame.init()
clock = pygame.time.Clock()

### Creating the main surface ###
WIDTH = 1280
HEIGHT = 780
main_surface = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
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
    print("Player: " + message)

    if message == START_ACTION:
        PLAYER.msg = "NOW"
    elif message == STOP_GAME:
        global GAME_OVER
        GAME_OVER = True
        D_LOCK.set()


####################
##  Functions
####################

def send_action(name, action, value=""):
    message = SEP.join([name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret

def detect_distance(name):
    cap = cv2.VideoCapture(0)

    print("Waiting to detect distance...")
    D_LOCK.wait()
    while not GAME_OVER:
        new_val = GetDistance(cap)
        dist = str(round(new_val, 1))
        send_action(name, Act.DIST, dist)

        if not GAME_OVER:
            D_LOCK.clear()
        D_LOCK.wait()

    cap.release()
    cv2.destroyAllWindows()

def process_order(order, value1, value2):
    if order == START_DIST:
        msg = "Measuring distance..."
        PLAYER.msg = msg
        print(msg)
        D_LOCK.set()

    elif order == PLAYER.name:
        action = Act[value1]
        print("Received action: {}".format(action))
        if action in [Act.RELOAD, Act.BLOCK, Act.SHOOT]:
            PLAYER.msg = action.name

    elif order == ACTION_COUNT:
        msg = "action in {}".format(value1)
        PLAYER.msg = msg
        print(msg)

    elif order == MOVE_NOW:
        msg = "Move to new distance..."
        PLAYER.msg = msg
        PLAYER.defense = "?"
        print(msg)

    elif order == STATUS:
        status = json.loads(value1)
        print(status)

        if status["name"] == PLAYER.name:
            PLAYER.ammo = status["ammo"]
            PLAYER.lives = status["lives"]
            PLAYER.defense = status["defense"]
    
    else:
        print("Unexpected message! {}".format(order))


####################
##  Pygame Functions
####################

def draw_main():
    main_surface.fill(BLACK)

    player_name = Status(PLAYER.name, ypos=-250)
    ammo = Status(PLAYER.ammo, xpos=-400, ypos=-0)
    lives = Status(PLAYER.lives, ypos=-0)
    defense = Status(PLAYER.defense, xpos=400, ypos=-0)
    action = Status(PLAYER.msg, ypos=250)

    ammo_label = Status("ammo", True, xpos=-400, ypos=-75)
    lives_label = Status("health", True, ypos=-75)
    defense_label = Status("defense", True, xpos=400, ypos=-75)

    all_sprites = pygame.sprite.RenderPlain(player_name, ammo, lives, defense, action, ammo_label, lives_label, defense_label)
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
        name = sys.argv[1]
    else:
        name = input("Please enter your name: ")
    PLAYER.name = name

    print("Listening...")
    client.loop_start()

    ### Handle connection with player ###

    threads = []
    for func in [detect_distance]:
        t = threading.Thread(target=func, args=[name], daemon=True)
        t.start()
        threads.append(t)

    client.publish(TOPIC_SETUP, name)


    ####################
    ##  Start Game
    ####################

    time.sleep(1.5)
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
