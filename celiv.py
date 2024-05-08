# celiv.py
# written by Veit Wagner
#  basic routines for CELIV measurements
# usage:
#  from meas.celiv import *
# v0.01 01.11.2022 initial version (based on scilab meas/celiv_ah_ny_vw.sci 29.01.2014, last change 15.03.2016 added ny_calc_WF(), 24.10.2022 VW )
# v0.02 19.04.2023 with class based instr access

#// needs instr/scilabvisa.sci
#// memo: [rsc, status] = viOpenDefaultRM();
import pyvisa
import time   # time.sleep(t_sec)
import os
import ctypes
os.chdir('/users/celiv/py')
if True:
    from instr.cleverscope.CleverscopeInterface import Cleverscope
    from instr.cleverscope.T_AcquireSpec import T_AcquireSpec, T_AcquireAction, T_SigGenWaveform, T_LinkPort, T_TrigChannel, T_TrigSlope, T_TriggerFilter, T_AcquireMode
    from instr.cleverscope.T_ChannelSpec import T_ChannelSpec, T_Probe, T_GlobalFilter, T_PreFilter20MHz, T_MA_Filter, T_ExpFilter, T_FilterOption, T_Coupling
    from instr.cleverscope.T_InterfaceSpec import T_InterfaceSpec, T_Interface
    from instr.cleverscope.T_ReplaySpec import T_ReplaySpec
    from instr.cleverscope.T_T0dt import T_T0dt
    from instr.cleverscope.CleverscopeClasses import T_CAUStatus, T_Command, T_FunctionCommand, T_LinkMasterSlave, T_TriggeringUnit
from instr.tds2022b import t20_init, t20_getData
from instr.cs328a import cs32_open, cs32_setTrigger, cs32_setAcqModus, cs32_setA, cs32_setB
from instr.spexctrl import spexctrl_class
from instr.k3390_k3390 import *
from instr.a33220_a33220 import *

# -------------------------------------
def celiv_open_instr(rsc, use_SPEXCTRL=False, use_TDS2022B=False):  # ret:  viFG, CAU, viAG
    # "GPIB::16::INSTR", "USB::0x05e6::0x3390::KEI0007::INSTR", "TCPIP::10.50.252.21::INSTR"
    # Keithley Functionegenerator KE3390
    InstrDescr = "usb0::0x05e6::0x3390::1415620::INSTR"
    #InstrDescr = "USB::0x05e6::0x3390::KEI0007::INSTR"
    InstrDescr =  "USB0::0x0957::0x0407::MY44003895::0::INSTR"
    viFG =  rsc.open_resource(InstrDescr)

    # Agilent Functionegenerator Ag33220A
    InstrDescr = "TCPIP::10.50.252.21::INSTR"
    InstrDescr =  "USB0::0x0957::0x0407::MY44002154::0::INSTR"
    viAG =  rsc.open_resource(InstrDescr)
    
    if use_TDS2022B:
        # Tektronix TDS 2022B scope
        InstrDescr = "USB0::0x0699::0x0369::C101634::INSTR"
        viOSC =  rsc.open_resource(InstrDescr)
    else:
        # Cleverscope Oscilloscope CS328A
        """
        CAU = 0  # unit 0..31
        #[CAU_stat, err_stat] = cs32_openFindFirst(CAU)
        ###########  Set triggering Parameters
        TriggeringUnit = T_TriggeringUnit.T_TriggeringUnit_UnitA # Trigger on Unit A (used when LinkedDualScope is True)
        UnitATriggerChannel = T_TrigChannel.T_TrigChan_ChanA	 # Unit A will Trigger on Channel A (if LinkedDualScope then the Triggering Unit will impact on this setting)
        UnitBTriggerChannel = T_TrigChannel.T_TrigChan_ChanA     # Unit B will Trigger on Channel A (if LinkedDualScope then the Triggering Unit will impact on this setting)
        AcquisitionTypeToDo = T_AcquireAction.T_AcquireAction_Automatic #Choose Single, Automatic, or Triggered
        # Set some Parameters
        StartTime = -0.005
        StopTime = 0.005
        ProbeMinVoltage = -3
        ProbeMaxVoltage = 3
        Numsamples = 10000
        MaximumSamples = 10000
        FrameNum = 0
        CscopeUnit = Cleverscope(CAU, InterfaceSource = T_Interface.T_Interface_EthernetOrUSBFirstFound, IPAddr = '10.1.5.45', TCP_Port = 53270, SerialNumber='IT10081',
                          StartTime = StartTime, StopTime =StopTime,  
                          FrameNum = FrameNum, NumSamples = Numsamples, MaximumSamples = MaximumSamples,
                          TriggerSource = UnitATriggerChannel, TriggerLevel = .5, 
                          LinkPort = T_LinkPort.T_LinkPort_Debug,
                          ProbeMinVoltage = ProbeMinVoltage, ProbeMaxVoltage = ProbeMaxVoltage, 
                          ProbeAGain = T_Probe.T_Probe_Vsat_x2,
                          ProbeBGain = T_Probe.T_Probe_x10,
                          ProbeCGain = T_Probe.T_Probe_x1,
                          ProbeDGain = T_Probe.T_Probe_x1,
                          ProbeCoupling = T_Coupling.T_Coupling_DC)
        viOSC = CscopeUnit
        """
        viOSC = cs32_open()
        
    if use_SPEXCTRL:
        # Spex-Ctrl
        ComPort = 3
        #viSX = sxc_open_init(rsc, ComPort)
        sxc = spexctrl_class(rsc, ComPort)
        return  viFG, viOSC, viAG, sxc
    
    return  viFG, viOSC, viAG   

"""
function [viFG, CAU, status] = celiv_open_instr2(rsc) // used for electrochemical deposition ecd.sce for torsten (added AH 23.04.2015)
    // "GPIB::16::INSTR", "USB::0x05e6::0x3390::KEI0007::INSTR", "TCPIP::10.50.252.21::INSTR"
    // Keithley Functionegenerator KE3390
    InstrDescr = "usb0::0x05e6::0x3390::1415620::INSTR";
    //InstrDescr = "USB::0x05e6::0x3390::KEI0007::INSTR";
    [viFG, status] = viOpen(rsc, InstrDescr); if(status<0) then disp('viOpen('''+InstrDescr+'''): '+viStatusDesc(rsc, status)); end
 
    // Cleverscope Oscilloscope CS328A
    CAU = 0;  // unit 0..31
    [CAU_stat, err_stat] = cs32_openFindFirst(CAU);

endfunction
"""

