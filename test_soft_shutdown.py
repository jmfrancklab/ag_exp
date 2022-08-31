import numpy as np
import pyspecdata as psp
import os
import sys
import SpinCore_pp
import time
from Instruments import power_control
from datetime import datetime
from SpinCore_pp.ppg import run_spin_echo, run_IR
# do the same with the inversion recovery
from SpinCore_pp.power_helper import gen_powerlist
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
import h5py

logger = psp.init_logging(level="debug")
# {{{ Combined ODNP
# {{{ experimental parameters
# {{{ these need to change for each sample
output_name = "test_soft_shutdown"
adcOffset = 30
carrierFreq_MHz = 14.616346
nScans = 1
nEchoes = 1
# all times in microseconds
# note that acq_time_ms is always milliseconds
p90_us = 4.401
repetition_us = 0.5e6
SW_kHz = 3.9  # AAB and FS have found the min SW without loss to be 1.9 kHz
acq_time_ms = 1024.0  # below 1024 is **strongly discouraged**
tau_us = 3500  # 3.5 ms is a good number
uw_dip_center_GHz = 9.69
uw_dip_width_GHz = 0.02
date = '220624'#datetime.now().strftime("%y%m%d")
# }}}
fl = psp.figlist_var()
nPoints = int(acq_time_ms * SW_kHz + 0.5)
acq_time_ms = nPoints / SW_kHz
pad_us = 0
Ep_ph1_cyc = psp.r_[0, 1, 2, 3]
nPhaseSteps = 4
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts

# {{{run enhancement
with power_control() as p:
   # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(9.57,9.61)
    p.mw_off()
    DNP_ini_time = time.time()
    DNP_data = run_spin_echo(
        nScans=nScans,
        indirect_idx=0,
        indirect_len=1,
        ph1_cyc=Ep_ph1_cyc,
        adcOffset=adcOffset,
        carrierFreq_MHz=carrierFreq_MHz,
        nPoints=nPoints,
        nEchoes=nEchoes,
        p90_us=p90_us,
        repetition=repetition_us,
        tau_us=tau_us,
        SW_kHz=SW_kHz,
        output_name=output_name,
        indirect_fields=("start_times", "stop_times"),
        ret_data=None,
    ) 
    retval = p.dip_lock(9.57,9.61)
    quit()
    p.set_power(this_dB)
    for k in range(10):
        time.sleep(0.5)
        if p.get_power_setting() >= this_dB:
            break
    if p.get_power_setting() < this_dB:
        raise ValueError("After 10 tries, the power has still not settled")
    time.sleep(5)
    power_settings_dBm[j] = p.get_power_setting()
    time_axis_coords[j + 1]["start_times"] = time.time()
    run_spin_echo(
        nScans=nScans,
        indirect_idx=j + 1,
        indirect_len=len(powers) + 1,
        adcOffset=adcOffset,
        carrierFreq_MHz=carrierFreq_MHz,
        nPoints=nPoints,
        nEchoes=nEchoes,
        p90_us=p90_us,
        repetition=repetition_us,
        tau_us=tau_us,
        SW_kHz=SW_kHz,
        output_name=output_name,
        ret_data=DNP_data,
    )
    time_axis_coords[j + 1]["stop_times"] = time.time()

