"""
Spin Echo
=========

To run this experiment, please open Xepr on the EPR computer, connect to
spectrometer, load the experiment 'set_field' and enable XEPR API. Then, in a
separate terminal, run the program XEPR_API_server.py, and wait for it to
tell you 'I am listening' - then, you should be able to run this program from
the NMR computer to set the field etc. 
"""

from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
from Instruments import power_control
fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'echo'
config_dict['date'] = date
config_dict['echo_counter'] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
#}}}
#{{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#}}}    
#{{{check total points
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{acquire echo
echo_data = run_spin_echo(
        nScans=config_dict['nScans'],
        indirect_idx = 0,
        indirect_len = 1,
        ph1_cyc = ph1_cyc,
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz = config_dict['carrierFreq_MHz'],
        nPoints = nPoints,
        nEchoes = config_dict['nEchoes'],
        p90_us = config_dict['p90_us'],
        repetition_us = config_dict['repetition_us'],
        tau_us = config_dict['tau_us'],
        SW_kHz = config_dict['SW_kHz'],
        ret_data = None)
#}}}
#{{{setting acq_params
echo_data.set_prop("postproc_type","proc_Hahn_echoph")
echo_data.set_prop("acq_params",config_dict.asdict())
echo_data.name(config_dict['type']+'_'+str(config_dict['echo_counter']))
#}}}
#{{{Look at raw data
if phase_cycling:
    echo_data.chunk('t',['ph1','t2'],[4,-1])
    echo_data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    if config_dict['nScans'] > 1:
        echo_data.setaxis('nScans',r_[0:config_dict['nScans']])
    echo_data.reorder(['ph1','nScans','t2'])
    fl.next('image')
    fl.image(echo_data.C.mean('nScans'))
#}}}    
target_directory = getDATADIR(exp_type='ODNP_NMR_comp/Echoes')
filename_out = filename + '.h5'
nodename = echo_data.name()
if os.path.exists(filename+'.h5'):
    print('this file already exists so we will add a node to it!')
    with h5py.File(os.path.normpath(os.path.join(target_directory,
        f"{filename_out}"))) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, lets delete it to overwrite")
            del fp[nodename]
    echo_data.hdf5_write(f'{filename_out}/{nodename}', directory = target_directory)
else:
    try:
        echo_data.hdf5_write(filename+'.h5',
                directory=target_directory)
    except:
        print(f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory")
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 -- I'm removing it")
            os.remove('temp.h5')
        echo_data.hdf5_write('temp.h5')
        print("if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!")
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",echo_data.name()))
print(("Shape of saved data",ndshape(echo_data)))
fl.show()