# -------------------------------------
# lvl: 0=complete init, 1=assumed some init was already done
def celiv_init_FGs(FG, AG, lvl):  # ret:  -
    if (f'{FG.__class__}')[-11:-2] != ".fg_class":
        viFG, viAG = FG, AG
        return celiv_init_FGs_via_vi(viFG, viAG, lvl) # do old fassion with viFG, viAG
    # Agilent Functionegenerator Ag33220A
    if lvl==0:
        AG.init()
        AG.vi.write("BURSt:GATE:POLarity NORMal")    # BURSt:GATE:POLarity { NORMal|INVerted }
        AG.vi.write("TRIGger:SOURce BUS")	       # TRIGger:SOURce {IMMediate|EXTernal|BUS} (avoids LED on by ext. trigger while KE3390 inits)
        AG.vi.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
        AG.vi.write("OUTPut:TRIGger OFF")     # OUTPut:TRIGger {OFF|ON}
        AG.vi.write("VOLTage:UNIT VPP")	             # VOLTage:UNIT {VPP|VRMS|DBM} (VPP is dflt (?))
        AG.vi.write("FORM:BORD SWAP")    # required by scilab_k3390_sendWF0.sci; ensure was sent before !!!  // FORMat:BORDer {NORMal|SWAPped} 
        AG.vi.write("DATA:DAC VOLATILE,0,255,0") # has to be set before a33220_setFunction_User(viAG, 'VOLATILE');
        AG.setTerm50Ohm(False)
        AG.setV(0.0, 0.02) # 10 mVSS bis 10 VSS an 50 Ohm; 20 mVSS bis 20 VSS im Leerlauf
    
    # Keithley Functionegenerator KE3390
    if lvl==0:
        FG.init()
        FG.vi.write("BURSt:GATE:POLarity NORMal")	# BURSt:GATE:POLarity { NORMal|INVerted }
        FG.vi.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
        FG.vi.write("OUTPut:TRIGger:SLOPe POSitive")	# OUTPut:TRIGger:SLOPe {POSitive|NEGative}
        FG.vi.write("VOLTage:UNIT VPP")	             # VOLTage:UNIT {VPP|VRMS|DBM} (VPP is dflt)
        FG.vi.write("FORM:BORD SWAP")    # required by scilab_k3390_sendWF0.sci; ensure was sent before !!!  // FORMat:BORDer {NORMal|SWAPped} 
        FG.vi.write("DATA:DAC VOLATILE,0,255,0") # be sure its exists (perhaps not needed for KE)
        FG.setTerm50Ohm(True)
        FG.setV(0.0, 0.01) # 10mVpp to 10Vpp in 50Ω; 20mVpp to 20Vpp in Hi-Z
    FG.vi.write("BURSt:MODE TRIGgered")	# BURSt:MODE {TRIGgered|GATed}
    # viFG.write("BURSt:GATE:POLarity NORMal")	# BURSt:GATE:POLarity { NORMal|INVerted }
    FG.vi.write("BURSt:NCYCles 1")		# BURSt:NCYCles {<#cycles>|INF..
    FG.vi.write("TRIGger:SOURce BUS")	# TRIGger:SOURce {IMMediate|EXTernal|BUS}
    FG.vi.write("BURSt:STATe ON")
    # viFG.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
    # viFG.write("OUTPut:TRIGger:SLOPe POSitive")	# OUTPut:TRIGger:SLOPe {POSitive|NEGative}
    FG.vi.write("OUTPut:TRIGger ON")	# OUTPut:TRIGger {OFF|ON}
    # viAG.write("DATA:DAC VOLATILE,0,255,0") # be sure its exists (perhaps not needed for KE)
    FG.setFunction('USER')
    FG.setFunction_User('VOLATILE')
    # k3390_setTerm50Ohm(viFG, True)
    
    # Agilent Functionegenerator Ag33220A
    AG.vi.write("BURSt:MODE TRIGgered")	# BURSt:MODE {TRIGgered|GATed}
    # viAG.write("BURSt:GATE:POLarity NORMal")	# BURSt:GATE:POLarity { NORMal|INVerted }
    AG.vi.write("BURSt:NCYCles 1")		# BURSt:NCYCles {<#cycles>|INF..
    AG.vi.write("TRIGger:SOURce EXT")	# TRIGger:SOURce {IMMediate|EXTernal|BUS}
    AG.vi.write("BURSt:STATe ON")
    # viAG.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
    # viAG.write("OUTPut:TRIGger OFF")	# OUTPut:TRIGger {OFF|ON}
    # viAG.write("DATA:DAC VOLATILE,0,255,0") # has to be set before a33220_setFunction_User(viAG, 'VOLATILE');
    AG.setFunction('USER')
    AG.setFunction_User('VOLATILE')
    # a33220_setTerm50Ohm(viAG, False)

# -------------------------------------
# lvl: 0=complete init, 1=assumed some init was already done
def celiv_init_FGs_via_vi(viFG, viAG, lvl):  # ret:  -
    # Agilent Functionegenerator Ag33220A
    if lvl==0:
        a33220_init(viAG)
        viAG.write("BURSt:GATE:POLarity NORMal")    # BURSt:GATE:POLarity { NORMal|INVerted }
        viAG.write("TRIGger:SOURce BUS")	       # TRIGger:SOURce {IMMediate|EXTernal|BUS} (avoids LED on by ext. trigger while KE3390 inits)
        viAG.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
        viAG.write("OUTPut:TRIGger OFF")     # OUTPut:TRIGger {OFF|ON}
        viAG.write("VOLTage:UNIT VPP")	             # VOLTage:UNIT {VPP|VRMS|DBM} (VPP is dflt (?))
        viAG.write("FORM:BORD SWAP")    # required by scilab_k3390_sendWF0.sci; ensure was sent before !!!  // FORMat:BORDer {NORMal|SWAPped} 
        viAG.write("DATA:DAC VOLATILE,0,255,0") # has to be set before a33220_setFunction_User(viAG, 'VOLATILE');
        a33220_setTerm50Ohm(viAG, False)
        a33220_setV(viAG, 0.0, 0.02) # 10 mVSS bis 10 VSS an 50 Ohm; 20 mVSS bis 20 VSS im Leerlauf
    
    # Keithley Functionegenerator KE3390
    if lvl==0:
        k3390_init(viFG);
        viFG.write("BURSt:GATE:POLarity NORMal")	# BURSt:GATE:POLarity { NORMal|INVerted }
        viFG.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
        viFG.write("OUTPut:TRIGger:SLOPe POSitive")	# OUTPut:TRIGger:SLOPe {POSitive|NEGative}
        viFG.write("VOLTage:UNIT VPP")	             # VOLTage:UNIT {VPP|VRMS|DBM} (VPP is dflt)
        viFG.write("FORM:BORD SWAP")    # required by scilab_k3390_sendWF0.sci; ensure was sent before !!!  // FORMat:BORDer {NORMal|SWAPped} 
        viFG.write("DATA:DAC VOLATILE,0,255,0") # be sure its exists (perhaps not needed for KE)
        k3390_setTerm50Ohm(viFG, True)
        k3390_setV(viFG, 0.0, 0.01) # 10mVpp to 10Vpp in 50Ω; 20mVpp to 20Vpp in Hi-Z
    viFG.write("BURSt:MODE TRIGgered")	# BURSt:MODE {TRIGgered|GATed}
    # viFG.write("BURSt:GATE:POLarity NORMal")	# BURSt:GATE:POLarity { NORMal|INVerted }
    viFG.write("BURSt:NCYCles 1")		# BURSt:NCYCles {<#cycles>|INF..
    viFG.write("TRIGger:SOURce BUS")	# TRIGger:SOURce {IMMediate|EXTernal|BUS}
    viFG.write("BURSt:STATe ON")
    # viFG.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
    # viFG.write("OUTPut:TRIGger:SLOPe POSitive")	# OUTPut:TRIGger:SLOPe {POSitive|NEGative}
    viFG.write("OUTPut:TRIGger ON")	# OUTPut:TRIGger {OFF|ON}
    # viAG.write("DATA:DAC VOLATILE,0,255,0") # be sure its exists (perhaps not needed for KE)
    k3390_setFunction(viFG, 'USER')
    k3390_setFunction_User(viFG, 'VOLATILE')
    # k3390_setTerm50Ohm(viFG, True)
    
    # Agilent Functionegenerator Ag33220A
    viAG.write("BURSt:MODE TRIGgered")	# BURSt:MODE {TRIGgered|GATed}
    # viAG.write("BURSt:GATE:POLarity NORMal")	# BURSt:GATE:POLarity { NORMal|INVerted }
    viAG.write("BURSt:NCYCles 1")		# BURSt:NCYCles {<#cycles>|INF..
    viAG.write("TRIGger:SOURce EXT")	# TRIGger:SOURce {IMMediate|EXTernal|BUS}
    viAG.write("BURSt:STATe ON")
    # viAG.write("TRIGger:SLOPe POSitive")	# TRIGger:SLOPe {POSitive|NEGative}
    # viAG.write("OUTPut:TRIGger OFF")	# OUTPut:TRIGger {OFF|ON}
    # viAG.write("DATA:DAC VOLATILE,0,255,0") # has to be set before a33220_setFunction_User(viAG, 'VOLATILE');
    a33220_setFunction(viAG, 'USER')
    a33220_setFunction_User(viAG, 'VOLATILE')
    # a33220_setTerm50Ohm(viAG, False)

