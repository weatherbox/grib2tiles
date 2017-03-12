import sys
import os
import glob
import datetime
import logging
import json
import re
import Queue
from threading import Thread

import grib2tiles
from msm import MSM

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def msm_to_tiles(file):
    msm = MSM(file)
    files = []
    tile_json = {}
    file_type = re.findall(r"L[^_]+_FH[^_]+", file)[0]
    if re.match(r"Lsurf", file_type):
        tile_json['surface'] = {
            'elements': {},
            'valid_time': {}
        }
    else:
        tile_json['upperair'] = {
            'elements': {},
            'levels': {},
            'valid_time': {}
        }

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
    tile_json['ref_time'] = ref_time_str

    while not msm.is_end_section():
        sec4, pdt = msm.parse_section4()
        sec5, drt, bin_RED = msm.parse_section5(True)
        msm.parse_section6() # not used
        sec7, data = msm.parse_section7()

        ft = pdt['forecast_time'][0]
        valid_time = ref_time + datetime.timedelta(hours=int(ft))
        valid_time_str = valid_time.strftime('%Y%m%d%H%M')
        level = msm.level(
            pdt['first_fixed_surface_type'],
            pdt['first_fixed_surface_scale_factor'],
            pdt['first_fixed_surface_scale_value'])
        element = msm.parameter(
            pdt['parameter_category'],
            pdt['parameter_number'])

        directory = '/tmp/' + '/'.join(['tiles', ref_time_str, valid_time_str, level, element])

        if level == 'surface':
            tile_json['surface']['valid_time'][valid_time_str] = 1
            tile_json['surface']['elements']['wind'] = 1

            files.extend(grib2tiles.to_tile(directory, data, bin_RED, ni=481, nj=505, level=1))
            files.extend(grib2tiles.to_tile(directory, data, bin_RED, ni=481, nj=505, level=0, thinout=1))

        else:
            tile_json['upperair']['valid_time'][valid_time_str] = 1
            tile_json['upperair']['elements']['wind'] = 1 
            tile_json['upperair']['levels'][int(level)] = 1

            files.extend(grib2tiles.to_tile(directory, data, bin_RED, ni=241, nj=253, level=0))

        logger.info(directory)

    return files, file_type, tile_json



def main(grib):
    logging.info("start processing: " + grib)
    files, file_type, tile_json = msm_to_tiles(grib)



if __name__ == '__main__':
    grib = sys.argv[1]
    main(grib)

