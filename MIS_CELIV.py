# -*- coding: utf-8 -*-
# MIS_CELIV.py
# do CELIV measurements
# v0.01 02.11.2022 initial version  (based on scilab MIS_CELIV_FINAL working version_20160315_vw.sce )
# v0.02 19.04.2022 class-based instr version

import numpy as np
import time
import pyvisa                 # https://pypi.org/project/PyVISA/
import os
os.chdir("/Users/celiv/py")
from instr.fg_class import fg_class
from instr.tds2022b import t20_x_intv, t20_y_intv
#from instr.cs328a import *
#from instr.spexctrl import spexctrl_class
from meas.savefile import svspec
from meas.celiv import celiv_open_instr, celiv_init_FGs, celiv_init_osca, celiv_init_osca2, celiv_send_WF, celiv_osca2_aquire_WF, ny_calc_WF #*

if __name__ == "__main__":
    use_OSC1 = False#True #False False=Tektronix TDS2022B, True=CS328A Cleverscope
    rsc = pyvisa.ResourceManager() if 'rsc' not in globals()  else rsc
    viFG, viOSC, viAG, sxc = celiv_open_instr(rsc, use_SPEXCTRL=True, use_TDS2022B=not use_OSC1)
    FG = fg_class(viFG, fg_typ='a33220') # fg_typ='k3390')
    AG = fg_class(viAG, fg_typ='a33220')
    if use_OSC1:   # rename handle to avoid confusion (OSC1 uses own driver not VISA)
        OSC = viOSC
        del viOSC
    print('instruments opened.')
    
    celiv_init_FGs(FG, AG, 0)
    FG.setTerm50Ohm(False)
    if use_OSC1:
        celiv_init_osca(OSC, 0)
    else:
        celiv_init_osca2(viOSC)
    
    # -------------------------------------------
    # OTRACE parameter
    i= 1
    fname = r'C:\buffer\Nivedita\MIS_CELIV\20160316\transient time\NYG237_D1_m2V_10V_tp_600us_th_5ms.dat'
    fname = r'C:\buffer\NYG237_D1_m2V_10V_tp_600us_th_5ms.dat'
    fname = r'C:\buffer\aaa_VW_test.dat'
    c = {}
    c['cmt']      = 'ITO/420 nm PMMA/550 nm P3HT:PCBM/85 nm Ag, sourceV with 100pF '
    c['sample']   = 'test - NYG237'
    c['device']   = 'D1'
    c['user']     ='vw'
    c['LEDcolor'] ='no LED';
    Rload         = 1e3   # Ohm
    A             = [0.126, 0.0458, 0.094, 0.126, 0.094, 0.0458, 0.126]
    k             = 0    #1
    Aarea         = A[k] #A (:,k); 
    tx            = 0
    tLED          = 1e-6
    VLED          = 2
    nOSCrep       = 8 #16   # 1 4 16 64 128
    nPCrep        = 2 #32
    ch2w1         = -0.1
    ch2w2         = 0.1
    
    ws            = 2000
    
    V0e           = 0.0 # 4.98
    Vh            = 5
    t0            = 0.0e-3
    
    tp            = 500e-6  # Ramping up time [s]
    th            = 1000e-6 # time duration for which constant Vh is applied [s]
    tn            = 600e-6  # time taken to go down from Vh to V0e [s]
    
    te            = 0e-6
    #n_pulses = 1
    
    t_min_charging = 20e-3 # [s]
    
    # -------------------------------------------
    cmt = [ c['cmt'] ]
    cmt.append( '; sample: '+c['sample'] )
    cmt.append( '; device: '+c['device'] )
    cmt.append( '; user:   '+c['user'] )
    cmt.append( '; file:   '+fname )
    cmt.append( '; '+'LEDcolor   '+c['LEDcolor'] )
    cmt.append( '; '+'V0e (V):  '+f"{V0e:f}"+'   Vh(V):   '+f"{Vh:f}"+'   VLED(V):   '+f"{VLED:f}" )
    cmt.append( '; '+'t0 (s):   '+f"{t0:f}"+'   tp(s):   '+f"{tp:f}"+'   th(s):   '+f"{th:f}"+'   tn (s):   '+f"{tn:f}"+'   td(s):   '+f"{0.0:f}"+'   te(s):   '+f"{te:f}"+'   n_pulses:   '+f"{1:d}" )
    cmt.append( '; '+'tx (s):   '+f"{tx:f}"+'   tLED(s):   '+f"{tLED:f}" )
    cmt.append( '; Rload (Ohm):'+f"{Rload:f}" )
    cmt.append( '; Aarea (cm2):'+f"{Aarea:f}" )
    cmt.append( '; nOSCrep:   '+f"{nOSCrep:d}" )
    cmt.append( '; nPCrep:   '+f"{nPCrep:d}" )
    cmt.append( '; t_min_charging(s):   '+f"{t_min_charging:e}" )
    # initialize instruments
    celiv_init_FGs(FG, AG,1)
    if use_OSC1:
        celiv_init_osca(OSC,1)
    else:
        celiv_init_osca2(viOSC)
    sxc.setZ(0) # 0=through, 1=through + 1k to GND, 2=no connection, 3= no connect. with osca-side 1k to GND
        #global xxx_abort; xxx_abort = %F;
    # --------------------- 
    # calculate waveform form the Lightpulse (agilent)
    a,dtLED,fLED, nt0L, ntpL, nthL, ntnL, ntdL, n_L = AG.calc_CELIV_WF(tx, 0e-6, tLED, 0, 0, 4e-6, 1) #a33220_calc_CELIV_WF(tx, 0e-6, tLED, 0, 0, 4e-6, 1)
    celiv_send_WF(AG, a)  # was: dac=round(8191*a); a33220_sendWF0(viAG, dac);
    AG.setFreq(fLED) #*size(a,'*')/size(dac,'*'));
    tLEDdac = dtLED * len(a)  # total time of LED waveform
    AG.setV(0, VLED)
    
    ## -------------create otrace waveform: vectr a
    ##a,dt,f, nt0, ntp, nth, ntn, ntd, n_ = k3390_calc_CELIV_WF(t0, tp, th, tn, td, te, n_pulses,VR,dV)
    #a,dt,f, nt0, ntp, nth, ntn, ntd, n_, Tmin = celiv_calc_OTRACE_WF(t0, tp, th, tn, td, te, n_pulses)
    
    ##move offset
    ##a(nt0:$)= a(nt0:$)+a(nt0-1);
    #a($) =-1; a($-1)=1;
    #a=-a
    
    #a,dt,f, nt0, ntp, nth, ntn, ntd, n_,Tmin,Vmax = celiv_calc_ecd_WF(t0, tp, th, tn, td, tn2, tl, tp2, td2, te, n_pulses, dVp, dVn, dVp2, dVn2)
    #old&wrong:       a,dt,f, nt0, ntp, nth, ntn, ntd, n_,Tmin,Vmax,Vmin = ecd_calc_WF(t0, tp, th, tn, td, tn2, tl, tp2, td2, te, n_pulses, V0,dVp, dVn, dVp2, dVn2)
    #a,dt,f, nt0, ntp, nth, ntn, ntd,ntn2,ntl,ntp2,ntd2, n_,Tmin,Vmax,Vmin = ecd_calc_WF(t0, tp, th, tn, td, tn2, tl, tp2, td2, te, n_pulses, V0,dVp, dVn, dVp2, dVn2)
    a,dt,f, nt0, ntp, nth, ntn, nte, n_, Tmin, Vmax, Vmin = ny_calc_WF(t0, tp, th, tn, te, V0e, Vh)
    cmt.append( '; '+f"FG: dt={dt:e}, dtLED={dtLED:e}" )
    import matplotlib.pyplot as plt
    #plt.plot(dt*np.arange(len(a)), a)
    if 'fig' in globals(): plt.close(fig=fig)
    fig, ax = plt.subplots(1,1)

    # ------------------------Sending Waveform and measure-------------------------------------
    celiv_send_WF(FG, a)  # was: dac=round(8191*a); k3390_sendWF0(viFG, dac);
    FG.setFreq(f)  #*size(a,'*')/size(dac,'*'));
    tFGdac = dt * len(a)  # total time of waveform
    #k3390_setV(viFG, V0, 2*abs(dV)) #+abs(VR)
    #k3390_setV(viFG, V0, Vmax) #2*abs(dV)
    FG.setV((Vmax+Vmin)/2, abs(Vmax-Vmin))
    AG.output(True)
    FG.output(True)
    ##tw=[0*dt*nt0+t0(ii), 0*dt*n_+t0(ii)+tp(ii)]
    ##cs32_setT(viOSC, tw(1), tw(2), 1.1) #tw=[20e-3, 20.1e-3]
    tw = [0*dt*nt0, 0*dt*n_+ws*1e-6]
    if use_OSC1:
        cs32_setT(OSC, tw[0], tw[1], 1.1)  # cs32_setT(CAU, StartTime, StopTime) // disp(tend)
    else:
        t20_x_intv(viOSC, tw[0], tw[1], f_enlarge=1.1)
    
    ddddTime=0.5 * (tw[1] - tw[0]) * (1.1-1)
    #if use_OSC1:  --> check T_ReplaySpec
    #    cs32_requestTime_set(OSC, tw(1)-ddddTime, tw(2)+ddddTime)  # bugfix if long times 8.Jun.2015 VW
    
    tend = 0.5*( (tw[0]+tw[1])+1.1*(tw[1]-tw[0]) )
    if use_OSC1:
        cs32_setAMinMax(OSC, Vmin, Vmax, 2)
        cs32_setBMinMax(OSC, ch2w1, ch2w2)
    else:
        t20_y_intv(viOSC, '1', Vmin, Vmax, f_enlarge=2)
        t20_y_intv(viOSC, '2', ch2w1, ch2w2, f_enlarge=1)
    
    cmt.append( f"; osc: tw={tw[0]:e} {tw[1]:e}" )
    
    time.sleep(0.1) #Delay(0.1); //100ms
    t_delay_charging = dt*(nt0+ntp+nth+ntn) + t_min_charging
    t_delay = np.asarray([tFGdac, tend, tLEDdac, t_delay_charging]).max() + 0.001  # delay time between pulses
    #scf(1); clf;
    for itt in range(nPCrep):
        if use_OSC1:
            t, ch1, ch2 = celiv_osca_aquire_WF(OSC, FG, nOSCrep, t_delay, Tmin)
        else:
            t, ch1, ch2 = celiv_osca2_aquire_WF(viOSC, FG, nOSCrep, t_delay)
        print(f'# itt={itt+1}/{nPCrep}')
        if itt == 0:
            ch1s, ch2s, ts = ch1, ch2, t
            #ax.plot(t*1e6, ch1)
            #ax.plot(t*1e6, ch2)
            #plt.show()
        else:
            if len(ch1s)!=len(ch1):
                itt -= 1
                print(itt)
            else:
                ch1s = ch1s + ch1
                ch2s = ch2s + ch2

    # -----------compute offset and subtract it---------
    if True and V0e==0:
        V1off = 0
        V2off = 0
        ch1 = ch1s / nPCrep
        ch2 = ch2s / nPCrep
    #    scf(2); plot2d(t*1e6,ch2); xlabel("t (us)"); ylabel("ch2 (V)"); xgrid(4);
        V1off = ch1[:20].mean()
        V2off = ch2[:20].mean()
        print( f"new V1off={V1off:f}, V2off={V2off:f}" )
    ch1 = ch1s / nPCrep - V1off #+ 0.00055
    ch2 = ch2s / nPCrep - V2off #+ 0.0043
    ch20 = ch2s / nPCrep #+ 0.0043
    
    cmt.append( f"; V1off={V1off:f}, V2off={V2off:f}" )
    
    time.sleep(200e-3)
    #clf; plot2d(t*1e6,[ch1;ch2]'); addmenu(1, "Abort"); Abort_1 = ['global xxx_abort; xxx_abort = %T;']; xlabel("t (us)"); ylabel("ch1,ch2 (V)"); xgrid(4); legend("ch1", "ch2");
    #scf(2); plot2d(t*1e6,ch2); xlabel("t (us)"); ylabel("ch2 (V)"); xgrid(4);
    #fig, ax = plt.subplots(1,1)
    ax.plot(t*1e6, ch1, label='ch1 (V)')
    ax.plot(t*1e6, ch2/Rload*1e3, label='ch2/Rload*1e3 (mA)')
    ax.grid()
    ax.legend()
    ax.set_xlabel("t (us)") #{pre['XUNIT']})")
    ax.set_ylabel("j (mA), V (V)") 
    
    # ----------saving data------------------
    svspec(fname, t, np.asarray([ch1, ch2, ch20]), cmt, '%e')
    print(f"saved file {fname} .")
        
    # -------------------------------------------
    FG.vi.close()
    if use_OSC1:
        OSC.SendCleverscopeCommand(T_Command.T_Command_Close)
        OSC.SendCleverscopeCommand(T_Command.T_Command_Finish)
    else:
        viOSC.close()
    AG.vi.close()
    sxc.close()
    print("Instruments closed.")
