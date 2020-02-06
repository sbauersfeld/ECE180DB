from config import *
import paho.mqtt.client as mqtt
import sys
import time
import pygame, sys, time
from pygame.locals import *


####################
##  Variables
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
player_win = False

### Music ###
pygame.mixer.music.load("music/zelda.ogg")
sound_effect = pygame.mixer.Sound("music/dada.ogg")

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
    def __init__(self, category, value=0, xpos=0):

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
        self.category = category
        self.value = value

    def update_value(self, new_val):
        self.value = new_val


####################
##  Functions
####################

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received message: " + message)

def send_action(client, name, action, value=""):
    print("Sending message...")

    topic = "ee180d/hp_shotgun/action"
    message = '_'.join([name, action.name, value])
    ret = client.publish(topic, message)

    # print(topic)
    print(message)
    # print(ret.is_published())
    # print(ret.rc == mqtt.MQTT_ERR_SUCCESS)

    return ret

def register_action():
    msg = input("Enter the desired action: ").upper()
    if msg in Act.__members__.keys():
        action = Act.__members__[msg]
        return action
    else:
        print("That's not an action!")
        return register_action()

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
    client.connect("broker.hivemq.com")
    client.subscribe("ee180d/hp_shotgun/status")

    if len(sys.argv) == 2:
        # Sleep necessary if no code present before publish
        time.sleep(0.5)
        name = sys.argv[1]
    else:
        name = input("Please enter your name: ")
    client.publish("ee180d/hp_shotgun/setup", name)

    print("Listening...")
    client.loop_start()


    ####################
    ##  Start Game
    ####################

    ammo = Status("ammo", xpos=-250)
    lives = Status("lives")
    defense = Status("defense", xpos=250)
    all_sprites = pygame.sprite.RenderPlain(ammo, lives, defense)

    time.sleep(1.5)
    pygame.mixer.music.play(-1, 0.5)

    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                global player_win
                player_win = True
                done = True

        # # Extend loop to register detected actions
        # action = register_action()
        # send_action(client, name, action)

        # Visuals
        draw_main(name, all_sprites)
        
        pygame.display.update()
        clock.tick(60)


    ####################
    ##  End Game
    ####################

    pygame.mixer.music.load("music/end.ogg")
    pygame.mixer.music.play(-1, 0.5)

    # Visuals
    game_over = font_big.render("GAME OVER", True, WHITE, BLACK)
    if player_win == True:
        winner = font_small.render("Player Wins", True, WHITE, BLACK)

    g_o_rect = game_over.get_rect()
    g_o_rect.centerx = surface_rect.centerx
    g_o_rect.centery = surface_rect.centery - 50
    win_rect = winner.get_rect()
    win_rect.centerx = g_o_rect.centerx
    win_rect.centery = g_o_rect.centery + 75

    main_surface.fill(BLACK)
    main_surface.blit(game_over, g_o_rect)
    main_surface.blit(winner, win_rect)

    while True:
        # Quit conditions
        for event in pygame.event.get():
            if event.type == QUIT:
                break
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                break

        # Visuals
        pygame.display.update()

    pygame.quit()
        

if __name__ == '__main__':
    main()
