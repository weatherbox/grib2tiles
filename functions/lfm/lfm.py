import sys
import numpy as np

from msm import MSM 

class LFM(MSM):

    def parse_section6(self, return_bitmap=False):
        section6_dtype = np.dtype([
            ('length', '>u4'),
            ('section_number', 'u1'),
            ('bitmap_indicator', 'u1')
        ])
        sec6 = np.fromfile(self.fileptr, dtype=section6_dtype, count=1)

        if sec6['bitmap_indicator'] == 254:
            return sec6

        elif sec6['bitmap_indicator'] == 0:
            bitmap = self.fileptr.read(sec6['length'] - 6)

            if return_bitmap:
                return sec6, bitmap

            else:
                return sec6


if __name__ == '__main__':
    file = sys.argv[1]
    lfm = LFM(file)
    lfm.parse()
