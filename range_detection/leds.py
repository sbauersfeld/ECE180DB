import board
import neopixel

num_pixels = 12
pixels = neopixel.NeoPixel(board.D18, num_pixels)
pixels.fill((127, 0, 0))
pixels.show()
