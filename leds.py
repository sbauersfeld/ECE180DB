import board
import neopixel

num_pixels = 12
pixels = neopixel.NeoPixel(board.D18, num_pixels)
#pixels.fill((0, 255, 0))
pixels[0] = (0, 255, 0)

#for i in range(num_pixels):
 # pixels[i] = (0, 255, 0)

pixels.show()
