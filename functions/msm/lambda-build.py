import os
import shutil
import datetime


if __name__ == '__main__':
    date = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    package = 'lambda-grib2tiles-msm-' + date + '.zip'
    shutil.copy('lambda-numpy.zip', package)

    for file in ['bitstruct.py', 'grib2tiles.py', 'msm.py', 'main.py']:
        os.system('zip -9 ' + package + ' ' + file) 

    print 'created deploy package ' + package
