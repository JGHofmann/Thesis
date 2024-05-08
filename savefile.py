# savefile.py
# written by Veit Wagner
#  save data in 1. Ac-Institue format
# usage:
#  from meas.savefile import savefile
# v0.01 01.11.2022 initial version (based on scilab  meas/savefile.sci)

import numpy as np

# -----------------------------------------
# saves standard data file (typically created by Stala and other Lab equipment)
# input:    filename    filename with path (existing files will overwritten!)
#           x           vector of x-values
#           y           matrix of y-values (usually as cloumns of vectors)
#           cmt         list of strings with comments (1st is line 4, afterwards all lines below data) (optional)
#           fmtstrx     printf-format string for x values (dflt = '%f') (optional)
#           fmtstry     printf-format string for y values (dflt = '%e') (optional)
# -----------------------------------------
def svspec(filename, x, y, cmt=[''], fmtstrx='%f', fmtstry='%e'):  # ret:  -
    #if((argn(2)<1) | (length(filename)==0)) then filename = uigetfile("", "c:\"); end    // allow file selection if no name is given
    #if(argn(2)<4) then cmt = ''; end   // dflt = empty cmt
    #if(argn(2)<5) then fmtstrx = '%f'; end   // dflt = '%f'
    #if(argn(2)<6) then fmtstry = '%e'; end   // dflt = '%e'
    if type(cmt) == str:   # convert simple string to 1-element list
        cmt = [cmt]
    xx = np.asarray(x)
    yy = np.asarray(y)
    assert len(xx.shape) == 1, f"x-data must be a vector, found shape={xx.shape}"
    assert len(yy.shape) == 1  or  len(yy.shape) == 2 , f"y-data must be a vector or matrix, found shape={yy.shape}"
    n = len(xx)
    assert n == max(yy.shape), f"y-data must match x-data of n={n} elements, but shape of y={yy.shape}"
    # transpose if needed
    if yy.shape[0] != n:
        yy = yy.T
    # if vector -> to matrix
    xx = xx.reshape((n,1))
    if len(yy.shape) == 1:
        yy = yy.reshape((n,1))
    #
    ny = yy.shape[-1]
    # line 1+2: xmin, xmax
    #xmin = min(x); xmax=max(x); xx = xmin + ([0:n-1].')*(xmax-xmin)/(n-1); bool = (max(abs(xx-x))) < 1e-10*max(abs([xmin,xmax]));
    #bool = %F;  // always store x-column explicitly
    #if(~bool) then xmin = 0.0; xmax = 0.0; end
    xmin, xmax = 0.0, 0.0   # always store x-column explicitly
    header = f"{xmin}\n{xmax}\n{n} {ny}\n{cmt[0]}"
    footer = '\n'.join(cmt[1:])
    fmt    = [fmtstrx] + [fmtstry]*ny
    MM     = np.concatenate((xx,yy), axis=-1)
    np.savetxt(filename, MM, fmt, delimiter='\t', header=header, footer=footer, comments='')

# --------------------------------------
# example usage    
if __name__ == "__main__":
    from meas.savefile import savefile
    x = np.arange(5)
    y = np.asarray([[4, 2.3, 1, 6, 2],
                    [2, 2.2, 2.5, 2.7, 2.9]]).T
    svspec('tmp.dat', x, y, ['comment1', 'comment2', 'comment3'])
    