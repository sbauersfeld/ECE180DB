from config import *
import paho.mqtt.client as mqtt
import sys
import time
import threading
import json
import platform
import pygame
from pygame.locals import *
import numpy as np
import cv2
import imutils
from range_detection.range_detection import GetDistance
from speech_detection.speech_detection import speech_setup, get_speech, get_speech2, translate_speech


####################
##  Global Variables
####################

### GameStuff ###
GAME_OVER = False
PLAYER_WIN = "Nobody"
D_LOCK = threading.Event()
V_LOCK = threading.Event()
client = mqtt.Client()

### Voice ###
start_phrase = ["start", "starch", "sparks", "fart", "darts", "spikes",
                "search", "bikes", "strikes", "starks", "steps", "stopped",
                "art"]
headset_map = {
    "scott" : "Headset (SoundBuds Slim Hands-F",
    "jon" : "SP620",
}

### Camera ###
camera_default = ([160,150,150], [180,255,255], 500)
camera_map = {
    "scott" :   ([160,150,150], [180,255,255], 500),
    "jon" :     ([160,50,50],   [180,255,255], 1000),
    "wilson" :  ([160,150,150], [180,255,255], 500),
    "jesse" :   ([160,150,150], [180,255,255], 500)
}

### Pygame ###
pygame.init()
clock = pygame.time.Clock()

### Creating the main surface ###
if platform.system() == "Darwin":
    pygame_flags = pygame.NOFRAME
else:
    pygame_flags = pygame.FULLSCREEN
main_surface = pygame.display.set_mode((0, 0), pygame_flags)
main_origin = main_surface.get_rect()

### Display position ###
WIDTH, HEIGHT = main_surface.get_size()
M_WIDTH, M_HEIGHT = 1440, 900
WIDTH_FACTOR = WIDTH/M_WIDTH
HEIGHT_FACTOR = HEIGHT/M_HEIGHT

XPOS_SIDE = round(400 * WIDTH_FACTOR)
XPOS_ZERO = round(0 * WIDTH_FACTOR)
YPOS_STATUS = round(10 * HEIGHT_FACTOR)
YPOS_LABEL = round(-85 * HEIGHT_FACTOR)
YPOS_OTHER = round(105 * HEIGHT_FACTOR)
YPOS_TOP = round(-300 * HEIGHT_FACTOR)
YPOS_BOTTOM = round(305 * HEIGHT_FACTOR)

### Music ###
sound_suit_up = pygame.mixer.Sound("music/SuitUp.ogg")
sound_shoot = pygame.mixer.Sound("music/Repulsor1.ogg")

### Text fonts and colors ###
WHITE = (255, 255, 255)
RED = (225, 0, 0)
BLACK = (0, 0, 0)
GRAY = (155, 155, 155)
font_huge = pygame.font.SysFont("Helvetica", 180)
font_large = pygame.font.SysFont("Helvetica", 120)
font_big = pygame.font.SysFont("Helvetica", 80)
font_small = pygame.font.SysFont("Helvetica", 50)

### Text type map ###
text_map = {
    Text.NUM : (font_huge, WHITE),
    Text.TEXT : (font_large, WHITE),
    Text.ENEMY : (font_big, GRAY),
    Text.LABEL : (font_small, WHITE),
}


####################
##  Classes
####################

class Player:
    def __init__(self, name="", lives=LIVES_MAX, ammo=AMMO_RELOAD, defense="?"):
        # Status
        self.name = name
        self.lives = lives
        self.ammo = ammo
        self.defense = defense

        # Display
        self.color = WHITE
        self.top = "Waiting for server..."
        self.bottom = name
        self.temp_def = defense

    def update_name(self, new_name):
        self.name = new_name
        self.bottom = new_name

    def update_status(self, status=None, lives=None, ammo=None, defense=None):
        if status:
            self.lives = status[LIVES]
            self.ammo = status[AMMO]
            self.defense = status[DEFENSE]
            return

        if lives:
            self.lives = lives
        if ammo:
            self.ammo = ammo
        if defense:
            self.defense = defense

    def update_color(self, new_color):
        self.color = new_color

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
    def __init__(self, value, text_type, xpos, ypos, hit_change=None,
                xval=None, yval=None, background=None):
        ### Status information ###
        self.value = str(value)

        ### Creating the object ###
        pygame.sprite.Sprite.__init__(self)
        font, color = text_map.get(text_type)
        if hit_change:
            color = hit_change
        self.image = font.render(self.value, True, color, background)
        self.rect = self.image.get_rect()

        ### Establishing the location ###
        self.rect.centerx = main_origin.centerx if not xval else xval
        self.rect.centery = main_origin.centery if not yval else yval
        self.rect.centerx += xpos
        self.rect.centery += ypos

