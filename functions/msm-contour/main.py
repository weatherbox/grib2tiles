import sys
import os
import glob
import datetime
import boto3
import logging
import json
import re
import Queue
from threading import Thread

import grib2tiles
from msm import MSM

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

queue = Queue.Queue()

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
 

def upload_files(files):
    for file in files:
        queue.put(file)

    for i in range(10):
        thread = Thread(target=upload_worker)
        thread.start()

    return queue.join()


def upload_worker():
    while not queue.empty():
        file = queue.get()

        key = file[5:]
        s3_client.upload_file(file, 'msm-tiles', key)

        queue.task_done()


def create_tile_json(tile_json):
    if 'surface' in tile_json:
        tile_json['surface']['valid_time'] = tile_json['surface']['valid_time'].keys()
        tile_json['surface']['valid_time'].sort() 
        tile_json['surface']['elements'] = tile_json['surface']['elements'].keys()

    elif 'upperair' in tile_json:
        tile_json['upperair']['valid_time'] = tile_json['upperair']['valid_time'].keys()
        tile_json['upperair']['elements'] = tile_json['upperair']['elements'].keys()
        tile_json['upperair']['levels'] = tile_json['upperair']['levels'].keys()
        tile_json['upperair']['levels'].sort(reverse=True)

    tile_json_file = '/tmp/tile.json'
    file = open(tile_json_file, 'w')
    file.write(json.dumps(tile_json))
    file.close()

    return tile_json_file


def main(grib):
    logging.info("start processing: " + grib)
    files, file_type, tile_json = msm_to_tiles(grib)

    logger.info("start uploading to s3://msm-tiles %d files", len(files))
    upload_files(files)
    logger.info("done uploading files")

    # tile.json
    tile_json_file = create_tile_json(tile_json)
    key = '/'.join(['tiles', tile_json['ref_time'], 'tile-' + file_type + '.json'])
    s3_client.upload_file(tile_json_file, 'msm-tiles', key)
    logger.info("uploaded tile.json")


# called by aws lambda
def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        file = '/tmp/' + key.replace('/', '-')

        s3_client.download_file('msm-data', key, file)
        main(file)


if __name__ == '__main__':
    grib = sys.argv[1]
    main(grib)

