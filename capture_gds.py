from Instruments import *
from pyspecdata import *
from serial.tools.list_ports import comports
from pylab import axhline, text, gca
import numpy as np
expected_amp = 14e-3
input_amp = 492e-3
with figlist_var() as fl:
    with GDS_scope() as g:
        # {{{ choose settings we want
        g.reset()
        g.CH1.disp=True
        g.CH2.disp=True
        g.write(':CHAN1:DISP ON')
        g.write(':CHAN2:DISP OFF')
        g.write(':CHAN3:DISP OFF')
        g.write(':CHAN4:DISP OFF')
        g.CH1.voltscal=expected_amp*1.1/5 # set to a little more than amp/5
        g.timscal(50e-9, pos=0)
        g.write(':TIM:MOD WIND')
        print("window scale:")
        print(g.respond(':TIM:WIND:SCAL?'))
        g.write(':CHAN1:IMP 5.0E+1')
        g.write(':TRIG:SOUR CH1') 
        g.write(':TRIG:MOD AUTO')# or normal
        #g.write(':TRIG:HLEV 7.5E-2')
        g.write(':ACQ:MOD HIR')
        g.write(':CURS:MOD HV')
        g.write(':CURS:SOUR CH1')
        print("cursor mode:",g.respond(':CURS:MOD?'))
        mycursors = (expected_amp,-expected_amp)
        g.write(':CURS:V1P '
                +('%0.2e'%mycursors[0]).replace('e','E'))
        g.write(':CURS:V2P '
                +('%0.2e'%mycursors[1]).replace('e','E'))
        print("cursor:",g.respond(':CURS:V1P?'))
        print("cursor:",g.respond(':CURS:V2P?'))
        # }}}
        datalist = []
        for j in range(1,2): # this dumb but leave to keep flexible
            print("trying to grab data from channel",j)
            g.write(':SING')
            datalist.append(g.waveform(ch=j))
        data = concat(datalist,'ch').reorder('t')
        data.set_units('t','s')
    fl.next("data from all channels, raw")
    fl.plot(data, label='orig')
    N = ndshape(data)['t']
    # {{{ convert to analytic signal
    data.ft('t', shift=True)
    data = data['t':(0,None)]
    data *= 2
    data['t',0] *= 0.5
    data.ift('t')
    # }}}
    # {{{ show the manual cursor positions
    for y in mycursors:
        axhline(y=y,color='k', alpha=0.5)
    # }}}
    fl.plot(abs(data), label='analytic')
    ph = (data['t',1:]/data['t',:-1]).angle.sum('t').item()
    Dt = np.diff(data.getaxis('t')[r_[0,-1]]).item()
    frq = ph/Dt/2/pi
    # {{{ now, filter the signal
    data.ft('t')
    data['t':(None,frq-5e6)] = 0
    data['t':(frq+5e6,None)] = 0
    data.ift('t')
    # }}}
    fl.plot(data, label='filtered analytic signal')
    fl.plot(abs(data), label='filtered analytic signal')
    Vamp = abs(data['t':(1e-6,4e-6)]).mean('t').real.item()
    text(0.5,0.75,s='$V_{amp}=%0.4f$ mV, ratio %0.6g, dB %0.6f'%(
        Vamp/1e-3, input_amp/Vamp, 20*np.log10(input_amp/Vamp)),
            transform=gca().transAxes)
