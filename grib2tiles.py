import sys
import os
from msm import MSM
import datetime
import numpy as np
import bitstruct
import math

def msm_to_tiles(file):
    msm = MSM(file)
    
    msm.parse_section0()
    sec1 = msm.parse_section1()
    sec3, grid = msm.parse_section3()

    ref_time = datetime.datetime(
        sec1['year'][0],        
        sec1['month'][0],        
        sec1['day'][0],
        sec1['hour'][0],
        sec1['minute'][0],
        sec1['second'][0]
    )
    ref_time_str = ref_time.strftime('%Y%m%d%H%M')

    while not msm.is_end_section():
        sec4, pdt = msm.parse_section4()
        sec5, drt, bin_RED = msm.parse_section5(True)
        msm.parse_section6() # not used
        sec7, data = msm.parse_section7()

        ft = pdt['forecast_time'][0]
        forecast_time = ref_time + datetime.timedelta(hours=int(ft))
        forecast_time_str = forecast_time.strftime('%Y%m%d%H%M')
        level = msm.level(
            pdt['first_fixed_surface_type'],
            pdt['first_fixed_surface_scale_factor'],
            pdt['first_fixed_surface_scale_value'])
        element = msm.parameter(
            pdt['parameter_category'],
            pdt['parameter_number'])
            
        directory = '/'.join(['tiles', ref_time_str, forecast_time_str, level, element])

        if level == 'surface' and (element == 'UGRD' or element == 'VGRD'):
            to_tile(directory, data, bin_RED, ni=481, nj=505, level=2)
            to_tile(directory, data, bin_RED, ni=481, nj=505, level=1, thinout=1)
            
        elif element == 'UGRD' or element == 'VGRD': # upper
            to_tile(directory, data, bin_RED, ni=241, nj=253, level=1)


def to_tile(dir, data, bin_RED, ni, nj, level=1, thinout=0):
    ntile = 2 ** level

    directory = dir + '/' + str(level)
    if not os.path.exists(directory):
        os.makedirs(directory)
    print directory

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
                    base_y = ni * (ty + y)
                    bx1 = int(math.floor((base_y + lx1) * 12 / 8.))
                    bx2 = int(math.ceil((base_y + lx2) * 12 / 8.))
                    d = data[bx1:bx2]

                    if ((base_y + lx1) * 12) % 8 == 4:
                        tile_data.extend(list(bitstruct.unpack('p4' + format_row, d)))
                    else:
                        tile_data.extend(list(bitstruct.unpack(format_row, d)))

                bin_tile_data = bitstruct.pack(format_row * tnj, *tile_data)

                f = open(directory + '/%d_%d.bin' % (tx, ty), 'w')
                f.write(bin_RED + bin_tile_data)
                f.close()

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
                    base_y = ni * (thinout_level * ty + y)
                    bx1 = int(math.floor((base_y + lx1) * 12 / 8.))
                    bx2 = int(math.ceil((base_y + lx2) * 12 / 8.))
                    d = data[bx1:bx2]

                    if ((base_y + lx1) * 12) % 8 == 4:
                        tile_data.extend(list(bitstruct.unpack('p4' + format_row, d)))
                    else:
                        tile_data.extend(list(bitstruct.unpack(format_row, d)))

                bin_tile_data = bitstruct.pack('u12' * tni * tnj, *tile_data)

                f = open(directory + '/%d_%d.bin' % (tx, ty), 'w')
                f.write(bin_RED + bin_tile_data)
                f.close()


if __name__ == '__main__':
    file = sys.argv[1]
    msm_to_tiles(file)

