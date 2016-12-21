import os
import numpy as np
import bitstruct
import math

def to_tile(dir, data, bin_RED, ni, nj, level=1, thinout=0):
    ntile = 2 ** level
    files = []

    directory = dir + '/' + str(level)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if thinout == 0:
        tni = (ni - 1) / ntile + 1
        tnj = (nj - 1) / ntile + 1

        for ty in range(0, ntile):
            for tx in range(0, ntile):
                tile_data = []
                lx1 = (tni - 1) * tx
                lx2 = (tni - 1) * (tx + 1) + 1
                length = (lx2 - lx1) * 12
                format_row = 'r' + str(length)

                for y in range(0, tnj):
                    base_y = ni * ((tnj - 1) * ty + y)
                    bx1 = int(math.floor((base_y + lx1) * 12 / 8.))
                    bx2 = int(math.ceil((base_y + lx2) * 12 / 8.))
                    d = data[bx1:bx2]

                    if ((base_y + lx1) * 12) % 8 == 4:
                        tile_data.extend(list(bitstruct.unpack('p4' + format_row, d)))
                    else:
                        tile_data.extend(list(bitstruct.unpack(format_row, d)))

                bin_tile_data = bitstruct.pack(format_row * tnj, *tile_data)

                file = directory + '/%d_%d.bin' % (tx, ty)
                f = open(file, 'w')
                f.write(bin_RED + bin_tile_data)
                f.close()
                files.append(file)

    elif thinout > 0:
        thinout_level = 2 ** thinout
        tni = (ni - 1) / thinout_level / ntile + 1
        tnj = (nj - 1) / thinout_level / ntile + 1

        for ty in range(0, ntile):
            for tx in range(0, ntile):
                tile_data = []
                lx1 = (tni - 1) * thinout_level * tx
                lx2 = (tni - 1) * thinout_level * (tx + 1) + 1
                l = tni - 1
                format_row = ('u12' + 'p12' * (thinout_level - 1)) * l + 'u12'

                for y in range(0, tnj):
                    base_y = ni * thinout_level * ((tnj - 1) * ty + y)
                    bx1 = int(math.floor((base_y + lx1) * 12 / 8.))
                    bx2 = int(math.ceil((base_y + lx2) * 12 / 8.))
                    d = data[bx1:bx2]

                    if ((base_y + lx1) * 12) % 8 == 4:
                        tile_data.extend(list(bitstruct.unpack('p4' + format_row, d)))
                    else:
                        tile_data.extend(list(bitstruct.unpack(format_row, d)))

                bin_tile_data = bitstruct.pack('u12' * tni * tnj, *tile_data)

                file = directory + '/%d_%d.bin' % (tx, ty)
                f = open(file, 'w')
                f.write(bin_RED + bin_tile_data)
                f.close()
                files.append(file)

    return files

