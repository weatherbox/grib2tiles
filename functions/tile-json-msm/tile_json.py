import sys
import logging
import json

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def main(ref_time):
    logging.info("start processing: " + ref_time)
    prefix = 'tiles/' + ref_time + '/tile'
    response = s3_client.list_objects(Bucket='msm-tiles', Prefix=prefix)

    if 'Contents' in response:
        keys = [content['Key'] for content in response['Contents']]
        if len(keys) == 6:
            tile_json_file = create_tile_json(ref_time, keys)
            s3_client.upload_file(tile_json_file, 'msm-tiles', 'tiles/tile.json',
                ExtraArgs={'ContentType': "application/json"})
            logger.info("done updating tile.json")

        else:
            logger.info("pass: %d tile.jsons", len(keys))


def create_tile_json(ref_time, keys):
    host = 'http://msm-tiles.s3-website-ap-northeast-1.amazonaws.com'
    tile_json = {
        'ref_time': ref_time,
        'url': host + '/tiles/' + ref_time + '/{valid_time}/{e}/{z}/{x}_{y}.bin',
        'surface': {
            'elements': [],
            'valid_time': []
        },
        'upperair': { 
            'elements': [],
            'valid_time': [],
            'levels': []
        }   
    }

    for key in keys:
        file = '/tmp/' + key.replace('/', '-')
        s3_client.download_file('msm-tiles', key, file)

        f = open(file)
        data = json.load(f)
        f.close()
    
        if 'surface' in data:
            tile_json['surface']['valid_time'].extend(data['surface']['valid_time'])
            tile_json['surface']['elements'].extend(data['surface']['elements'])

        elif 'upperair' in data:
            tile_json['upperair']['valid_time'].extend(data['upperair']['valid_time'])
            tile_json['upperair']['elements'].extend(data['upperair']['elements'])
            tile_json['upperair']['levels'].extend(data['upperair']['levels'])

    # uniquify and sort
    tile_json['surface']['valid_time']  = sorted(list(set(tile_json['surface']['valid_time'])))
    tile_json['surface']['elements']    = sorted(list(set(tile_json['surface']['elements'])))
    tile_json['upperair']['valid_time'] = sorted(list(set(tile_json['upperair']['valid_time'])))
    tile_json['upperair']['elements']   = sorted(list(set(tile_json['upperair']['elements'])))
    tile_json['upperair']['levels']     = sorted(list(set(tile_json['upperair']['levels'])), reverse=True)

    tile_json_file = '/tmp/tile.json'
    file = open(tile_json_file, 'w')
    file.write(json.dumps(tile_json))
    file.close()

    return tile_json_file
    

def handler(event, context):
    for record in event['Records']:
        key = record['s3']['object']['key']
        ref_time = key[6:18]
        main(ref_time)

if __name__ == '__main__':
    main(sys.argv[1])

