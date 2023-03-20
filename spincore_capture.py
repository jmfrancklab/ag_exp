
from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
fl = figlist_var()
data_length = 2048
output_name = 'SC_noise_floor'
date = datetime.now().strftime('%y%m%d')
nScans=1
raw_data = SpinCore_pp.getData(data_length, output_name)
raw_data.astype(float)
data_array = []
data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
print(("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0]))
print(("RAW DATA ARRAY LENGTH:",shape(raw_data)[0]))
dataPoints = float(shape(data_array)[0])
for x in range(nScans):
    if x == 0:
        time_axis = linspace(0.0,2048,dataPoints)
        data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:nScans])
        data.name('signal')
        data.set_prop('acq_params',acq_params)
    data['nScans',x] = data_array
SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        data.hdf5_write(date+'_'+output_name+'.h5')
        print("FILE SAVED!")
        print(("Name of saved data",data.name()))
        print(("Units of saved data",data.get_units('t')))
        print(("Shape of saved data",ndshape(data)))
        save_file = False
    except Exception as e:
        print(e)
        print("EXCEPTION ERROR - FILE MAY ALREADY EXIST.")
        save_file = False

data.set_units('t','data')
# {{{ once files are saved correctly, the following become obsolete
print(ndshape(data))
fl.show();quit()