"""
def celiv_init_FGs2(viFG, lvl):  # ret:  -   #used for electrochemical deposition ecd.sce for torsten (added AH 23.04.2015)
    // Keithley Functionegenerator KE3390
    if(lvl==0) then
        status = k3390_init(viFG);
        viWrite(viFG, "BURSt:GATE:POLarity NORMal");	// BURSt:GATE:POLarity { NORMal|INVerted }
        viWrite(viFG, "TRIGger:SLOPe POSitive");	// TRIGger:SLOPe {POSitive|NEGative}
        viWrite(viFG, "OUTPut:TRIGger:SLOPe POSitive");	// OUTPut:TRIGger:SLOPe {POSitive|NEGative}
        viWrite(viFG, "VOLTage:UNIT VPP");	             // VOLTage:UNIT {VPP|VRMS|DBM} (VPP is dflt)
        viWrite(viFG, "FORM:BORD SWAP");    // required by scilab_k3390_sendWF0.sci; ensure was sent before !!!  // FORMat:BORDer {NORMal|SWAPped} 
        viWrite(viFG, "DATA:DAC VOLATILE,0,255,0"); // be sure its exists (perhaps not needed for KE)
        k3390_setTerm50Ohm(viFG, %T);
        k3390_setV(viFG, 0.0, 0.02); // 10mVpp to 10Vpp in 50Ω; 20mVpp to 20Vpp in Hi-Z
    end
    viWrite(viFG, "BURSt:MODE TRIGgered");	// BURSt:MODE {TRIGgered|GATed}
    // viWrite(viFG, "BURSt:GATE:POLarity NORMal");	// BURSt:GATE:POLarity { NORMal|INVerted }
    viWrite(viFG, "BURSt:NCYCles 1");		// BURSt:NCYCles {<#cycles>|INF..
    viWrite(viFG, "TRIGger:SOURce BUS");	// TRIGger:SOURce {IMMediate|EXTernal|BUS}
    viWrite(viFG, "BURSt:STATe ON");
    // viWrite(viFG, "TRIGger:SLOPe POSitive");	// TRIGger:SLOPe {POSitive|NEGative}
    // viWrite(viFG, "OUTPut:TRIGger:SLOPe POSitive");	// OUTPut:TRIGger:SLOPe {POSitive|NEGative}
    viWrite(viFG, "OUTPut:TRIGger ON");	// OUTPut:TRIGger {OFF|ON}
    // viWrite(viAG, "DATA:DAC VOLATILE,0,255,0"); // be sure its exists (perhaps not needed for KE)
    k3390_setFunction(viFG, 'USER');
    k3390_setFunction_User(viFG, 'VOLATILE');
    // k3390_setTerm50Ohm(viFG, %T);
endfunction
"""

