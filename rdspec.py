# rdspec.py
# written by Veit Wagner
#  --- loads text data files in 1.Ac Institute format (experimental data) ---
# v0.01 19.09.2022 initial version
# v0.02 12.07.2023 allow not unicode text files -> open with encoding='latin1'
#
# usage:
#
import numpy as np

# -----------------------------------------
# reads standard data file (typically created by Stala and other Lab equipment)
# input:    filename    filename with path to file to be loaded
# output:   x           numpy vector of x-values
#           y           numpy matrix of y-values
#           cmt         list of strings with comments (1st is line 4, afterwards all lines below data)
#           npar        list of integer from line 3 (1st two: n, ncol; following: nxx, njw, nrev1, n1, nglob, nrev2, n2, n0V) 
# -----------------------------------------
def rdspec(filename):    # -> [x,y,cmt,npar]
#if((argn(2)<1) | (length(filename)==0)) then filename = uigetfile("", "c:\"); end    // allow file selection if no name is given
    #[f,err] = mopen(filename, 'r');
    #if(err ~= 0) then error(sprintf("rdspec: cant open file %s for reading.", filename)); end
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filename, 'r', encoding='latin1') as f:   # try old text coding for e.g. german ü
            lines = f.readlines()
    # line 1+2: xmin, xmax
    xmin = float(lines[0].split()[0])
    xmax = float(lines[1].split()[0])
    # line 3: nx, ny [, ..]
    npar = [int(d) for d in lines[2].split()] # msscanf(a, "%d %d %d %d %d %d %d %d %d %d");
    assert len(npar) >= 2, f"rdspec: less than 2 parameters, i.e. {len(npar):d}, for n, ncol in file {filename} in line 3: {lines[2]}"
    n, ncol = npar[:2]
    # line 4: comment line
    cmt = lines[3].rstrip()
    if len(cmt) == 0:
        cmt = "  "   # ensure cmt is counted as the 1st line
    # line 5ff: data block -> x,y
    m = np.asarray([np.fromiter(l.split(), float, count=ncol) for l in lines[4:4+n]]).T
    if xmin != xmax:
        x = np.linspace(xmin, xmax, n)
        y = m                             #  y = matrix(mfscanf(n*(ncol), f, "%lf"), ncol, n)';
    else:
        # m = matrix(mfscanf(n*(ncol+1), f, "%lf"), ncol+1, n)';
        x = m[0]
        y = m[1:]
    # lines after data block: further comments
    cmt = [ cmt , *[l.rstrip()  for l in lines[4+n:]] ]
    return x,  y, cmt, npar
#
# memo meaning npar (see rdstala()):
#   nn_n, nn_ncol, nn_nxx, nn_njw, nn_nrev1, nn_n1, nn_nglob, nn_nrev2, nn_n2, nn_n0V = npar
