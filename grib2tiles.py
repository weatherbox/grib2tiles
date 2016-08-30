import sys
import os
from msm import MSM
import datetime
import numpy as np
import bitstruct

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

        level = msm.level(
            pdt['first_fixed_surface_type'],
            pdt['first_fixed_surface_scale_factor'],
            pdt['first_fixed_surface_scale_value'])
        element = msm.parameter(
            pdt['parameter_category'],
            pdt['parameter_number'])

        if level == 'surface' and (element == 'UGRD' or element == 'VGRD'):
            to_tile(data, bin_RED, split=2)
            



def to_tile(data, bin_RED, **kwargs):
    print data[0:3]
    



if __name__ == '__main__':
    file = sys.argv[1]
    msm_to_tiles(file)