# -------------------------------------
# lvl: 0=complete init, 1=assumed some init was already done
#def celiv_init_osca(CAU, lvl):  # ret:  -
def celiv_init_osca(OSC, lvl):  # ret:  -
    
    ## [CAU_status, err_status, err_code] = cs32_setTrigger(CAU, TAmplitude, TrigSlope, TriggerSource, TriggerFilter);
    ##   TAmplitude:     Level at which to trigger for Channel A or Channel B or external or digital input (depending on Triggersource s.b.)
    ##   TrigSlope:      Sets the trigger slope. 0 = rising, 1 = falling
    ##   TriggerSource:  Sets trigger source. 0 = A chan, 1 = B chan, 2 = Ext Trigger, 3 = Dig Input, 4 = Link Portacquire.AMaxScale = 2;
    ##   TriggerFilter:  Sets filter on trigger. 0 = None, 1 = Low Pass (<250kHz), 2 = Hi Pass (>500 kHz), 3 = noise. (Test signal 20% FSD sine wave). Normal hysteresis is 2.5%. Noise hysteresis is 7.5%
    if lvl == 0:
        ## cs32_setTrigger(CAU, 1.6, 0, 2, 0);
        cs32_setTrigger(OSC, 1.6, T_TrigSlope.T_TrigSlope_Rising, T_TrigChannel.T_TrigChan_ExtTrigger, T_TriggerFilter.T_TriggerFilter_None)
        #OSC.AcquireSpec.TriggerAmplitude = ctypes.c_double(1.6)                 # see class T_AcquireSpec
        #OSC.AcquireSpec.TrigSlope        = T_TrigSlope.T_TrigSlope_Rising       # Rising(0), Falling(1) ; see class T_TrigSlope in T_AcquireSpec.py
        #OSC.AcquireSpec.TriggerSource    = T_TrigChannel.T_TrigChan_ExtTrigger  # ChanA(0), ChanB(1), ExtTrigger(2), DigTrig(3), LinkInput(4), .. Dig2(15) ; see T_AcquireSpec.py
        #OSC.AcquireSpec.TriggerFilter    = T_TriggerFilter.T_TriggerFilter_None # None(0), LowPass(<250kHz)(1), HiPass(>500 kHz)(2), Noise(3)_(Test signal 20% FSD sine wave). Normal hysteresis is 2.5%. Noise hysteresis is 7.5%        

    ## [CAU_status, err_status, err_code] = cs32_setAcqModus(CAU, AcquireMode, AcquisitionMode, WaveformAverages, NumSeqFrames)
    ##   AcquireMode      How to acquire: 0 = Single, 1= automatic, 2 = triggered, 3 = stop Make sure this is 3 (stop) when initializing the driver.
    ##   AcquisitionMode  Method of acquisition: 0 = sampled, 1= Peak captured, 2 = Filtered, 3= Repetitive, 4= Waveform avg, (for which make sure there are at least waveform avg +1 buffers).
    ##   WaveformAverages ets how many waveforms to average in acquisition unit if acquisition mode = waveform avg. Values are 1, 4, 16, 64 and 128
    ##   NumSeqFrames     acquire.NumSeqFrames; Sets the number of frames captured sequentially. If waveform avg method of capture set to 1. If capturing sequential frames,
    ##                    set to number of frames to capture.
    ## cs32_setAcqModus(CAU, 2, 4, 1, 1);
    cs32_setAcqModus(OSC, T_AcquireAction.T_AcquireAction_Triggered, T_AcquireMode.T_AcquireMode_WaveformAvg, WaveformAverages=1, NumSeqFrames=1)
    #OSC.AcquireSpec.AcquireMode      = T_AcquireAction.T_AcquireAction_Triggered   # Single(0), Automatic(1), Triggered(2) [], Stop(3), SingleStop(4), Replay(5), Chart(6) ] ; see class T_AcquireAction in T_AcquireSpec.py
    #OSC.AcquireSpec.AcquisitionMode  = T_AcquireMode.T_AcquireMode_WaveformAvg     # Sampled(0), PeakCaptured(1), Filtered(2), Repetitive(3), WaveformAvg(4)
    #OSC.AcquireSpec.WaveformAverages = ctypes.c_int32(1)                           # how many waveforms to average in acquisition unit if acquisition mode = waveform avg. Values are 1, 4, 16, 64 and 128 (<- from class T_AcquireSpec)
    #OSC.AcquireSpec.NumSeqFrames     = ctypes.c_int16(1)                           # number of frames captured sequentially. Read the 'Cscope Control Driver DLL description.pdf'.
    
    ## [CAU_status, err_status, err_code] = cs32_setA(CAU, Coupling, Probe, Bandwidth)
    ##   ACoupling        A Coupling, 0 = AC, 1= DC
    ##   AProbe           A Probe Multiplier 0 = x1, 1 = x10, 2 = x100, 3 = x1000, 4 = x20, 5 = x50, 6 = x200.
    ##   ABandwidth       Bit 0 - Global Filter enable, 0 = no filter, 1 = use filter   // |tttx|mppe|  (e=Global Filter enable)|
    ##										Bit 2:1 - Pre-filter frequency 0 = No filter, 1 = 20 MHz filter
    ##										Bit 3: - If true, use the moving average (MA) filter
    ##										Bit 4: - Reserved
    ##										Bits 7:5 - Filter time constant, in taps:
    ##										000 = no filter, 001 = 40ns, 010 = 80ns, 011 = 160ns
    ##										100 = 320ns, 101 = 640ns, 110 = 1280ns, tap111 = reserved MA
    ##										For the moving average only the channel A moving average value is used, and
    ##										it also used for Channel B
    if lvl >= 0:
        ## cs32_setA(CAU, 1, 0,  3+128+8);
        ## cs32_setB(CAU, 1, 0,  3+128+8);
        cs32_setA(OSC, T_Coupling.T_Coupling_DC, T_Probe.T_Probe_x1, T_GlobalFilter.T_GlobalFilter_On, T_PreFilter20MHz.T_PreFilter20MHz_On, T_MA_Filter.T_MA_Filter_On, T_ExpFilter.T_ExpFilter_Off, T_FilterOption=T_FilterOption.T_FilterOption__32xMA_16xExp)  # 320ns(4)
        cs32_setB(OSC, T_Coupling.T_Coupling_DC, T_Probe.T_Probe_x1, T_GlobalFilter.T_GlobalFilter_On, T_PreFilter20MHz.T_PreFilter20MHz_On, T_MA_Filter.T_MA_Filter_On, T_ExpFilter.T_ExpFilter_Off, T_FilterOption=T_FilterOption.T_FilterOption__32xMA_16xExp)  # 320ns(4)
        #OSC.ChannelSpecArray[0].Coupling       = T_Coupling.T_Coupling_DC             # AC(0), DC(1) ;  see class T_Coupling and class T_ChannelSpec in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[0].Probe          = T_Probe.T_Probe_x1                   # x1(0), x10(1), x100(2), x1K(3), x2(4), x20(5), x50(6), x200(7), Vsat_0_15(8), Vsat_1_50(9), Vsat_15_0(10), Vsat_x2(11) ; see class T_Probe in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[0].GlobalFilter   = T_GlobalFilter.T_GlobalFilter_On     # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[0].PreFilter20MHz = T_PreFilter20MHz.T_PreFilter20MHz_On # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[0].MA_Filter      = T_MA_Filter.T_MA_Filter_On           # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[0].Exp_Filter     = T_ExpFilter.T_ExpFilter_Off          # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[0].T_FilterOption = T_FilterOption.T_FilterOption__32xMA_16xExp # NoFilter(0), _4xMA_2xExp(1), _8xMA_4xExp(2), _16xMA_8xExp(3), _32xMA_16xExp(4), _64xMA_32xExp(5), _2048xMA_64xExp(6), _XXXxMA_2048xExp(7) ; see in  T_ChannelSpec.py
                                                                                             #               40ns            80ns            160ns            320ns             640ns             1280ns(?)
        #OSC.ChannelSpecArray[0].T_FilterOption = T_FilterOption.T_FilterOption__32xMA_16xExp # NoFilter(0), _4xMA_2xExp(1), _8xMA_4xExp(2), _16xMA_8xExp(3), _32xMA_16xExp(4), _64xMA_32xExp(5), _2048xMA_64xExp(6), _XXXxMA_2048xExp(7) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[1].Coupling       = T_Coupling.T_Coupling_DC # AC(0), DC(1) ;  see class T_Coupling and class T_ChannelSpec in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[1].Probe          = T_Probe.T_Probe_x1       # x1(0), x10(1), x100(2), x1K(3), x2(4), x20(5), x50(6), x200(7), Vsat_0_15(8), Vsat_1_50(9), Vsat_15_0(10), Vsat_x2(11) ; see class T_Probe in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[1].GlobalFilter   = T_GlobalFilter.T_GlobalFilter_On # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[1].PreFilter20MHz = T_PreFilter20MHz.T_PreFilter20MHz_On # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[1].MA_Filter      = T_MA_Filter.T_MA_Filter_On           # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[1].Exp_Filter     = T_ExpFilter.T_ExpFilter_Off          # Off(0), On(1) ; see in  T_ChannelSpec.py
        #OSC.ChannelSpecArray[1].T_FilterOption = T_FilterOption.T_FilterOption__32xMA_16xExp # NoFilter(0), _4xMA_2xExp(1), _8xMA_4xExp(2), _16xMA_8xExp(3), _32xMA_16xExp(4), _64xMA_32xExp(5), _2048xMA_64xExp(6), _XXXxMA_2048xExp(7) ; see in  T_ChannelSpec.py
        
    OSC.UpdateCleverscope()  # <- needed??
    
    """
    # set: TriggerAmplitude=1.6V; TriggerSlope=(0)rising; TriggerSource=(2)Ext.Trigger; TriggerFilter=(0)None 
    # set: AcquireMode=(2)triggered; AquisitionsMode=(4)Waveform avg; WaveformAverages=(1)# of waveforms to avg; NumSeqFrames=(1)
    # set: ChannelA: Coupling=(1)DC; Probe=(0)x1; Bandwidth=(3+128+8), UseFilter, 20MHzPre-filter, timeconst 320ns, MovingAvgFilter
    # set: ChannelB: Coupling=(1)DC; Probe=(0)x1; Bandwidth=(3+128+8), UseFilter, 20MHzPre-filter, timeconst 320ns, MovingAvgFilter
    ChanA = T_ChannelSpec()
    ChanA.Init(-10.0, 10.0, T_Probe.T_Probe_x1, T_Coupling.T_Coupling_DC) # ProbeMinVoltage, ProbeMaxVoltage, ProbeGain, ProbeCoupling
    ChanA.GlobalFilter   = T_GlobalFilter.T_GlobalFilter_On     # Use Filter on
    ChanA.PreFukter20MHz = T_PreFilter20MHz.T_PreFilter20MHz_On # 20 MHz filter on
    ChanA.MA_Filter      = T_MA_Filter.T_MA_Filter_On           # moving average filter on
    ChanA.FilterOption   = T_FilterOption.T_FilterOption__32xMA_16xExp # (4) 320ns moving average(?)
    """    
    


