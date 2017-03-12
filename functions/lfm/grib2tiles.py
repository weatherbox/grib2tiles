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

    bitmap = np.unpackbits(np.fromstring(bitmap, dtype=np.uint8))
    no_data = bitstruct.unpack('u12', b'\xff\xff')[0]

    ntile = 2 ** level
    thinout_level = 2 ** thinout
    tni = (ni - 1) / thinout_level / ntile + 1
    tnj = (nj - 1) / thinout_level / ntile + 1

    for ty in range(0, ntile):
        for tx in range(0, ntile):
            tile_data = []

            for y in range(0, tnj):
                base_y = ni * thinout_level * ((tnj - 1) * ty + y)

                for x in range(0, tni):
                    grid_point = base_y + x ** thinout_level

                    if bitmap[grid_point] == 0:
                        tile_data.append(no_data)

                    else:
                        bin_point = np.count_nonzero(bitmap[:grid_point])

                        bx = int(math.floor((bin_point) * 12 / 8.))
                        d = data[bx : bx+2]

                        if (bin_point * 12) % 8 == 4:
                            tile_data.append(bitstruct.unpack('p4u12', d)[0])
                        else:
                            tile_data.append(bitstruct.unpack('u12', d)[0])

            bin_tile_data = bitstruct.pack('u12' * tni * tnj, *tile_data)

            file = directory + '/%d_%d.bin' % (tx, ty)
            print file
            f = open(file, 'w')
            f.write(bin_RED + bin_tile_data)
            f.close()
            files.append(file)

    return files


