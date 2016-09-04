import sys
import os
from msm import MSM
import datetime
import grib2tiles

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
            grib2tiles.to_tile(directory, data, bin_RED, ni=481, nj=505, level=2)
            grib2tiles.to_tile(directory, data, bin_RED, ni=481, nj=505, level=1, thinout=1)
            
        elif element == 'UGRD' or element == 'VGRD': # upper
            grib2tiles.to_tile(directory, data, bin_RED, ni=241, nj=253, level=1)

if __name__ == '__main__':
    file = sys.argv[1]
    msm_to_tiles(file)