# -------------------------------------
def celiv_init_osca2(viOSC):  # ret:  -
    status = t20_init(viOSC)
#    viWrite(viOSC, "CH1:SCA 1.0");	// CH<x>:SCAle <NR3> p. 2-69  (1-2-5 value)
#    viWrite(viOSC, "CH1:POS 0.0");	// CH<x>:POSition <NR3> p. 2-67  (<NR3> in divisions, see table 2-28)
    viOSC.write("*esr?")			# check for any message and clear from queue
    viOSC.read()  # buffer = blanks(64); [xx, status, n] = viRead(viOSC, buffer);
    viOSC.write("allev?")
    viOSC.read()  # buffer = blanks(64); [xx, status, n] = viRead(viOSC, buffer);
    viOSC.write("trig:main:edge:source ext5") 	# CH<x> | EXT | EXT5 (EXT5 = voltage divided by 5)
    viOSC.write("trig:main:level 1.6")			# 1/5 of TTL-threshold = 1.6V (below 5V/2)
    viOSC.write("ACQ:MOD SAM")		# ACQuire:MODe { SAMple | PEAKdetect | AVErage } p. 2-46

    viOSC.write("ACQ:STATE 0")		# ACQuire:STATE { OFF | ON | RUN | STOP | <NR1> } p. 2-49; OFF | STOP | <NR1> = 0 stops acquisitions; ON | RUN | <NR1> != 0 starts acquisition
    viOSC.write("TRIG:MAI:MOD NORM")	# TRIGger:MAIn:MODe { AUTO | NORMal } p.2-229  (NORM=waits for valid trigger)
    viOSC.write("ACQ:STOPA SEQ")	# ACQuire:STOPAfter { RUNSTop | SEQuence} p. 2-50

# -------------------------------------
# suitable for KE3390 and A33220
def celiv_send_WF(FG, a):  # ret:  -
    viFG = FG if (f'{FG.__class__}')[-11:-2] != ".fg_class"  else FG.vi # allow old fassion with viFG as parameter
    dac = np.int16(np.round(8191*a))
    k3390_sendWF0(viFG, dac)   # (slower) ASCII transfer
    #err = k3390_sendWF0_bin(viFG, dac); // <- needs to have scilab_k3390_sendWF0.sci loaded and linked

