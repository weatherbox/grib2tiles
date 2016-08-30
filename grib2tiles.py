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

    date = datetime.datetime(
        sec1['year'][0],        
        sec1['month'][0],        
        sec1['day'][0],
        sec1['hour'][0],
        sec1['minute'][0],
        sec1['second'][0]
    )
    print date

    while not msm.is_end_section():
        sec4, pdt = msm.parse_section4()
        sec5, drt, bin_RED = msm.parse_section5(True)
        msm.parse_section6() # not used
        sec7, data = msm.parse_section7()

        ft = pdt['forecast_time'][0]
        level = msm.level(
            pdt['first_fixed_surface_type'],
            pdt['first_fixed_surface_scale_factor'],
            pdt['first_fixed_surface_scale_value'])
        element = msm.parameter(
            pdt['parameter_category'],
            pdt['parameter_number'])

        if level == 'surface' and (element == 'UGRD' or element == 'VGRD'):
            print ft, level, element
            to_tile(data, bin_RED, ni=481, nj=505, split=2)
            



def to_tile(data, bin_RED, ni, nj, split=1):
    nsplit = 2 ** split
    tni = (ni - 1) / nsplit + 1
    tnj = (nj - 1) / nsplit + 1

    for ty in range(0, nsplit):
        for tx in range(0, nsplit):
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

                if lx1 % 8 == 4:
                    tile_data.extend(list(bitstruct.unpack('p4' + format_row, d)))
                else:
                    tile_data.extend(list(bitstruct.unpack(format_row, d)))

            bin_tile_data = bitstruct.pack(format_row * tnj, *tile_data)


if __name__ == '__main__':
    file = sys.argv[1]
    msm_to_tiles(file)

