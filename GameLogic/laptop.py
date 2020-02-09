from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import pygame
from pygame.locals import *


####################
##  Global Variables
####################

### Pygame ###
pygame.init()
clock = pygame.time.Clock()

### Creating the main surface ###
WIDTH = 1024
HEIGHT = 600
main_surface = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
surface_rect = main_surface.get_rect()

### GameStuff ###
GAME_OVER = False
D_LOCK = threading.Event()

### Music ###
pygame.mixer.music.load("music/Nimbus2000.ogg")
sound_effect = pygame.mixer.Sound("music/SoundEffect.ogg")

### Misc ###
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
font_basic = pygame.font.SysFont("Helvetica", 120)
font_big = pygame.font.SysFont("Helvetica", 72)
font_small = pygame.font.SysFont("Helvetica", 50)



####################
##  Classes
####################

class Status(pygame.sprite.Sprite):
    def __init__(self, value=0, xpos=0):

        ### Creating the object ###
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([100, 100])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()

        ### Establishing the location ##
        self.rect.centerx = main_surface.get_rect().centerx
        self.rect.centery = main_surface.get_rect().centery
        self.rect.centerx += xpos

        ### Status information ###
        self.value = value

    def update(self, new_val):
        self.value = new_val

ammo = Status(xpos=-250)
lives = Status()
defense = Status(xpos=250)


####################
##  MQTT callback functions
####################

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received unexpected message: " + message)

def on_message_status(client, userdata, msg):
    message = msg.payload.decode()
    print("Status: " + message)

    # Update status here through pygame
    pass

def on_message_player(client, userdata, msg):
    message = msg.payload.decode()
    print("Order: " + message)

    if message == START_ACTION:
        # Inform Player to do action here through pygame
        pass
    elif message == START_DIST:
        D_LOCK.set()
    elif message == STOP_GAME:
        global GAME_OVER
        GAME_OVER = True
        D_LOCK.set()


####################
##  Functions
####################

def send_action(client, name, action, value=""):
    message = '_'.join([name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret

def process_distance(client, name):
    D_LOCK.wait()
    while not GAME_OVER:

        ################
        ### EDIT HERE FOR CAMERA STUFF
        value = input("Input a distance between 0.00 and 1.00: ")
        ### EDIT HERE FOR CAMERA STUFF
        ################################
        send_action(client, name, Act.DIST, value)

        if not GAME_OVER:
            D_LOCK.clear()
        D_LOCK.wait()

def draw_main(name, all_sprites):
    player = font_basic.render(name, True, WHITE, BLACK) 
    player_rect = player.get_rect()
    player_rect.centerx = surface_rect.centerx 
    player_rect.y = 10

    main_surface.fill(BLACK)
    main_surface.blit(player, player_rect)

    all_sprites.draw(main_surface)


####################
##  Main function
####################

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.message_callback_add(TOPIC_STATUS, on_message_status)
    client.message_callback_add(TOPIC_PLAYER, on_message_player)
    client.connect("broker.hivemq.com")
    client.subscribe(TOPIC_GLOBAL)
    client.subscribe(TOPIC_STATUS)
    client.subscribe(TOPIC_PLAYER)

    if len(sys.argv) == 2:
        # Sleep necessary if no code present before publish
        time.sleep(0.25)
        name = sys.argv[1]
    else:
        name = input("Please enter your name: ")
    role = "laptop"
    setup_message = "{}_{}".format(name, role)
    client.publish(TOPIC_SETUP, setup_message)

    print("Listening...")
    client.loop_start()

    t = threading.Thread(target=process_distance, args=[client, name])
    t.start()


    ####################
    ##  Start Game
    ####################

    all_sprites = pygame.sprite.RenderPlain(ammo, lives, defense)

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
        draw_main(name, all_sprites)
        
        pygame.display.update()
        clock.tick(60)


    ####################
    ##  End Game
    ####################

    pygame.mixer.music.load("music/LeavingHogwarts.ogg")
    # pygame.mixer.music.play(-1, 0.5)

    # Visuals
    game_over = font_big.render("GAME OVER", True, WHITE, BLACK)
    g_o_rect = game_over.get_rect()
    g_o_rect.centerx = surface_rect.centerx
    g_o_rect.centery = surface_rect.centery - 50

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
