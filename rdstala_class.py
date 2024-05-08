# rdstala_class.py
# written by Veit Wagner
# --- collection of routines to load/save and handle stala data (experimental data measured by stala-setup) ---
# v0.01 19.09.2022? initial version
# v0.02 24.02.2023 several bug fixes to get it working ; renamed file stala_class.py -> rdstala_class.py

# usage:
#

import numpy as np
import re
from meas.rdspec import rdspec

class rdstala_class:
    def __init__(self, filename=None): #"/buffer/tmp.dat"):
        self.filename = None
        self.x        = None
        self.y        = None
        self.z        = None
        self.cmt      = None
        self.npar     = None
        self.p        = None
        if filename is not None:
            self.rdstala(filename)

    # -----------------------------------------
    # reads stala standard data file (typically created by Stala and other Lab equipment)
    # -----------------------------------------
    # readfile (based on scilab code: readfile.sci v0.12 status 14.06.2018)
    def rdstala(self, filename=None):
        if filename is not None:
            self.filename = filename
        assert self.filename is not None, "No filename was given to read from"
        x, y, cmt, npar  = rdspec(self.filename)    # read complete file
        self.cmt, self.npar = cmt, npar  # assign alread for self.stalainfo() call below
        # for stala: npar = [n, ncol, nxx, njw, nrev1, n1, nglob, nrev2, n2, n0V]
        npar_dflt = [npar[0], npar[1], 0, 1, 1, 1, 1, 1, npar[0], 0 ]    # default stala npar-values (it's forbidden, that nrev2 is given but n2 not !)
        npar      = [*npar, *npar_dflt[len(npar):] ]    # use val. from default if npar is to short
        nn_n, nn_ncol, nn_nxx, nn_njw, nn_nrev1, nn_n1, nn_nglob, nn_nrev2, nn_n2, nn_n0V = npar
        # reshape x if nxx>0 :
        if nn_nxx > 0:
            x = np.vstack([x.reshape(1,(len(x))), y[0:nn_nxx,:]])   # x = cat(2,x,y(:, 1:nn.nxx));
            y = y[nn_nxx:,:]                                        # y = y(:, (1+nn.nxx):$);
        # analyze cmt data :
        if True: # p-return <=> (argn(1)>=4) then 
            p = self.stalainfo()
            assert (p['rev1']+1 == nn_nrev1) and (p['n1'] == nn_n1), "xxx"   # consistency check
            # compute z
            #a = self.xramp0_init(p)
            #z = self.xramp0(a)
            z = self.xramp0( self.xramp0_init(p) )
            if p['rev1'] > 0  :   # was: if(p.rev1>1) then
                z0   = z
                zrev = z0[-2::-1]    # skipping 1st value on repeats
                zfwd = z0[1:]        #     "
                for i in range(1, p['rev1']+1): # =1:p.rev1 do
                    if i % 2 == 0:
                        z += zfwd
                    else:
                        z += zrev
            # end of compute z
        #self.cmt, self.npar = cmt, npar  (already done, s.a.)
        self.x, self.y, self.z, self.p = x, y, z, p
        return x, y

    # -----------------------------------------
    # calculates proper y-col index for multi-sample stala data files
    # input:     npar     parameters returned by rdstala()
    #            iglob    sample index (0, 1, 2, 3, .. nn.nglob-1)
    #            iz       curves index (i1=0, 1, 2, 3, .. (1+nn.nrev1*(nn.n1-1))-1 ) e.g. next gate voltage in output curves [optional parameter]
    #            idat     data index (i=0, 1, 2, .. nn.njw)-1 e.g. selects between Id, Ig, Is [optional parameter]
    # output:    icol     y-column index -> y[icol,:] of y-data returned by rdstala()
    # -----------------------------------------
    def scol(self, iglob=0, iz=0, idat=0):    # ->  icol
        nn_n, nn_ncol, nn_nxx, nn_njw, nn_nrev1, nn_n1, nn_nglob, nn_nrev2, nn_n2, nn_n0V = self.npar
        icol = idat + nn_njw * (iz + (1+nn_nrev1*(nn_n1-1)) * iglob );
        return icol
    
    
    
    # -----------------------------------------
    # extracts measurement, sample, etc. parameters from comment lines of standard data file (typically created by Stala and other Lab equipment)
    # -----------------------------------------
    def stalainfo(self, p={"comment":"", "settle_time":0.0, "nplc":0.0, "intg_time":0.0, "period":0.0,"z_start":0.0, "z_step":0.0, "delay0":0.0, "delay1":0.0, "njw":1, "n1":1, "rev1":0, "nsample":1, "ramp_catchup":1, "full_settletime":0, "xr_linlog":0, "xr_uselist":0, "xr_list":np.array([],dtype=np.float_), "sample":"", "operator":"", "date":"", "time_since_start":0.0, "id":"", "T":0.0, "RH":0.0, "swb_time":0.0, "swb_type":0, "s_idx":[], "s_iref":[], "s_slot":[], "s_mask":[], "s_dev":[], "s_sample":[], "s":[], "filename":"", "col_info":"", "id_meas":"", "remote_sensing":False}):   # -> p
        rname = "stalainfo";
        cmt, npar = self.cmt, self.npar
        # optional field in p: "z_end", 0.0, (exists if xramp with log) 
        # optional field in p: "z_end", 0.0, (exists if impedance) 
        n = len(cmt) #size(cmt, '*');
        #
        while True :   # <- break-statement allows to jump to end
            # line 1: <cmt>
            if n<1: break
            p['comment'] = cmt[0]

            # line 2: ;settle time (ms): 100.000000  ; nplc (20ms):  0.00 ; intg.time (ms): 0.000000 ; period (s): 0.000000
            if n<2 : break
            a = cmt[1].split(':')
            assert a[0] == ';settle time (ms)'
            p['settle_time'] = float( a[1].split(';')[0] ) * 1e-3    # [s]
            p['nplc']        = float( a[2].split(';')[0] )           # [20ms] or [16.6667ms]
            p['intg_time']   = float( a[3].split(';')[0] ) * 1e-3    # [s]
            p['period']      = float( a[4].split(';')[0] )           # [s]

            # line 3: ;z-start(V) z-step(V) extrapause at start and scan (ms): 0.000000 0.500000 0.000000 0.000000  ; njw n1 rev1 nsample: 8 1 0 1 ; ramp_catchup full_settletime: 1 0 ; xramp> linlog uselist [list]: 0 0
            if  n<3: break
            a = cmt[2].split(':')
            assert a[0][:8] == ';z-start'
            aa = a[0].split()  # aa[1] = "z-step(Hz)" "z-step(V)" or  "z-end(Hz)"  "z-end(V)"
            zz = a[1].split()  # 1st four are the numbers
            p['z_start'] = float( zz[0] )    # [?] Hz or V or ..
            p['z_step']  = float( zz[1] )    # [?] Hz or V or ..
            if aa[1][:5] == "z-end":          # position to store z_end if linlog=1
                p['z_end']  = float( zz[1] )    # [?] Hz or V or ..
            p['delay0'] = float( zz[2] )*1e-3 # [s] pause at start
            p['delay1'] = float( zz[3] )*1e-3 # [s] pause at start of each scan
            #
            nn = [int(z) for z in a[2].split()[:4]] if len(a) > 2  else [1, 1, 0, 1]   # njw n1 rev1 nsample
            p['njw']     = nn[0]
            p['n1']      = nn[1]
            p['rev1']    = nn[2]
            p['nsample'] = nn[3]
            #
            f1 = [int(z) for z in a[3].split()[:2]] if len(a) > 3  else [1, 1]   # ramp_catchup full_settletime
            p['ramp_catchup']    = f1[0]
            p['full_settletime'] = f1[0]
            #
            azxr = a[4].split() if len(a) > 4  else ['0', '0', '0']   # linlog uselist [n_list list] (for xramp)
            if azxr[0]=='1' and azxr[1]=='0' and aa[1][:5]=="z-end":  # outdated position to store z_end
                p['z_end'] = float( azxr[2] )  # outdated position to store z_end  ,was aax = msscanf(a(5), "%d %d %f");
            p['xr_linlog']  = int( azxr[0] );
            p['xr_uselist'] = int( azxr[1] );
            p['xr_list']    = np.asarray([float(az) for az in azxr[2:]], dtype=np.float_)  if p['xr_uselist']    else  np.array([], dtype=np.float_)

            # line 4: ;sample: -,"empty"
            #         ;sample: VJ190401,"","","","","","",""
            #         ;sample: SPM163,"SPM163 2A1","SPM163 2A1","SPM163 2A1"
            if n<4: break
            a = cmt[3].split(':', 1)                        # https://docs.python.org/3/library/re.html
            b = a[1].split(',', 1) if len(a)>1 else ['']           # separate sample by "," to b[0]
            A = re.findall(r'"[^"]*"', b[1]) if len(b)>1 else []   # get slot-samples by searching for quoted text by regex ".." to A
            #print("cmt[3]:", cmt[3])
            #print("a:", a)
            #print("b:", b)
            #print("A:", A)
            assert a[0][:7] == ';sample'
            p['sample'] = b[0].strip()
            p['s_sample'] = [s[1:-1] for s in A]   # list of sample names per slot w/ stripped quotes
            #print("p['sample']:", p['sample'])
            #print("p['s_sample']:", p['s_sample'])

            # line 5: ;operator: vw
            if n<5: break
            a = cmt[4].split(':')
            assert a[0][:9] == ';operator' or a[0][:5] == ';user'
            p['operator'] = a[1].strip()

            # line 6:      ;date: 04-19-2012 15:19:09 ;  time since start (s) : 0.114707
            #   v2.12.03:  ;date: 04-26-2019 11:19:13
            if n<6: break
            a = cmt[5].split(':', 1)
            assert a[0][:5] == ';date'
            aa = a[1].split(';')
            #print("cmt[5]:", cmt[5])
            #print("a:", a)
            #print("aa:", aa)
            p['date'] = aa[0].strip()   # = "04-19-2012 15:19:09"
            p['time_since_start'] = float( aa[1].split(':')[1] )  if len(aa) > 1 else 0.0  # = 0.114707

            # line 7: ;iv curve - stala v2.12.05
            #         ;impedance vs frequency (Cp-Rp); ; Vac (V) #average: 0.500000 1; time mode: MED - stala v2.05pre
            #         ;transfer curve - stala v1.02
            #         ;transfer curve (on/off) - stala v1.02
            if n<7: break
            ipos = 6
            a = re.split(' - |;|:', cmt[ipos]) # .split('strsplit(cmt(7), strindex(cmt(7),[" - ", ";", ":"])); //xx
            p['version'] = a[-1].strip()    # part(a($), 3:length(a($))); //xx
            aa = p['version'].split('v', 1)[1].strip() # "%lf.%d %s"
            aaa  = aa.split(".", 1)
            #print('cmt[ipos]:', cmt[ipos])
            #print('a:', a)
            #print('aa:', aa)
            #print('aaa:', aaa)
            if len(aaa):
                i=0
                for c in aaa[1]:
                    if not c.isnumeric(): break
                    i += 1
                txt_frac = aaa[1][:i]
            else:
                txt_frac = ""
            #txt_frac       = "".join([c if c.isnumeric() else ""  for c in aaa[1] ])  if len(aaa) else ""  # take only initial digits
            p['ver_no']    = float( ".".join([aaa[0], txt_frac]) )
            is_subno       = ( len(aaa)>0 and len(aaa[1])>len(txt_frac) and aaa[1][len(txt_frac)]=='.' )
            txt_subno      = "".join([c if c.isnumeric() else ""  for c in aaa[1][len(txt_frac)+1:] ])  if is_subno else "0"
            p['ver_subno'] = int( txt_subno )
            p['ver_txt']   = aaa[1][(len(txt_frac) + ( (len(txt_subno) + 1) if is_subno else 0)):].strip()  if len(aaa) else ""      # [nn, p.ver_no, p.ver_subno, p.ver_txt] = msscanf(p.version, "stala v%lf.%d %s");
            p['id']        = cmt[ipos][1:].strip()  # part(cmt(7), 2:length(cmt(7)));
            p['id_meas']   = a[1].strip()        # e.g. "impedance vs frequency (Cp-Rp)", "impedance vs voltage (Cp-Rp)", "transfer curve", .. 
            #if( part(p.id_meas, 1:min(length(p.id_meas), length("impedance vs"))) == "impedance vs") then ; end  // <- to be finished, VW 11.08.2017
            #print("txt_frac:", txt_frac)
            #print("is_subno:", is_subno)
            #print("txt_subno:", txt_subno)
            #print("p['ver_no']:", p['ver_no'])
            #print("p['ver_subno']:", p['ver_subno'])
            #print("p['ver_txt']:", p['ver_txt'])
            #print("p['id']:", p['id'])
            #print("p['id_meas']:", p['id_meas'])

            # line 8: ;relative humidity   :  0.000000; sample temp (C):  0.000000
            if n<8: break
            a = cmt[7].split(':')
            assert a[0][:18] == ";relative humidity"
            p['T']  = float( a[1].split(';')[0] )   # [C]
            p['RH'] = float( a[2] )                 # [%]

            # line 9: ;swbtime (ms) : 10.000000 swbtype: 3706
            if n<9: break
            a = cmt[8].split(':')
            assert a[0][:13] == ";swbtime (ms)"
            p['swb_time'] = float( a[1].strip().split()[0] ) * 1e-3  # [s]
            p['swb_type'] = [int(s) for s in a[2].strip().split()]   # [-]    msscanf(a(3),"%d %d %d %d %d %d %d %d %d");

            # line 10: ;nch: 1   name: dev1
            if n<10: break

            # line 11: ;idx                :	1	2 
            if n<11: break
            a = cmt[10].split(':', 1)
            assert a[0][:4] == ";idx"
            idx = [int(s) for s in a[1].split()]
            p['s_idx'] = idx

            # line 12: ;ref-list (slot/pos):	17001	1702
            if n<12: break
            a = cmt[11].split(':', 1)
            assert a[0][:9] == ";ref-list"
            ref = [int(s) for s in a[1].split()]
            p['s_iref'] = ref

            # line 13: ;slot-list          :	imped01	slot01
            if n<13: break
            a = cmt[12].split(':', 1)
            assert a[0][:10] == ";slot-list"
            slo = a[1].split()
            p['s_slot'] = slo

            # line 14: ;mask-list          :	mask13	mask2
            if n<14: break
            a = cmt[13].split(':', 1)
            assert a[0][:10] == ";mask-list"
            msk = a[1].split()
            p['s_mask'] = msk

            # line 15: ;dev-list           :	C100	K10
            if n<15: break
            a = cmt[14].split(':', 1)
            assert a[0][:9] == ";dev-list"
            dev = a[1].split()
            p['s_dev'] = dev

            # line 16: ;c:\stala_data\test_imped_x_04_impedf.dat
            if n<16: break
            if p['ver_no'] <= 2.06:
                p['filename'] = cmt[15][1:].strip() # part(cmt(16), 2:length(cmt(16)));
                # line 17: ;
                if n<17: break
                # line 18: ; V/Hz  Cp Rp Vac Iac Vdc Iac  Cp Rp Vac Iac Vdc Iac ..
                if n<18: break
                p['col_info'] = cmt[17][1:].strip() # stripblanks( part(cmt(18), 2:length(cmt(18))), %T);
            else:
                # line 16, stala version >2.06 -> v2.12 : ;start end time (s) :     1.936476   101.554196 ; reference date and 2 time stamps (s) : 13.06.2018 09:27:32   183.035202 0.000000 
                #                               v2.12.03: ;start end time (s) :   304.445056   397.312649 ; reference date and 2 time stamps (s) : 26.04.2019 11:12:35   4873.727502 0.000000
                a = cmt[15].split(':', 2)
                assert a[0][:19] == ";start end time (s)"
                aa  = a[1].split(';')
                aaa = aa[0].strip().split()
                #print("cmt[15]:", cmt[15])
                #print("a:", a)
                #print("aa:", aa)
                #print("aaa:", aaa)
                p['t_start'] = float( aaa[0] )
                p['t_end']   = float( aaa[1] )
                assert aa[1].strip() == "reference date and 2 time stamps (s)"
                bb  = a[2].strip().split() 
                #print("bb:", bb)
                p['t_ref_date']  = bb[0] + " " + bb[1]
                p['t_ref']       = [float(bb[2]), float(bb[3])]
                # line 17, stala version 2.12 : ;dev-start time (s) :	1.936	16.323	30.631	44.857	59.220	72.794	86.689
                if n<17: break
                a = cmt[16].split(':', 1)
                assert a[0][:19] == ";dev-start time (s)"
                p['s_t_start'] = [float(s) for s in a[1].split()]
                # line 18, stala version 2.12 : ; meas_pdev   ba/#  : 3 2
                if n<18: break
                a = cmt[17].split(':', 1)
                assert a[0][:18] == "; meas_pdev   ba/#"
                aa = a[1].strip().split()
                p['meas_pdev'] = int( aa[0] )     # 0=no, 1=before, 2=after, 3=before and after, list only if was measured
                p['n_TRHX']    = int( aa[1] )     #
                # line 19, stala version 2.12 : ;dev-temperature (C):	0.000	0.000	0.000	0.000	0.000	0.000	0.000
                nx_meas_pdev = 0      # # of extra cmt lines for measurements per device data
                ipos = 18             # current cmt line
                if (p['meas_pdev'] & 1): # before meas.
                    p['s_TRHX1']   = np.zeros((p['n_TRHX'], len(p['s_t_start'])))
                    p['lbl_TRHX1'] =  p['n_TRHX'] * [""]
                    assert n > ipos+p['n_TRHX']
                    for i in range(p['n_TRHX']):
                        # line 19, stala version 2.12 : ;dev-temperature (C):	0.000	0.000	0.000	0.000	0.000	0.000	0.000
                        # line 20, stala version 2.12 : ;dev-  rel. humidity:	0.000	0.000	0.000	0.000	0.000	0.000	0.000
                        a = cmt[ipos+i].split(':', 1)
                        p['lbl_TRHX1'][i] = a[0][5:].rstrip()
                        p['s_TRHX1'][i]   = [float(s) for s in a[1].strip().split()] 
                    nx_meas_pdev += p['n_TRHX']
                    ipos         += p['n_TRHX']
                if (p['meas_pdev'] & 2): # after meas.
                    p['s_TRHX2']   = np.zeros((p['n_TRHX'], len(p['s_t_start'])))
                    p['lbl_TRHX2'] = p['n_TRHX'] * [""]
                    assert n > ipos+p['n_TRHX']
                    for i in range(p['n_TRHX']):
                        # line 21, stala version 2.12 : ;dev-end temp.   (C):	0.000	0.000	0.000	0.000	0.000	0.000	0.000
                        # line 22, stala version 2.12 : ;dev-end   rel. hum.:	0.000	0.000	0.000	0.000	0.000	0.000	0.000
                        a = cmt[ipos+i].split(':', 1)
                        p['lbl_TRHX2'][i] = a[0][5:].rstrip()
                        p['s_TRHX2'][i]   = [float(s) for s in a[1].strip().split()] 
                    nx_meas_pdev += p['n_TRHX']
                    ipos         += p['n_TRHX']

                # line 23, stala version 2.12 : ;\\dali\data\data\IV\2018\06\13\180202\180202_iv_dark.dat
                a = cmt[ipos]  # cmt(19+nx_meas_pdev);
                p['filename'] = a[1:].rstrip()
                ipos += 1

                # line 24 (optional),  stala version 2.12 : ; remote sensing
                p['remote_sensing'] = (cmt[ipos].rstrip() == "; remote sensing") if n > ipos  else False
                ipos += 1

                # line 25: ;
                if n <= ipos: break
                ipos += 1

                # line 26: ; V/Hz  Cp Rp Vac Iac Vdc Iac  Cp Rp Vac Iac Vdc Iac ..
                if n <= ipos: break
                a = cmt[ipos]  # (21+nx_meas_pdev+p.remote_sensing);
                p['col_info'] = a[1:].strip()
                # new: t_start, t_end, t_ref_date, t_ref, meas_pdev, n_TRHX, p.s_TRHX1, p.lbl_TRHX1, p.s_TRHX2, p.lbl_TRHX2, p.remote_sensing
            #
            p['s'] = []
            for idx, iref, slot, mask, dev, sample  in zip(p['s_idx'], p['s_iref'], p['s_slot'], p['s_mask'], p['s_dev'], p['s_sample']):
                p['s'].append( {"idx":idx, "iref":iref, "slot":slot, "mask":mask, "dev":dev, "sample":sample} )
            break  # final (needed!) break of  while True:
        return p

    # -----------------------------------------
    # calcs values of xramp (see xramp.c: get_val_xramp0())
    # input:  xr0.
    #           flag       0=lin, 1=log, 2=list, 3=loglist
    #           n          # of values
    #           start      start value used for lin and log
    #           step       step value used for lin, log and loglist
    #           nl         # of val per decade used for loglist
    #           l          list of values used for list and loglist
    # output:   x          vector of x values (#=n)
    # -----------------------------------------
    def xramp0(self, xr0): # -> x
        flag = xr0["flag"]
        if   flag==0: x = xr0["start"] + np.arange(xr0["n"]) * xr0["step"]            # lin
        elif flag==1: x = xr0["start"] * np.exp( np.arange(xr0["n"]) * xr0["step"] )  # log
        elif flag==2: x = np.asarray(xr0["l"])                                        # list
        elif flag==3:                                                                 # loglist
            x = []
            for i in range(xr0["n"]):
                x.append( xr0["l"][i % xr0["nl"]] * np.exp( int(i/xr0["nl"]) * xr0["step"]  ) )   # <- calc to be checked again ??
            x = np.asarray(x)
        else: assert False, f"xramp0: illegal flag parameter {flag} (allowed 0=lin, 1=log, 2=list, 3=loglist)"
        return x

    # -----------------------------------------
    # calcs values of xramp (similar to xramp.c: xramp2xramp0())
    # input:    p        parameters read from stala file (see stalainfo())
    #                     (p.z_start, p.z_step, p.n1, p.xr_linlog,  p.xr_uselist,  p.xr_list)
    # output:   xr0      xramp0 parameters (xr0.flag, xr0.n, xr0.start, xr0.step, xr0.nl, xr0.l)
    #                                        xr0.flag: 0=lin, 1=log, 2=list, 3=loglist
    # -----------------------------------------
    def xramp0_init(self, p):  # -> xr0
        rname = "xramp0_init";
        xr0 = {'n': p['n1']}   # xr0.n = p.n1;
        if(p['xr_uselist'] != 0):
            if(p['xr_linlog'] != 0):

                xr0['flag'] = 3       # loglist
                z_end = p['z_step']   # (ATTN: z_end is stored as z_step)
                flag_incr, xsign, i_0, n10exp_0, ntot = xramp0_indeces_list_log(p['xr_list'], p['z_start'], z_end)
                n = len(p['xr_list'])
                xr0['nl'] = n
                if flag_incr:
                     xr0['step'] = np.log(10.0)    # = logd
                     ii = i0 + np.arange(n)
                else:
                     xr0['step'] = np.log(0.1)
                     ii = i0 + n - np.arange(n)
                xr0['list'] = xsign * p['xr_list'][ii % n] * 10.0**(n10exp_0 + np.floor(ii / n) )

            else:

                xr0['flag'] = 2       # list
                assert p['n1'] == len(p['xr_list']), f"{rname}: inconsistent input! p.n1 = {p['n1']} differs from # of elements in p.xr_list (= {len(p['xr_list'])})"
                xr0['l'] = p['xr_list']

        else:
            if p['xr_linlog'] != 0:

                xr0['flag'] = 1       # log
                z_end = p['z_end']    # p.z_step;    // (ATTN: z_end is stored as z_step)
                xr0['start'] = p['z_start']
                if (p['n1'] <= 1) or (p['z_start'] == 0.0) or (z_end / p['z_start'] <= 0):
                    xr0['n'] = min(p['n1'], 1)
                else:
                    xr0['step'] = np.log(z_end / p['z_start']) / (p['n1'] - 1)

            else:

                xr0['flag']  = 0      # lin
                xr0['start'] = p['z_start']
                xr0['step']  = p['z_step']

        return xr0

