import PIL
from PIL import Image
from matplotlib import pyplot as plt
import sys
import numpy
import struct

im = Image.open(sys.argv[1])  
w, h = im.size  
colors = im.getcolors(w*h)

if len(sys.argv) > 2 and sys.argv[2] == 'visualize':
    def hexencode(rgb):
        r=rgb[0]
        g=rgb[1]
        b=rgb[2]
        return '#%02x%02x%02x' % (r,g,b)

    for idx, c in enumerate(colors):
        color = hexencode(c[1])
        plt.bar(idx, c[0], color=color, edgecolor=color)

    plt.show()


# make a summary histogram and write it out to a file
# http://stackoverflow.com/questions/1819124/image-comparison-algorithm

r = numpy.asarray(im.convert( "RGB", (1,0,0,0, 1,0,0,0, 1,0,0,0) ))
g = numpy.asarray(im.convert( "RGB", (0,1,0,0, 0,1,0,0, 0,1,0,0) ))
b = numpy.asarray(im.convert( "RGB", (0,0,1,0, 0,0,1,0, 0,0,1,0) ))
MAX_VAL = 256
NUM_BINS = 64
bins = range(0, MAX_VAL + 1, MAX_VAL / NUM_BINS)
hr, h_bins = numpy.histogram(r, bins=bins)
hg, h_bins = numpy.histogram(g, bins=bins)
hb, h_bins = numpy.histogram(b, bins=bins)
hist = numpy.array([hr, hg, hb]).ravel()
buf = bytearray(4 * 64 * 3)

with open('hist.bin', 'wb') as f:
    for i, data in enumerate(hist):
        struct.pack_into('>I', buf, 4*i, data)
    f.write(buf)

for idx, count in enumerate(hist):
    plt.bar(idx, count)

plt.show()
