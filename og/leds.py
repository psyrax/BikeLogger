from adafruit_led_animation import helper
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.color import PURPLE, CYAN, JADE, ORANGE
from adafruit_led_animation.sequence import AnimationSequence
from adafruit_pixel_framebuf import PixelFramebuffer
import asyncio
import neopixel
import board
from math import ceil
from time import monotonic, sleep

class OGLEDS:
    def __init__(self):
        pixel_pin = board.GP0
        num_pixels = 64
        self.pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1, auto_write=False)
        self.pixelframe = PixelFramebuffer(
            self.pixels,
            8,
            8,
            alternating=False,
            rotation = 2
        )
        pixelMatrix = helper.PixelMap.vertical_lines(
            self.pixels, 8, 8, helper.vertical_strip_gridmap(8, alternating=False)
        )
        comet = Comet(pixelMatrix, speed=0.1, color=PURPLE, tail_length=2, bounce=True)
        chase = Chase(pixelMatrix, speed=0.1, color=JADE, size=2, spacing=2)


        self.animations = AnimationSequence(
            comet,
            chase,
            advance_interval=5,
            auto_clear=True,
            random_order = True
        )

    def setBrightness(self, brightness):
        self.pixels.brightness = brightness

    def blinkBlock(self, color):
        for i in range(2):
            self.pixelframe.fill(0)
            self.pixelframe.display()
            sleep(.5)
            self.pixelframe.fill(color)
            self.pixelframe.display()
            sleep(.5)
            self.pixelframe.fill(0)
            self.pixelframe.display()

    def writeText(self, text, color=0xFFFFFF):
        text = '   {}   '.format(text)
        charBufSize = ceil(8/5)
        self.blinkBlock(color)
        for i in range(len(text)+1):
            cText = text[i:i+charBufSize]
            for j in range(6):
                self.pixelframe.fill(0)
                self.pixelframe.text(cText, -1*(j), 0,color)
                self.pixelframe.display()
        self.blinkBlock(color)
        

    async def updateStatus(self, status):
        while True:
            color= 0xFFA500
            if status.fixStatus is 1:
                color = 0x00FF00
            if status.fixStatus is 2:
                color = 0x00FFFF
            if status.display:
                self.writeText(status.gpsText, color)
                status.display = False
            else:
                self.animations.animate()
            await asyncio.sleep(0)
