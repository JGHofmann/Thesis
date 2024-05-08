# rduvvis.py
# written by Veit Wagner
#  --- loads text data files in 1.Ac Institute format (experimental data) ---
# v0.01 19.09.2022 initial version
#
# usage:
#  from ..meas import rduvvis
#  x,y,p,cmt = rduvvis('/bufa/vj180509/VJ180905.SP')
import numpy as np

# -----------------------------------------
# reads PerkinElmer lambda 9 UV/VIS data file
# -----------------------------------------
def rduvvis(filename=None):      # ret:  x,y,p,cmt
    # --- read whole file ---
    with open(filename) as f:
        aa = f.readlines()
        
    # --- treat read  contents ---
    # line 1: PE UV                   SPECTRUM    ASCII       PEDS        1.60
    p = {}    # initialize dictionary parameters returned
    cmt = []  # initialize comments found
    n = 0     # initialize no of datalines to read
    while len(aa) > 0:
        a = aa.pop(0).rstrip()
        cmt.append(a)
        if len(a)>=3 and (a[0:3] == "#GR"):
            # line was : #GR
            a = aa.pop(0).rstrip()
            p['xaxis'] = a             # NM
            a = aa.pop(0).rstrip()
            p['yaxis'] = a             # %T
            a = aa.pop(0)           # 0.00002384185791015625        ??
            a = aa.pop(0)           # 0.0                ??
            a = aa.pop(0)           # 800.0000000    [xmax]
            p['xmax'] = float(a)
            a = aa.pop(0)           # 0.50000000    [xstep]
            p['xstep'] = float(a)
            a = aa.pop(0)           # 1201          [ndata]
            p['ndata'] = int(a)
            a = aa.pop(0)           # 8                 ??
            a = aa.pop(0)           # 99.453000    [ymax]
            p['ymax'] = float(a)
            a = aa.pop(0)           # 61.459000    [ymin]
            p['ymin'] = float(a)
            n = p['ndata']
        elif len(a)>=5 and (a[0:5] == "#DATA"):
            # line was : #DATA
            m = np.asarray([[float(txt) for txt  in a.split('\t')] for a in aa[:n] if len(a)>1])
            x = m[:,0]
            y = m[:,1]
            break
            
    return x,y,p,cmt