PLAYER = Player()
OTHER = Player(lives="", ammo="", defense="")


####################
##  MQTT Functions
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

    try:
        msg_list = message.split(SEP)
        order = msg_list[0]
        value1 = msg_list[1]
        value2 = msg_list[2]
    except (IndexError):
        print("Unexpected message: {}".format(message))
        return

    process_order_player(order, value1, value2)

def send_action(action, value=""):
    message = SEP.join([PLAYER.name, action.name, value])
    ret = client.publish(TOPIC_ACTION, message)

    print("Sent: {}".format(message))
    return ret


####################
##  Functions
####################

def process_order(order, value1, value2):
    if order == VOICE:
        PLAYER.update_bottom("Say 'start' to continue...")
        V_LOCK.set()

    if order == DIST:
        print()
        PLAYER.update_top("Move to new {}!".format(DEFENSE))
        PLAYER.update_bottom("...")
        PLAYER.update_color(WHITE)
        D_LOCK.set()

    if order == ACTION_COUNT:
        PLAYER.update_top("Get ready...")
        PLAYER.update_bottom("action in {}".format(value1))

    if order == PLAYER.name:
        try:
            action = Act[value1]
            print("Received action: {}".format(action))
            if action in [Act.RELOAD, Act.BLOCK, Act.SHOOT]:
                PLAYER.update_top("")
                PLAYER.update_bottom(action.name)
        except KeyError:
            PLAYER.update_bottom(value1)        

    if order == STATUS:
        status = json.loads(value1)
        print(status)

        if status["name"] == PLAYER.name:
            PLAYER.update_status(status)
        elif status["name"] == OTHER.name:
            OTHER.update_status(status)
        elif OTHER.name == "":
            OTHER.update_name(status["name"])
            OTHER.update_status(status)

    if order == DISPLAY:
        PLAYER.update_bottom(value1)

def process_order_player(order, value1, value2):
    if order == ACTION:
        PLAYER.update_top("Reading gestures...")
        PLAYER.update_bottom("NOW")

    if order == STOP_GAME:
        global GAME_OVER, PLAYER_WIN
        GAME_OVER = True
        PLAYER_WIN = value1

        D_LOCK.set()
        V_LOCK.set()
    
    if order == PLAYER.name:
        if value1 == HIT:
            PLAYER.update_top("YOU GOT HIT")
            PLAYER.update_color(RED)


####################
##  Threads
####################

def detect_distance(headset):
    cap = cv2.VideoCapture(0)
    cap_setting = camera_map.get(PLAYER.name, camera_default)
    microphone = speech_setup(headset)

    print("Range detection active!")
    D_LOCK.wait()
    while not GAME_OVER:
        timer = threading.Timer(5, detect_voice_start, [microphone, start_phrase])
        timer.start()
        
        while timer.isAlive():
            new_val = GetDistance(cap, cap_setting, 0.5)
            float_val = float(new_val)  # Necessary since new_val is type np.float64
                                        # round(new_val, None) does not return an int
            PLAYER.update_temp_def(str(round(float_val, SIGFIG)))

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

def detect_voice_start(microphone, trigger):
    while True:
        PLAYER.update_top("Say '{}' to continue!".format(trigger[0]))
        recognizer, audio = get_speech2(microphone)
        PLAYER.update_top("Detected voice!")

        success, value = translate_speech(recognizer, audio)
        if success:
            if value in trigger:
                PLAYER.update_top("Voice registered!")
                break
            PLAYER.update_top("- {} -".format(value))
        else:
            PLAYER.update_top(value)

        time.sleep(1.5)


####################
##  Pygame Functions
####################

def draw_display(blit_images=(), labels=(), enable_status=True, enable_enemy=True):
    main_surface.fill(BLACK)
    for blit_image in blit_images:
        image, rect = blit_image
        main_surface.blit(image, rect)

    top = Status(PLAYER.top, Text.TEXT, XPOS_ZERO, YPOS_TOP, hit_change=PLAYER.color)
    bottom = Status(PLAYER.bottom, Text.TEXT, XPOS_ZERO, YPOS_BOTTOM)
    all_sprites = pygame.sprite.RenderPlain(top, bottom)

    if enable_status:
        ammo = Status(PLAYER.ammo, Text.NUM, -XPOS_SIDE, YPOS_STATUS)
        lives = Status(PLAYER.lives, Text.NUM, XPOS_ZERO, YPOS_STATUS, hit_change=PLAYER.color)
        defense = Status(PLAYER.defense, Text.NUM, XPOS_SIDE, YPOS_STATUS)
        all_sprites.add(labels)
        all_sprites.add((ammo, lives, defense))

    if enable_enemy:
        enemy_ammo = Status(OTHER.ammo, Text.ENEMY, -XPOS_SIDE, YPOS_OTHER)
        enemy_lives = Status(OTHER.lives, Text.ENEMY, XPOS_ZERO, YPOS_OTHER)
        enemy_defense = Status(OTHER.defense, Text.ENEMY, XPOS_SIDE, YPOS_OTHER)
        all_sprites.add((enemy_ammo, enemy_lives, enemy_defense))

    all_sprites.draw(main_surface)