# -------------------------------------
#function [t, ch1, ch2, status] = celiv_osca_aquire_WF(CAU, viFG, noscarep, trep_delay)
#    // [CAU_status, err_status, err_code] = cs32_setAcqModus(CAU, AcquireMode, AcquisitionMode, WaveformAverages, NumSeqFrames)
#    //   AcquireMode      How to acquire: 0 = Single, 1= automatic, 2 = triggered, 3 = stop Make sure this is 3 (stop) when initializing the driver.
#    //   AcquisitionMode  Method of acquisition: 0 = sampled, 1= Peak captured, 2 = Filtered, 3= Repetitive, 4= Waveform avg, (for which make sure there are at least waveform avg +1 buffers).
#    //   WaveformAverages ets how many waveforms to average in acquisition unit if acquisition mode = waveform avg. Values are 1, 4, 16, 64 and 128
#    //   NumSeqFrames     acquire.NumSeqFrames; Sets the number of frames captured sequentially. If waveform avg method of capture set to 1. If capturing sequential frames,
#    //                    set to number of frames to capture.
#    cs32_setAcqModus(CAU, 2, 4, noscarep, 1);
#    //
#    for(i=[1:noscarep])
#        k3390_trigger(viFG);
#        sleep(trep_delay*1e3);  // Delay(trep_delay)
#    end
#    
#    [ch1, ch2, DIG, t, CAU_stat, status] = cs32_getData(CAU); // , nData, ReplayStartTime, ReplayStopTime, FrameNumber, timeout);
#endfunction
# -------------------------------------
#def celiv_osca_aquire_WF(CAU, FG, noscarep, trep_delay, Tmin):  # ret:  t, ch1, ch2
def celiv_osca_aquire_WF(OSC, FG, noscarep, trep_delay, Tmin):  # ret:  t, ch1, ch2
    ## [CAU_status, err_status, err_code] = cs32_setAcqModus(CAU, AcquireMode, AcquisitionMode, WaveformAverages, NumSeqFrames)
    ##   AcquireMode      How to acquire: 0 = Single, 1= automatic, 2 = triggered, 3 = stop Make sure this is 3 (stop) when initializing the driver.
    ##   AcquisitionMode  Method of acquisition: 0 = sampled, 1= Peak captured, 2 = Filtered, 3= Repetitive, 4= Waveform avg, (for which make sure there are at least waveform avg +1 buffers).
    ##   WaveformAverages ets how many waveforms to average in acquisition unit if acquisition mode = waveform avg. Values are 1, 4, 16, 64 and 128
    ##   NumSeqFrames     acquire.NumSeqFrames; Sets the number of frames captured sequentially. If waveform avg method of capture set to 1. If capturing sequential frames,
    ##                    set to number of frames to capture.
    ## cs32_setAcqModus(CAU, 2, 4, noscarep, 1);
    assert OSC.IsConnected(), "Cleverscope CS328A is not connected !"
    if noscarep == 1:
        OSC.AcquireSpec.AcquisitionMode  = T_AcquireMode.T_AcquireMode_Sampled          # Sampled(0), PeakCaptured(1), Filtered(2), Repetitive(3), WaveformAvg(4)
    else:
        OSC.AcquireSpec.AcquisitionMode  = T_AcquireMode.T_AcquireMode_WaveformAvg      # Sampled(0), PeakCaptured(1), Filtered(2), Repetitive(3), WaveformAvg(4)
        OSC.AcquireSpec.WaveformAverages = ctypes.c_int32(noscarep)       # how many waveforms to average in acquisition unit if acquisition mode = waveform avg. Values are 1, 4, 16, 64 and 128 (<- from class T_AcquireSpec)
        
    AcqTypToDo = T_AcquireAction.T_AcquireAction_Triggered # OSC.AcquireSpec.AcquireAction # T_AcquireAction.T_AcquireAction_Triggered #Choose Single, Automatic, or Triggered
    OSC.BeginSampleCapture(AcqTypToDo)  # sends command 'Acquire'
    time.sleep(20e-3)  #sleep(10)
    
    for i in range(noscarep):
        FG.trigger()
        time.sleep(trep_delay)  #sleep(trep_delay*1e3);  // Delay(trep_delay)
        
    if not OSC.CheckForSampleCaptureComplete(): # send command 'WaitForSamples' -> 'GotSamples'
        FG.trigger()
        print("extra trigger and wait ..")
        time.sleep(max(200e-3, trep_delay))
        if not OSC.CheckForSampleCaptureComplete():
            print("no data !")
            return np.asarray([]), np.asarray([]), np.asarray([])
        
    t        = OSC.T0dt.t0 + np.arange(OSC.T0dt.n)*OSC.T0dt.dt  # abs. time of trigger OSC.T0dt.TTrig
    ch1, ch2 =  OSC.ChannelAData, OSC.ChannelBData
    return t, ch1, ch2
    """    
    Nmax = 60000
    #[err] = cs32_sampleBuf_realloc(CAU, Nmax, Nmax, Nmax);
    #cs32_acquire_x_ValueChan(CAU);
    #cs32_setAcqModus(CAU, 2, 0, noscarep, 1);
    time.sleep(20e-3)  #sleep(10)
    #[got_smpls, t0, dt, smpls_rtd, frms_rtd, CAU_stat, err_stat] = cs32_CscopeControlDrv(CAU, 3, Nmax, 0); # 'wait for samples'
    #if(got_smpls ~= 0) then disp('found unexpected samples ?!'); end
    
    #[got_smpls, t0, dt, smpls_rtd, frms_rtd, CAU_stat, err_stat] = cs32_CscopeControlDrv(CAU, 1, Nmax, 0); # 'acquire'
    #
    for i in range(noscarep):
        FG.trigger()
        time.sleep(trep_delay)  #sleep(trep_delay*1e3);  // Delay(trep_delay)
    FG.trigger()
    time.sleep(trep_delay)  #sleep(trep_delay*1e3);  // Delay(trep_delay)
    #??t_delay global?? time.sleep(t_delay*1e-3)  #Delay(t_delay);
    time.sleep(50e-3)  #sleep(50);
    for i in range(20):
        time.sleep(100e-3)  #sleep(100); //***********
        #[got_smpls, t0, dt, smpls_rtd, frms_rtd, CAU_stat, err_stat] = cs32_CscopeControlDrv(CAU, 3, Nmax, 0);
        time.sleep(100e-3)  #sleep(100); //**********
        if got_smpls == 1:
            break
        time.sleep(100e-3)  #sleep(100);
    if got_smpls != 1:
        print('don''t have samples ?!')
    N = smpls_rtd
    t = t0 + np.arange(N)*dt
    #[ch1, ch2, DIG, err] = cs32_sampleBuf_get(CAU, N, N, N);
    ##N=smpls_rtd; t = [0:N-1]*dt; [ch1, ch2, DIG, err] = cs32_sampleBuf_get(CAU, N, N, N);//modified on 21.07.2015 NY
    status = err_stat
    ##[ch1, ch2, DIG, t, CAU_stat, status] = cs32_getData(CAU); // , nData, ReplayStartTime, ReplayStopTime, FrameNumber, timeout);
    return t, ch1, ch2
    """
    
# -------------------------------------
def celiv_osca2_aquire_WF_not_needed(viOSC, FG, noscarep, trep_delay,Tmin):  # ret:  t, ch1, ch2
    # [CAU_status, err_status, err_code] = cs32_setAcqModus(CAU, AcquireMode, AcquisitionMode, WaveformAverages, NumSeqFrames)
    #   AcquireMode      How to acquire: 0 = Single, 1= automatic, 2 = triggered, 3 = stop Make sure this is 3 (stop) when initializing the driver.
    #   AcquisitionMode  Method of acquisition: 0 = sampled, 1= Peak captured, 2 = Filtered, 3= Repetitive, 4= Waveform avg, (for which make sure there are at least waveform avg +1 buffers).
    #   WaveformAverages ets how many waveforms to average in acquisition unit if acquisition mode = waveform avg. Values are 1, 4, 16, 64 and 128
    #   NumSeqFrames     acquire.NumSeqFrames; Sets the number of frames captured sequentially. If waveform avg method of capture set to 1. If capturing sequential frames,
    #                    set to number of frames to capture.
#    cs32_setAcqModus(CAU, 2, 4, noscarep, 1);
    #Nmax = 60000
    viOSC.write('ACQuire:STATE STOP')
    viOSC.write('ACQuire:MODe AVErage')
    viOSC.write(f'ACQuire:NUMAVg {noscarep:d}')
    viOSC.write('ACQuire:STATE RUN')
    viOSC.write('ACQuire:NUMACq?')
    n0 = int(viOSC.read().rstrip())
    time.sleep(20e-3)  #sleep(10)
    viOSC.write('ACQuire:NUMACq?')
    n1 = int(viOSC.read().rstrip())
    assert n1 == n0, f'found unexpected samples (n0={n0}, n1={n1})?!'
    
    for i in range(noscarep):
        FG.trigger()
        time.sleep(trep_delay)  #sleep(trep_delay*1e3);  // Delay(trep_delay)
    
    #FG.trigger()
    #time.sleep(trep_delay)  #sleep(trep_delay*1e3);  // Delay(trep_delay)

    viOSC.write('ACQuire:NUMACq?')
    n2 = int(viOSC.read().rstrip())
    assert n2 == n1 + noscarep, f'found unexpected samples (n2={n2}, n1={n1})?!'

    i_start, n_pt = 0, 2500 # n_pts_max = 2500
    t1, ch1, pre1 = t20_getData(viOSC, i_start, n_pt, '1')
    t2, ch2, pre2 = t20_getData(viOSC, i_start, n_pt, '2')
    t = t1
    return t, ch1, ch2