# --- test the code ---
# execute with python rdstala_class.py
if __name__ == '__main__':
    #from meas.rdstala_class import rdstala_class 
    #-------
    # memo:
    #  ff.x        x-values
    #  ff.y        all y-values, select specific y by  y = ff.y[ ff.scol(idev, iz, ival) ]
    #  ff.z        z-values  (can be ignored for simple measurements)
    #  ff.p[]      dictionary of extracted parameters from file comments
    #  ff.cmt      comment lines of file
    #  ff.filename file used
    #  ff.npar     integers of 3rd line of file
    #
    #  ff.p['comment']   comment entered for measurement
    #  ff.p['sample']    sample name
    #  ff.p['operator']  operator
    #  ff.p['date']      date of measurement
    #  ff.p['T']         temperature during measurement
    #  ff.p['RH']        humidity during measurement
    #  ff.p['id_meas']   type of measurement
    # further data are:
    # dict_keys(['comment', 'settle_time', 'nplc', 'intg_time', 'period', 'z_start', 'z_step', 'delay0', 'delay1', 'njw', 'n1', 'rev1', 'nsample', 'ramp_catchup', 'full_settletime', 'xr_linlog', 'xr_uselist', 'xr_list', 'sample', 'operator', 'date', 'time_since_start', 'id', 'T', 'RH', 'swb_time', 'swb_type', 's_idx', 's_iref', 's_slot', 's_mask', 's_dev', 's_sample', 's', 'filename', 'col_info', 'id_meas', 'remote_sensing', 'version', 'ver_no', 'ver_subno', 'ver_txt', 't_start', 't_end', 't_ref_date', 't_ref', 's_t_start', 'meas_pdev', 'n_TRHX', 's_TRHX1', 'lbl_TRHX1', 's_TRHX2', 'lbl_TRHX2'])
    
    # in short
    fname = 'Z:/data/IV/2023/02/20/ACO003_iv.dat'
    ff = rdstala_class(fname)
    print(f" {ff.p['filename']}")
    print(f" # of measurement values (per x value) : {ff.p['njw']:3d} ")
    print(f" # of x repeats (z1..z2) :               {ff.p['n1']:3d}   -> z     = {ff.z}") # =len(st.z)
    print(f" # of devices/samples :                  {ff.p['nsample']:3d}   -> s_dev = {ff.p['s_dev']}")
    print()
    # extract specific measurement from:
    idev, iz, ival = min(2, ff.p['nsample']-1), 0, 0
    print(f' retrieve x,    y for idev={idev}, iz={iz}, ival={ival} :')
    x, y = ff.x, ff.y[ ff.scol(idev, iz, ival) ] 
    print(x)
    print()
    print(y)
    print()
    print(ff.p['comment'])# comment entered for measurement
    print(ff.p['sample'])#    sample name
    print(ff.p['operator'])#  operator
    print(ff.p['date'])#      date of measurement
    print(ff.p['T'])#         temperature during measurement
    print(ff.p['RH'])#        humidity during measurement
    print(ff.p['id_meas'])#        humidity during measurement
    
