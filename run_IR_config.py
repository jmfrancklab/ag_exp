'''Run Inversion Recovery at set power
======================================
You will need to manually set the power manually with Spyder and the B12. Once the power is set and the parameters are adjusted, you can run this program to collect the inversion recovery dataset at the set power.
'''
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_IR
import socket
import sys
import time
from datetime import datetime
fl = figlist_var()
#{{{importing acquisition parameters
values = SpinCore_pp.configuration('AG_config.ini')
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
#}}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
values['type'] = 'IR'
values['date'] = date
values['ir_counter'] += 1
filename = str(values['date'])+'_'+values['chemical']+'_'+values['type']
#}}}
phase_cycling = True
if phase_cycling:
    ph1 = r_[0,2]
    ph2 = r_[0,2]
    nPhaseSteps = 4
if not phase_cycling:
    ph1 = r_[0]
    ph2 = r_[0]
    nPhaseSteps = 1 
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#{{{ check for file
myfilename = filename+'.h5'
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}
vd_kwargs = {
        j:values[j]
        for j in ['krho_cold','krho_hot','T1water_cold','T1water_hot']
        if j in values.keys()
        }
vd_list_us = SpinCore_pp.vdlist_from_relaxivities(values['concentration'],**vd_kwargs)
vd_list = np.linspace(5e1,0.65e6,5)
print('***************************')
print(vd_list_us*1e6)  
vd_list_us *= 1e6
vd_data = run_IR(
        nPoints = nPoints,
        nEchoes=values['nEchoes'],
        vd_list_us = vd_list_us,
        nScans=values['nScans'],
        adcOffset = 30,#values['adc_offset'],
        carrierFreq_MHz=14.901055,#values['carrierFreq_MHz'],
        p90_us=4.401,#values['p90_us'],
        tau_us = 3500,#values['tau_us'],
        repetition=1e6,#values['repetition_us'],
        ph1_cyc = r_[0,2],#ph1,
        ph2_cyc = r_[0,2],#ph2,
        output_name= filename,
        SW_kHz=3.9,#values['SW_kHz'],
        ret_data = None)
vd_data.set_prop('acq_params',values)
vd_data.set_prop("postproc", "spincore_IR_v1")
vd_data.name(values['type']+'_'+str(values['ir_counter']))
if phase_cycling:
    vd_data.chunk("t",['ph1','ph2','t2'],[len(ph1),len(ph2),-1])
    vd_data.setaxis("ph1", ph1 / 4)
    vd_data.setaxis("ph2", ph2 / 4)
else:
    vd_data.rename('t','t2')
vd_data.hdf5_write(filename+'.h5',
        directory=getDATADIR(exp_type='ODNP_NMR_comp/inv_rec'))
SpinCore_pp.stopBoard();
vd_data.reorder(['ph1','ph2','vd','t2'])
fl.next('raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('abs raw data')
fl.image(abs(vd_data).setaxis('vd','#'))
vd_data.ft(['ph1','ph2'])
vd_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('FT abs raw data')
fl.image(abs(vd_data).setaxis('vd','#')['t2':(-1e3,1e3)])
fl.show()