# -------------------------------------
# [a,dt,f, nt0, ntp, nth, ntn, ntd, n_]=k3390_calc_CELIV_WF(t0, tp, th, tn, td, te, n_pulses);
def celiv_calc_OTRACE_WF(t0, tp, th, tn, td, te, n_pulses):  # ret:  a,dt,f, nt0, ntp, nth, ntn, ntd, n_,Tmin
    Tmin = t0+ n_pulses*(tp+th+tn+td) - td + te
    #Tmin = n_pulses*(tp+th+tn+td) - td + te;//For MIS-CELIV // 21.07.2015
    dt, n_WF, f, T = k3390_calc_dt_of_WF_nat(Tmin)
    rate = 1/dt
    nt0 = max(1, int(round(0.5 + rate * t0)))     # a) 0.5  rounding, b) 0.5 artificial t0 contribution, 1st point belongs only half to ramp, even if t0=0s
    ntp = max(1, int(round(rate * tp)))           # w/o 1st (low) point of ramp  (set by t0-phase (or tn,td-phase))
    nth = max(0, int(round(rate * th)))
    ntn = max(1, int(round(rate * tn)))           # w/o 1st (high) point of ramp (set by tp,th-phase)
    ntd = max(0, int(round(rate * td)))
    n_ = nt0 + (ntp + nth + ntn) + (n_pulses-1) * (ntd + ntp + nth + ntn)	# # of data w/o te
    a = np.zeros(n_WF)
    n0 = nt0
    for i in range(n_pulses):
        #a(n0+[1:ntp]) = [1:ntp]/ntp;    n0 = n0+ntp;
        a[n0:n0+ntp] = np.arange(1,ntp+1)/ntp
        n0 += ntp  
        #a(n0+[1:nth]) = 1;              n0 = n0+nth;
        a[n0:n0+nth] = 1
        n0 += nth
        #a(n0+[1:ntn]) = [ntn:-1:1]/ntn; n0 = n0+ntn;
        a[n0:n0+ntn] = np.arange(ntn,0,-1)/ntn
        n0 += ntn
        if i == n_pulses-1:
            break
        #a(n0+[1:ntd]) = 0;              n0 = n0+ntd;
        a[n0:n0+ntd] = 0
        n0 += ntd
    return a, dt, f, nt0, ntp, nth, ntn, ntd, n_, Tmin

# -------------------------------------
# [a,dt,f, nt0, ntp, nth, ntn, ntd, n_]=k3390_calc_CELIV_WF(t0, tp, th, tn, td, te, n_pulses);
def celiv_calc_ecd_WF(t0, tp, th, tn, td, tn2, tl, tp2, td2, te, n_pulses, dVp, dVn, dVp2, dVn2):  # ret:  a,dt,f, nt0, ntp, nth, ntn, ntd,ntn2,ntl,ntp2,ntd2, n_,Tmin,Vmax
    #Tmin = n_pulses*(tp+th+tn+td+tn2+tl+tp2+td2) - td -td2 + te;//For MIS-CELIV NY 21.07.2015
    Tmin = t0+ n_pulses*(tp+th+tn+td+tn2+tl+tp2+td2) - td -td2 + te
    dt, n_WF, f, T = k3390_calc_dt_of_WF_nat(Tmin)
    rate = 1/dt;
    nt0 = max(1, int(round(0.5 + rate * t0)))     # a) 0.5  rounding, b) 0.5 artificial t0 contribution, 1st point belongs only half to ramp, even if t0=0s
    ntp = max(1, int(round(rate * tp)))           # w/o 1st (low) point of ramp  (set by t0-phase (or tn,td-phase))
    nth = max(0, int(round(rate * th)))
    ntn = max(1, int(round(rate * tn)))           # w/o 1st (high) point of ramp (set by tp,th-phase)
    ntd = max(0, int(round(rate * td)))
    ntn2 = max(1, int(round(rate * tn2)))           # w/o 1st (high) point of ramp (set by tp,th-phase)
    ntl = max(0, int(round(rate * tl)))
    ntp2 = max(1, int(round(rate * tp2)))           # w/o 1st (low) point of ramp  (set by t0-phase (or tn,td-phase))
    ntd2 = max(0, int(round(rate * td2)))
    #n_ = nt0 + (ntp + nth + ntn + ntd + ntn2 + ntl + ntp2 +ntd2) * (n_pulses);	// # of data w/o te
    n_ = nt0 + (ntp + ntn + ntd + ntn2 + ntp2 +ntd2) * (n_pulses)
    n_ = nt0 + (ntp + nth + ntn + ntd + ntn2 + ntl + ntp2 +ntd2) * (n_pulses)
    a = np.zeros(n_WF)
    n0 = nt0

    for i in range(n_pulses):
        #a(n0+[1:ntp]) = [1:ntp]/ntp *dVp;                   n0 = n0+ntp;
        a[n0:n0+ntp] = np.arange(1,ntp+1)/ntp *dVp
        n0 += ntp
        #a(n0+[1:nth]) = 1*dVp;                              n0 = n0+nth;
        a[n0:n0+1] = 1*dVp
        n0 += nth
        #a(n0+[1:ntn]) = [ntn:-1:1]/ntn*dVn+dVp-dVn;         n0 = n0+ntn;
        a[n0:n0+ntn] = np.arange(ntn,0,-1)/ntn*dVn+dVp-dVn
        n0 += ntn
        #a(n0+[1:ntd]) = dVp-dVn;                            n0 = n0+ntd;
        a[n0:n0+ntd] = dVp-dVn
        n0 += ntd
        #a(n0+[1:ntn2]) = dVp-dVn-([1:ntn2]/ntn2)*dVn2;      n0 = n0+ntn2;
        a[n0:n0+ntn2] = dVp-dVn-(np.arange(1,ntn2+1)/ntn2)*dVn2
        n0 += ntn2
        #a(n0+[1:ntl]) = dVp-dVn-dVn2;                       n0 = n0+ntl;
        a[n0:n0+ntl] = dVp-dVn-dVn2
        n0 += ntl
        #a(n0+[1:ntp2]) = dVp-dVn-dVn2+[1:ntp2]/ntp2 *dVp2;  n0 = n0+ntp2;
        a[n0:n0+ntp2] = dVp-dVn-dVn2+np.arange(1,ntp2+1)/ntp2 *dVp2
        n0 += ntp2
        if i == n_pulses-1:
            break
        #a(n0+[1:ntd2]) = dVp-dVn-dVn2+dVp2;                 n0 = n0+ntd2;        
        a[n0:n0+ntd2] = dVp-dVn-dVn2+dVp2
        n0 += ntd2
    Vmax = np.abs(a).max()
    a = a/Vmax
    return a, dt, f, nt0, ntp, nth, ntn, ntd,ntn2,ntl,ntp2,ntd2, n_, Tmin, Vmax


