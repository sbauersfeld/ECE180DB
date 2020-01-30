import board
import neopixel
import time

pixels = neopixel.NeoPixel(board.D18, 12)
while True:
  #pixels.fill((255, 0, 0))
  pixels[0] = (255, 0, 0)
  #time.sleep(1)
