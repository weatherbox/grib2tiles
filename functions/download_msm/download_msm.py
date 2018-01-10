import sys
import os

import datetime
import urllib2

import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

source = "http://database.rish.kyoto-u.ac.jp/arch/jmadata/data/gpv/original/"

def download(date):
    filetypes = [
        "Lsurf_FH00-15", "Lsurf_FH16-33", "Lsurf_FH34-39",
        "L-pall_FH00-15", "L-pall_FH18-33", "L-pall_FH36-39"
    ]

    for filetype in filetypes:
        filename = "Z__C_RJTD_" + date + "00_MSM_GPV_Rjp_" + filetype + "_grib2.bin"
        url = source + "/".join([date[0:4], date[4:6], date[6:8], filename])
        download_file(url, filename, date)


def download_file(url, filename, date):
    logging.info('start downlaoding: ' + url)
    try:
        response = urllib2.urlopen(url)
        content = response.read()
    except urllib2.HTTPError as e:
        print("[Error] " + str(e.code) + ": " + e.reason + " " + url)
        return

    file = '/tmp/' + filename
    f = open(file, 'w')
    f.write(content)
    f.close()
    logging.info('saved to ' + file)

    key = '/'.join([date, filename])
    logging.info('start uploading: ' + key)
    s3_client.upload_file(file, 'msm-data', key)
    logging.info('done uploading')


def handler(event, context):
    now = datetime.datetime.utcnow()
    dh = now.hour % 3 + 3
    d = now - datetime.timedelta(hours=dh)
    date = d.strftime('%Y%m%d%H00')
    logging.info('start processing: ' + date)

    download(date)


if __name__ == '__main__':
    date = sys.argv[1]
    download(date)

