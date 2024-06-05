import time
from socket import socket, AF_INET, SOCK_DGRAM

from PIL import Image, ImageFont, ImageDraw

UDP_ADDRESS = UDP_HOST, UDP_PORT = '192.168.1.14', 2323

FPS = 3
INVERT=False

IMG_SIZE = (120, 16)
FONT_SIZE = 11
FONT_OFFSET= (1, -1)

C_BLACK = (0, 0, 0)
C_WHITE = (255, 255, 255)

s = socket(AF_INET, SOCK_DGRAM)
s.connect(UDP_ADDRESS)

def list2byte(l):
    byte = 0
    i = 0
    for i in range(8):
        byte += 2**(7-i) if l[i] else 0
    return byte

def array2packet(a):
    print(a)
    return bytearray([list2byte(a[i*8:i*8+8]) for i in range(int(len(a)/8))])

def str2array(s):
    image = Image.new("RGBA", IMG_SIZE, C_BLACK)
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"         # No AA
    #font = ImageFont.load_default()
    font = ImageFont.load_default(FONT_SIZE)

    draw.text(FONT_OFFSET, s, font=font, fill=C_WHITE)

    imgmap = []
    for pixel in image.getdata():
        r, g, b, a = pixel
        if r == 255:
            imgmap.append(0 if INVERT else 1)
        else:
            imgmap.append(1 if INVERT else 0)
    return imgmap


text = 'GET TO THE CHOPPA'
for i in range(0, len(text) + 1):
    print(i, text[i:])
    time.sleep(0.2)
    s.send(array2packet(str2array(text[i:])))



