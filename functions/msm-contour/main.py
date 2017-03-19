import sys
import os
import datetime
import boto3
import logging
import json
import Queue
from threading import Thread

from msm import MSM

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

queue = Queue.Queue()

def msm_to_tiles(file):
    msm = MSM(file)
    files = []

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
        sec5, drt = msm.parse_section5()
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

        #directory = '/tmp/' + '/'.join(['tiles', ref_time_str, valid_time_str, level, element])
        directory = '/'.join(['countour', ref_time_str, valid_time_str, level, element])

        if level == 'surface' and element == 'PRES':
            print MSM.decode(data, drt, grid['ni'], grid['nj'])


        logger.info(directory)

    return files
 

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



def main(grib):
    logging.info("start processing: " + grib)
    files = msm_to_tiles(grib)

    logger.info("start uploading to s3://msm-tiles %d files", len(files))
    #upload_files(files)
    logger.info("done uploading files")



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

