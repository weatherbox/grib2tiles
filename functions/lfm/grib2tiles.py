import os
import numpy as np
import bitstruct
import math
import struct

def to_tile(dir, data, bin_RED, ni, nj, level=1, thinout=0, bitmap=None):
    directory = dir + '/' + str(level)
    if not os.path.exists(directory):
        os.makedirs(directory)

    return to_tile_bitmap_thinout(directory, data, bin_RED, ni, nj, level, thinout, bitmap)


def to_tile_bitmap_thinout(directory, data, bin_RED, ni, nj, level, thinout, bitmap):
    files = []

    bitmap_np = np.unpackbits(np.fromstring(bitmap, dtype=np.uint8))
    no_data = b'\xff\xff'

    ntile = 2 ** level
    thinout_level = 2 ** thinout
    tni = (ni - 1) / thinout_level / ntile + 1
    tnj = (nj - 1) / thinout_level / ntile + 1

    byte_data = bytearray(data)

    for ty in range(0, ntile):
        for tx in range(0, ntile):
    #for ty in range(0, 1):
    #    for tx in range(0, 1):
            bin_tile_data = bytearray()
            i = 0
            prev_byte1 = 0
            prev_byte2 = 0
            now_byte1 = 0b00000000
            now_byte2 = 0b00000000

            for y in range(0, tnj):
                base_y = ni * thinout_level * ((tnj - 1) * ty + y)

                for x in range(0, tni):
                    grid_point = base_y + (x + (tni - 1) * tx) * thinout_level

                    if bitmap_np[grid_point] == 0:
                        now_byte1 = 0b11111111
                        now_byte2 = 0b11111111

                    else:
                        bin_point = np.count_nonzero(bitmap_np[:grid_point])

                        bx = int(math.floor((bin_point) * 12 / 8.))
                        now_byte1 = byte_data[bx]
                        now_byte2 = byte_data[bx+1]

                        if (bin_point * 12) % 8 == 4:
                            now_byte1 = ((now_byte1 & 0b00001111) << 4) | (now_byte2 >> 4)
                            now_byte2 = (now_byte2 & 0b00001111) << 4

                    if i % 2 == 0:
                        prev_byte1 = now_byte1
                        prev_byte2 = now_byte2

                    else:
                        byte3 = now_byte1
                        byte4 = now_byte2

                        bin_tile_data.append(prev_byte1)
                        bin_tile_data.append((prev_byte2 & 0b11110000) | (byte3 >> 4))
                        bin_tile_data.append(((byte3 & 0b00001111) << 4) | (byte4  >> 4))

                    i += 1

            if (tnj % 2 == 1):
                bin_tile_data.append(prev_byte1)
                bin_tile_data.append(prev_byte2)

            file = directory + '/%d_%d.bin' % (tx, ty)
            print file
            f = open(file, 'w')
            f.write(bin_RED + bytes(bin_tile_data))
            f.close()
            files.append(file)

    return files


