import os
import numpy as np
import bitstruct
import math
import struct

def to_tile(dir, data, bin_RED, ni, nj, level=1, thinout=0):
    directory = dir + '/' + str(level)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if level == 0 and thinout == 0:
        return to_tile_raw(directory, data, bin_RED)

    elif thinout == 0:
        if ni % 2 == 1:
            return to_tile_base_odd(directory, data, bin_RED, ni, nj, level)

        else:
            return to_tile_base(directory, data, bin_RED, ni, nj, level)

    elif thinout > 0:
        if ni % 2 == 1:
            return to_tile_thinout_odd(directory, data, bin_RED, ni, nj, level, thinout)

        else:
            return to_tile_thinout(directory, data, bin_RED, ni, nj, level, thinout)


def to_tile_base(directory, data, bin_RED, ni, nj, level):
    files = []

    ntile = 2 ** level
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

    return files 


def to_tile_base_odd(directory, data, bin_RED, ni, nj, level):
    """
    assuming that ni is odd number,
    there is no need to shift binary bytes
    """

    files = []

    ntile = 2 ** level
    tni = (ni - 1) / ntile + 1
    tnj = (nj - 1) / ntile + 1

    for ty in range(0, ntile):
        for tx in range(0, ntile):
            lx1 = (tni - 1) * tx
            lx2 = (tni - 1) * (tx + 1) + 1

            bin_tile_data = ''
            bin_data_even = ''
            bin_data_even_last = ''

            for y in range(0, tnj):
                base_y = ni * ((tnj - 1) * ty + y)
                bx1 = int(math.floor((base_y + lx1) * 12 / 8.))
                bx2 = int(math.ceil((base_y + lx2) * 12 / 8.))

                if ((base_y + lx1) * 12) % 8 == 4:
                    left = struct.unpack('B', bin_data_even_last)[0] & 0b11110000
                    right = struct.unpack('B', data[bx1])[0] & 0b00001111
                    bin_data_glue = struct.pack('B', left | right)

                    bin_tile_data += bin_data_even + bin_data_glue + data[bx1+1:bx2]

                else:
                    bin_data_even = data[bx1:bx2-1]
                    bin_data_even_last = data[bx2-1]

            if (tnj % 2 == 1):
                bin_tile_data += bin_data_even + bin_data_even_last

            file = directory + '/%d_%d.bin' % (tx, ty)
            f = open(file, 'w')
            f.write(bin_RED + bin_tile_data)
            f.close()
            files.append(file)

    return files 


def to_tile_thinout(directory, data, bin_RED, ni, nj, level, thinout):
    files = []

    ntile = 2 ** level
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


def to_tile_thinout_odd(directory, data, bin_RED, ni, nj, level, thinout):
    files = []

    ntile = 2 ** level
    thinout_level = 2 ** thinout
    tni = (ni - 1) / thinout_level / ntile + 1
    tnj = (nj - 1) / thinout_level / ntile + 1

    byte_data = bytearray(data)

    for ty in range(0, ntile):
        for tx in range(0, ntile):
            lx = (tni - 1) * thinout_level * tx

            bin_tile_data = bytearray()
            i = 0
            prev_byte1 = 0
            prev_byte2 = 0

            for y in range(0, tnj):
                base_y = ni * thinout_level * ((tnj - 1) * ty + y)

                for x in range(0, tni):
                    t = base_y + lx + thinout_level * x
                    dt = int(math.floor((t) * 12 / 8.))

                    if i % 2 == 0:
                        prev_byte1 = byte_data[dt]
                        prev_byte2 = byte_data[dt+1]

                    else:
                        byte3 = byte_data[dt]
                        byte4 = byte_data[dt+1]

                        bin_tile_data.append(prev_byte1)
                        bin_tile_data.append((prev_byte2 & 0b11110000) | (byte3 >> 4))
                        bin_tile_data.append(((byte3 & 0b00001111) << 4) | (byte4  >> 4))

                    i += 1

            if (tnj % 2 == 1):
                bin_tile_data.append(prev_byte1)
                bin_tile_data.append(prev_byte2)

            file = directory + '/%d_%d.bin' % (tx, ty)
            f = open(file, 'w')
            f.write(bin_RED + bytes(bin_tile_data))
            f.close()
            files.append(file)

    return files


def to_tile_raw(directory, data, bin_RED):
    file = directory + '/0_0.bin'
    f = open(file, 'w')
    f.write(bin_RED + data)
    f.close()

    return [ file ]

