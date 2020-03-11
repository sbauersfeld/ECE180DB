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
from range_detection.range_detection import GetDistance, TestDistance
from speech_detection.speech_detection import speech_setup, get_speech, get_speech2, translate_speech


####################
##  Global Variables
####################

### GameStuff ###
GAME_OVER = False
PLAYER_WIN = "Nobody"
D_LOCK = threading.Event()
client = mqtt.Client()

### Voice ###
headset_map = {
    "scott" : "Headset (SoundBuds Slim Hands-F",
    "jon" : "SP620",
}
start_phrase = ["start", "starch", "sparks", "fart", "darts", "spikes",
                "search", "bikes", "strikes", "starks", "steps", "stopped",
                "art", "starts"]

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
sound_activate = pygame.mixer.Sound("music/Activate.ogg")
sound_tutorial = pygame.mixer.Sound("music/Tutorial.ogg")

### Text fonts and colors ###
WHITE = (255, 255, 255)
RED = (225, 0, 0)
BLACK = (0, 0, 0)
GRAY = (155, 155, 155)
font_large = pygame.font.SysFont("Helvetica", 120)
font_small = pygame.font.SysFont("Helvetica", 50)

### Text type map ###
text_map = {
    Text.NUM : (pygame.font.SysFont("Helvetica", 180), WHITE),
    Text.TEXT : (font_large, WHITE),
    Text.TUTORIAL : (pygame.font.SysFont("Helvetica", 100), WHITE),
    Text.ENEMY : (pygame.font.SysFont("Helvetica", 80), GRAY),
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
        self.top = ""
        self.bottom = ""
        self.temp_def = defense

    def update_name(self, new_name):
        self.name = new_name

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

class Tutorial:
    def __init__(self):
        # Variables
        self.OVER = False
        self.channel = None
        self.run_lock = threading.Lock()

        # State
        self.show_camera = False
        self.check1 = False
        self.check2 = False

        # Script
        self.max_lines = 0
        self.current = 0
        self.script_map = {}
        self.lock_map = {}

    def start(self, images=None):
        with open("script.txt") as f:
            for count, line in enumerate(f):
                try:
                    period_str, text1, text2 = line.strip().split(SEP)
                    self.script_map[count] = int(period_str), text1, text2
                    self.lock_map[count] = threading.Event()
                    self.max_lines += 1
                except ValueError:
                    print("Unexpected line: {}".format(line.strip()))

        if images is not None:
            hold_splash(images)

        if self.max_lines <= 0:
            self.end()
            return

        self.channel = sound_tutorial.play()

    def run(self):
        self.run_lock.acquire()

        print("\nStarting: Tutorial {}/{}".format(self.current+1, self.max_lines))
        self.reset()
        period, text1, text2 = self.script_map[self.current]
        PLAYER.update_top(text1)
        PLAYER.update_bottom(text2)

        self.run_lock.release()

    def reset(self):
        self.show_camera = False
        self.check1 = False
        self.check2 = False

    def next(self, next_lock=None):
        if not self.run_lock.acquire(False):
            return

        old_current = self.current

        if next_lock is None:
            self.current += 1
            if self.current >= self.max_lines:
                self.end()

            print("Finished: Tutorial {}/{}".format(old_current+1, self.max_lines))
            self.lock_map[old_current].set()

        elif next_lock in range(self.max_lines):
            self.current = next_lock
            for lock in range(self.current, self.max_lines):
                self.lock_map[lock].clear()

            self.lock_map[old_current].set()
            self.lock_map[old_current].clear()

        self.run_lock.release()

    def wait(self):
        if self.current not in range(self.max_lines):
            return

        period, text1, text2 = self.script_map[self.current]
        print("Waiting: {} seconds for: {}".format(period, self.current+1))
        return self.lock_map[self.current].wait(timeout=period)

    def end(self):
        self.OVER = True
        for num, lock in self.lock_map.items():
            lock.set()

    def is_finished(self):
        return self.OVER

    def is_talking(self):
        if self.channel is None:
            return False
        
        return self.channel.get_busy()

PLAYER = Player()
OTHER = Player(lives="", ammo="", defense="")
TUTORIAL = Tutorial()


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
##  Process Messages
####################

def process_order(order, value1, value2):
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
        # Add if statements here for individual

        try:
            action = Act[value1]
            print("Received action: {}".format(action))
            if action in [Act.RELOAD, Act.BLOCK, Act.SHOOT]:
                PLAYER.update_top("")
                PLAYER.update_bottom(action.name)
        except KeyError:
            # For individual display messages
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
        # For display messages to all
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
    
    if order == PLAYER.name:
        if value1 == HIT:
            PLAYER.update_top("YOU GOT HIT")
            PLAYER.update_color(RED)


####################
##  Functions
####################

def detect_voice(microphone, trigger=[], print_func=PLAYER.update_top):
    print_func("Say '{}' to continue!".format(trigger[0]))
    recognizer, audio = get_speech2(microphone)
    print_func("Detected voice!")

    success, value = translate_speech(recognizer, audio)
    if success:
        if not trigger or value in trigger:
            print_func("Voice registered!")
            return value
        print_func("- {} -".format(value))
    else:
        print_func(value)

    return None

def detect_distance(camera, speed=0.5):
    cap_setting = camera_map.get(PLAYER.name, camera_default)

    new_val = GetDistance(camera, cap_setting, speed)

    float_val = float(new_val)  # Necessary since new_val is type np.float64
    PLAYER.update_temp_def(str(round(float_val, SIGFIG)))


####################
##  Threads
####################

def detect_for_trigger(microphone, trigger):
    while True:
        ret = detect_voice(microphone, trigger)
        if ret is not None:
            break

        time.sleep(1.5)

def handle_tutorial():
    set_check = False
    while not TUTORIAL.is_finished():
        TUTORIAL.run()

        set_check = TUTORIAL.wait()
        if not set_check:
            TUTORIAL.next()

def handle_distance(microphone):
    cap = cv2.VideoCapture(0)

    print("Range detection active!")
    D_LOCK.wait()
    while not GAME_OVER:
        timer = threading.Timer(5, detect_for_trigger, [microphone, start_phrase])
        timer.start()
        
        while timer.isAlive():
            detect_distance(cap)

        send_action(Act.DIST, PLAYER.temp_def)

        if not GAME_OVER:
            D_LOCK.clear()
        D_LOCK.wait()

    cap.release()
    cv2.destroyAllWindows()


####################
##  Pygame Functions
####################

def draw_display(images=(), labels=(), enable_status=True, enable_enemy=True, text_type=Text.TEXT):
    main_surface.fill(BLACK)
    for blit_image in images:
        image, rect = blit_image
        main_surface.blit(image, rect)

    top = Status(PLAYER.top, text_type, XPOS_ZERO, YPOS_TOP, hit_change=PLAYER.color)
    bottom = Status(PLAYER.bottom, text_type, XPOS_ZERO, YPOS_BOTTOM)
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

def draw_tutorial(images=(), labels=(), progress_check=False, progress_check2=False):
    draw_display(images, labels, progress_check, progress_check2, text_type=Text.TUTORIAL)

def hold_splash(images, vel=5, d_max=225, d_min=440, fade_out=300):
    sound_activate.play()
    count, alpha = 0, 0

    SPLASH_OVER = False
    while not SPLASH_OVER:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                SPLASH_OVER = True
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                SPLASH_OVER = True


        main_surface.fill(BLACK)
        image, rect = images[0]
        image.set_alpha(alpha)
        main_surface.blit(image,rect)

        count += vel
        alpha = count
        if count >= d_min:
            SPLASH_OVER = True
        elif count >= fade_out:
            alpha = d_max - (count-fade_out)
        elif count >= d_max:
            alpha = d_max

        pygame.display.update()
        clock.tick(60)

def setup_images():
    ### Pictures ###
    arc_reactor = pygame.image.load("images/arc_reactor1.png")
    arc_reactor = pygame.transform.scale(arc_reactor, (360, 360))
    stark_industries = pygame.image.load("images/stark_industries2.png")
    stark_industries = pygame.transform.scale(stark_industries, (420, 165))
    avengers_logo = pygame.image.load("images/avengers2.png")
    avengers_logo = pygame.transform.scale(avengers_logo, (435, 160))
    arc_reactor_fade = pygame.image.load("images/arc_reactor0.png").convert()
    arc_reactor_fade = pygame.transform.scale(arc_reactor_fade, (360, 360))

    # Arc Reactor
    arc_rect = arc_reactor.get_rect()
    arc_rect.centerx, arc_rect.centery = main_origin.centerx, main_origin.centery
    fade_rect = arc_reactor_fade.get_rect()
    fade_rect.centerx, fade_rect.centery = main_origin.centerx, main_origin.centery

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

    # Tutorial Images
    image_arc_fade = arc_reactor_fade, fade_rect
    splash_images = image_arc_fade,
    tutorial_images = image_arc,

    # Labels
    l_ammo = Status(AMMO, Text.LABEL, -XPOS_SIDE, YPOS_LABEL)
    l_lives = Status(LIVES, Text.LABEL, XPOS_ZERO, YPOS_LABEL)
    l_defense = Status(DEFENSE, Text.LABEL, XPOS_SIDE, YPOS_LABEL)
    labels = (l_ammo, l_lives, l_defense)

    return game_images, labels, tutorial_images, splash_images

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
        print("Please input a name!")
        sys.exit()
    PLAYER.update_name(name)
    global GAME_OVER, PLAYER_WIN

    print("Listening...")
    client.loop_start()

    # Finish setup
    threads = []
    microphone = speech_setup(headset_map.get(name))
    game_images, labels, tutorial_images, splash_images = setup_images()


    ####################
    ##  Tutorial
    ####################

    TUTORIAL.start(splash_images)
    t_args = {
        handle_tutorial : [],
    }
    for func, args in t_args.items():
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()
        threads.append(t)

    while not TUTORIAL.is_finished():
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                TUTORIAL.end()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                TUTORIAL.end()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                TUTORIAL.next()

        # Visuals
        draw_tutorial(tutorial_images, labels, TUTORIAL.check1, TUTORIAL.check2)

        ### This needs to be changed - currently calls every frame
        # Camera
        if TUTORIAL.show_camera:
            TestDistance(camera_map.get(PLAYER.name, camera_default), True, 20, 10)
            TUTORIAL.show_camera = False
        
        pygame.display.update()
        clock.tick(12)

    ### This should apply after each while loop lol ###
    for t in threads:
        t.join()
    print()
    threads.clear()


    ####################
    ##  Start Game
    ####################

    t_args = {
        handle_distance : [microphone],
    }
    for func, args in t_args.items():
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()
        threads.append(t)

    PLAYER.update_top("Waiting for server...")
    PLAYER.update_bottom(name)
    pygame.mixer.music.load("music/SuitUp.mp3")
    pygame.mixer.music.play(0)
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

    END_OVER = False
    while not END_OVER:
        # Quit conditions
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                END_OVER = True

        # Visuals
        pygame.display.update()

    pygame.quit()


if __name__ == '__main__':
    main()