def draw_tutorial(labels=(), progress_check=False, progress_check2=False):
    draw_display((), labels, progress_check, progress_check2)

def setup_images():
    ### Pictures ###
    arc_reactor = pygame.image.load("images/arc_reactor1.png")
    arc_reactor = pygame.transform.scale(arc_reactor, (360, 360))
    stark_industries = pygame.image.load("images/stark_industries2.png")
    stark_industries = pygame.transform.scale(stark_industries, (420, 165))
    avengers_logo = pygame.image.load("images/avengers2.png")
    avengers_logo = pygame.transform.scale(avengers_logo, (435, 160))

    # Arc Reactor
    arc_rect = arc_reactor.get_rect()
    arc_rect.centerx, arc_rect.centery = main_origin.centerx, main_origin.centery

    # Stark Industries
    stark_rect = stark_industries.get_rect()
    stark_rect.bottomleft = main_origin.bottomleft
    stark_rect.centerx += 10
    stark_rect.centery -= 10

    # Avengers Logo
    avengers_rect = avengers_logo.get_rect()
    avengers_rect.bottomright = main_origin.bottomright
    avengers_rect.centerx -= 10
    avengers_rect.centery -= 10

    # Images
    image_arc = arc_reactor, arc_rect
    image_stark = stark_industries, stark_rect
    image_avengers = avengers_logo, avengers_rect
    game_images = image_arc, image_stark, image_avengers

    # Labels
    l_ammo = Status(AMMO, Text.LABEL, -XPOS_SIDE, YPOS_LABEL)
    l_lives = Status(LIVES, Text.LABEL, XPOS_ZERO, YPOS_LABEL)
    l_defense = Status(DEFENSE, Text.LABEL, XPOS_SIDE, YPOS_LABEL)
    labels = (l_ammo, l_lives, l_defense)

    return game_images, labels

def setup_images_end():
    # Game Over Text
    game_over = font_large.render("GAME OVER", True, WHITE, BLACK)
    g_o_rect = game_over.get_rect()
    g_o_rect.centerx = main_origin.centerx
    g_o_rect.centery = main_origin.centery - 50

    # Winner Text
    winner = font_small.render("--- {} wins! ---".format(PLAYER_WIN), True, WHITE, BLACK)
    win_rect = winner.get_rect()
    win_rect.centerx = g_o_rect.centerx
    win_rect.centery = g_o_rect.centery + 85

    # Images
    image_game_over = game_over, g_o_rect
    image_winner = winner, win_rect
    end_images = image_game_over, image_winner

    return end_images


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
    headset = headset_map.get(name)
    global GAME_OVER, PLAYER_WIN

    print("Listening...")
    client.loop_start()

    # Finish setup
    game_images, labels = setup_images()


    ####################
    ##  Tutorial
    ####################

    # Use TestDistance() to show the camera screen (for 5 seconds?)
    # Test voice and gesture control
    # Slowly introduce each display element by draw_tutorial() w/arguments


    ####################
    ##  Start Game
    ####################

    pygame.mixer.music.load("music/SuitUp2.mp3")
    pygame.mixer.music.play(0)

    threads = []
    t_args = {
        detect_distance : [headset],
    }
    for func, args in t_args.items():
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()
        threads.append(t)

    draw_display(game_images, labels)
    client.publish(TOPIC_SETUP, name)

    while not GAME_OVER:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                GAME_OVER = True
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                GAME_OVER = True
                PLAYER_WIN = PLAYER.name

        # Visuals
        draw_display(game_images, labels)
        
        pygame.display.update()
        clock.tick(12)


    ####################
    ##  End Game
    ####################

    end_images = setup_images_end()
    pygame.mixer.music.load("music/EndCredits.mp3")
    if PLAYER_WIN == PLAYER.name:
        pygame.mixer.music.play(-1, 1)

    # Visuals
    print("Finished the game!")
    main_surface.fill(BLACK)
    for blit_image in end_images:
        image, rect = blit_image
        main_surface.blit(image, rect)

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