# -------------------------------------
def celiv_osca2_aquire_WF(viOSC, FG, noscarep, trep_delay):  # ret:  t, ch1, ch2
    if noscarep==1:
        viOSC.write("ACQ:MOD SAM")		# ACQuire:MODe { SAMple | PEAKdetect | AVErage } p. 2-46
    else:
        viOSC.write("ACQ:MOD AVE")		# ACQuire:MODe { SAMple | PEAKdetect | AVErage } p. 2-46
        viOSC.write(f"ACQ:NUMAV {noscarep:d}")
    #
    viOSC.write("ACQ:STATE 1")		# ACQuire:STATE { OFF | ON | RUN | STOP | <NR1> } p. 2-49; OFF | STOP | <NR1> = 0 stops acquisitions; ON | RUN | <NR1> != 0 starts acquisition
	# ensure command is executed
    viOSC.write("ACQ:STATE?")		# ACQuire:STATE? p. 2-50; -> 0 or 1
    ACQ_STATE = viOSC.read()    #buffer = blanks(64); [ACQ_STATE, status, n] = viRead(viOSC, buffer);
    #
    for i in range(noscarep):
        FG.trigger()
        time.sleep(trep_delay)  #sleep(trep_delay*1e3);  // Delay(trep_delay)
       
    t, ch1, pre = t20_getData(viOSC, 0, 2500, '1')
    t, ch2, pre = t20_getData(viOSC, 0, 2500, '2')
    return t, ch1, ch2


# -------------------------------------
"""
function [a,dt,f, nt0, ntp, nth, ntn, ntd,ntn2,ntl,ntp2,ntd2, n_,Tmin,Vmax,Vmin]=ecd_calc_WF(t0, tp, th, tn, td, tn2, tl, tp2, td2, te, n_pulses, V0, dVp, dVn, dVp2, dVn2)
    // Tmin - Minimum Puls Train time
    Tmin = t0+ n_pulses*(tp+th+tn+td+tn2+tl+tp2+td2)  + te;
    //Tmin = n_pulses*(tp+th+tn+td+tn2+tl+tp2+td2) - td -td2 + te;//modified on 21.07.2015 NY
    // dt   - Time of step width of Function Generator 
    // n_WF - Number of waveform points
    // f    - Frequency
    // T    - Period
    [dt, n_WF, f, T] = k3390_calc_dt_of_WF_nat(Tmin)
    rate = 1/dt;
    nt0 = max([1, round(0.5 + rate * t0)]);     // a) 0.5  rounding, b) 0.5 artificial t0 contribution, 1st point belongs only half to ramp, even if t0=0s
    ntp = max([1, round(rate * tp)]);           // w/o 1st (low) point of ramp  (set by t0-phase (or tn,td-phase))
    nth = max([0, round(rate * th)]);
    ntn = max([1, round(rate * tn)]);           // w/o 1st (high) point of ramp (set by tp,th-phase)
    ntd = max([0, round(rate * td)]);
    ntn2 = max([1, round(rate * tn2)]);           // w/o 1st (high) point of ramp (set by tp,th-phase)
    ntl = max([0, round(rate * tl)]);
    ntp2 = max([1, round(rate * tp2)]);           // w/o 1st (low) point of ramp  (set by t0-phase (or tn,td-phase))
    ntd2 = max([0, round(rate * td2)]);
    //n_ = nt0 + (ntp + nth + ntn + ntd + ntn2 + ntl + ntp2 +ntd2) * (n_pulses);	// # of data w/o te
//    n_ = nt0 + (ntp + ntn + ntd + ntn2 + ntp2 +ntd2) * (n_pulses);
    n_ = nt0 + (ntp + nth + ntn + ntd + ntn2 + ntl + ntp2 +ntd2) * (n_pulses);
    a = zeros(1,n_WF);
    n0 = nt0;
        //a(1:nt0)=V0;
    for(i=[1:n_pulses])
        a(n0+[1:ntp]) = [1:ntp]/ntp *dVp;                   n0 = n0+ntp;
        a(n0+[1:nth]) = 1*dVp;                              n0 = n0+nth;
        a(n0+[1:ntn]) = [ntn:-1:1]/ntn*dVn+dVp-dVn;         n0 = n0+ntn;
        a(n0+[1:ntd]) = dVp-dVn;                            n0 = n0+ntd;
        a(n0+[1:ntn2]) = dVp-dVn-([1:ntn2]/ntn2)*dVn2;      n0 = n0+ntn2;
        a(n0+[1:ntl]) = dVp-dVn-dVn2;                       n0 = n0+ntl;
        a(n0+[1:ntp2]) = dVp-dVn-dVn2+[1:ntp2]/ntp2 *dVp2;  n0 = n0+ntp2;
        a(n0+[1:ntd2]) = dVp-dVn-dVn2+dVp2;                 n0 = n0+ntd2;        
        if(i==n_pulses) then break; end
    end
    a=a+V0
    Vmaxt=max(abs(a))
    Vmax=max(a)
    Vmin=min(a)
    a=a/Vmaxt


endfunction
"""

# -------------------------
# waveform:
#            _________  Vh
#          /          \
#        /             \
#  ____/                \_______ V0e
# | t0 | tp |  th    |tn|  te   |
#
# output: a()=-1..+1, ..
def ny_calc_WF(t0, tp, th, tn, te, V0e, Vh):  # ret: a,dt,f, nt0, ntp, nth, ntn, nte, n_, Tmin, Vmax, Vmin
    # Tmin - Minimum Puls Train time
    Tmin = t0+ (tp+th+tn)  + te
    # dt   - Time of step width of Function Generator 
    # n_WF - Number of waveform points
    # f    - Frequency
    # T    - Period
    dt, n_WF, f, T = k3390_calc_dt_of_WF_nat(Tmin)
    rate = 1/dt
    nt0 = max(1, int(round(0.5 + rate * t0)))     # a) 0.5  rounding, b) 0.5 artificial t0 contribution, 1st point belongs only half to ramp, even if t0=0s
    ntp = max(1, int(round(rate * tp)))           # w/o 1st (low) point of ramp  (set by t0-phase (or tn,td-phase))
    nth = max(0, int(round(rate * th)))
    ntn = max(1, int(round(rate * tn)))           # w/o 1st (high) point of ramp (set by tp,th-phase)
    nte = max(0, int(round(rate * te)))
    n_ = nt0 + (ntp + nth + ntn) + nte
    a = V0e + np.zeros(n_WF)
    n0 = nt0
    # a(1:nt0) = V0e;
    dV = Vh - V0e
    for i in range(1):
        #a(n0+[1:ntp]) = V0e + [1:ntp]/ntp *dV;              n0 = n0+ntp;
        a[n0:n0+ntp] = V0e + np.arange(1,ntp+1)/ntp *dV
        n0 += ntp
        #a(n0+[1:nth]) = Vh;                                 n0 = n0+nth;
        a[n0:n0+nth] = Vh
        n0 += nth
        #a(n0+[1:ntn]) = V0e + [ntn:-1:1]/ntn*dV;            n0 = n0+ntn;
        a[n0:n0+ntn] = V0e + np.arange(ntn,0,-1)/ntn*dV
        n0 += ntn
    
    a = a - (V0e + Vh)/2
    a = a / (dV/2)     # a goes now from -1 .. +1
    
    Vmax = Vh
    Vmin = V0e
    if Vmax < Vmin:
        a = -a
        Vx = Vmin
        Vmin = Vmax
        Vmax = Vx
    return a,dt,f, nt0, ntp, nth, ntn, nte, n_, Tmin, Vmax, Vmin

