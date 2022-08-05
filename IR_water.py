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
output_name = "DI_water_IR_1"
adcOffset = 31
carrierFreq_MHz = 14.893133
nScans = 1
nEchoes = 1
# all times in microseconds
# note that acq_time_ms is always milliseconds
p90_us = 4.401
FIR_rd = 7e6
vd_list_us = np.linspace(5e1,7e6,6)
max_power = 3.98  # W
power_steps = 14
threedown = True
SW_kHz = 3.9 # AAB and FS have found the min SW without loss to be 1.9 kHz
acq_time_ms = 1024.0  # below 1024 is **strongly discouraged**
tau_us = 3500  # 3.5 ms is a good number
uw_dip_center_GHz = 9.81
uw_dip_width_GHz = 0.02
date = '220524'#datetime.now().strftime("%y%m%d")
# }}}
# {{{Power settings
dB_settings = gen_powerlist(max_power, power_steps + 1, three_down=threedown)
T1_powers_dB = gen_powerlist(max_power, 5, three_down=False)
T1_node_names = ["FIR_%0.1fdBm" % j for j in T1_powers_dB]
logger.info("dB_settings", dB_settings)
logger.info("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
logger.info("T1_powers_dB", T1_powers_dB)
logger.info("correspond to powers in Watts", 10 ** (T1_powers_dB / 10.0 - 3))
myinput = input("Look ok?")
if myinput.lower().startswith("n"):
    raise ValueError("you said no!!!")
# }}}
# {{{ these change if we change the way the data is saved
IR_postproc = "spincore_IR_v1"
Ep_postproc = "spincore_ODNP_v3"
# }}}
powers = 1e-3 * 10 ** (dB_settings / 10.0)
fl = psp.figlist_var()
save_file = True
nPoints = int(acq_time_ms * SW_kHz + 0.5)
acq_time_ms = nPoints / SW_kHz
pad_us = 0
IR_ph1_cyc = psp.r_[0, 2]
IR_ph2_cyc = psp.r_[0, 2]
# {{{ check for file
myfilename = date + "_" + output_name + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}
nPhaseSteps = 4
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts


# {{{run IR
with power_control() as p:
    retval_IR = p.dip_lock(
        uw_dip_center_GHz - uw_dip_width_GHz,
        uw_dip_center_GHz + uw_dip_width_GHz,
    )
    p.start_log()
    ini_time = time.time()  # needed b/c data object doesn't exist yet
    p.mw_off()
    time.sleep(5)
    vd_data = run_IR(
        nPoints=nPoints,
        nEchoes=nEchoes,
        vd_list_us=vd_list_us,
        nScans=2,
        adcOffset=adcOffset,
        carrierFreq_MHz=carrierFreq_MHz,
        p90_us=p90_us,
        tau_us=tau_us,
        repetition=FIR_rd,
        output_name=output_name,
        SW_kHz=SW_kHz,
        ph1_cyc=IR_ph1_cyc,
        ph2_cyc=IR_ph2_cyc,
        ret_data=None,
    )
    vd_data.set_prop("start_time", ini_time)
    vd_data.set_prop("stop_time", time.time())
    meter_power = -999
    acq_params = {
        j: eval(j)
        for j in dir()
        if j
        in [
            "adcOffset",
            "carrierFreq_MHz",
            "amplitude",
            "nScans",
            "nEchoes",
            "p90_us",
            "deadtime_us",
            "FIR_rd",
            "SW_kHz",
            "nPoints",
            "deblank_us",
            "tau_us",
            "MWfreq",
            "acq_time_ms",
            "meter_power",
        ]
    }
    vd_data.set_prop("acq_params", acq_params)
    vd_data.set_prop("postproc_type", IR_postproc)
    vd_data.name("FIR_noPower")
    vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph1_cyc), len(IR_ph2_cyc), -1])
    vd_data.setaxis("ph1", IR_ph1_cyc / 4)
    vd_data.setaxis("ph2", IR_ph2_cyc / 4)
    # Need error handling (JF has posted something on this..)
    vd_data.hdf5_write(myfilename)
    logger.debug("\n*** FILE SAVED ***\n")
    logger.debug("Name of saved data", vd_data.name())
    for j, this_dB in enumerate(T1_powers_dB):
        if j == 0:
            MWfreq = p.dip_lock(
                uw_dip_center_GHz - uw_dip_width_GHz,
                uw_dip_center_GHz + uw_dip_width_GHz,
            )
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            # JF notes that the following works for powers going up, but not
            # for powers going down -- I don't think this has been a problem to
            # date, and would rather not potentially break a working
            # implementation, but we should PR and fix this in the future.
            # (Just say whether we're closer to the newer setting or the older
            # setting.)
            if p.get_power_setting() >= this_dB:
                break
        if p.get_power_setting() < this_dB:
            raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        meter_power = p.get_power_setting()
        ini_time = time.time()
        vd_data = run_IR(
            nPoints=nPoints,
            nEchoes=nEchoes,
            vd_list_us=vd_list_us,
            nScans=nScans,
            adcOffset=adcOffset,
            carrierFreq_MHz=carrierFreq_MHz,
            p90_us=p90_us,
            tau_us=tau_us,
            repetition=FIR_rd,
            output_name=output_name,
            SW_kHz=SW_kHz,
            ret_data=None,
        )
        vd_data.set_prop("start_time", ini_time)
        vd_data.set_prop("stop_time", time.time())
        acq_params = {
            j: eval(j)
            for j in dir()
            if j
            in [
                "adcOffset",
                "carrierFreq_MHz",
                "amplitude",
                "nScans",
                "nEchoes",
                "p90_us",
                "deadtime_us",
                "repetition_us",
                "SW_kHz",
                "nPoints",
                "deblank_us",
                "tau_us",
                "MWfreq",
                "acq_time_ms",
                "meter_power",
            ]
        }
        vd_data.set_prop("acq_params", acq_params)
        vd_data.set_prop("postproc_type", IR_postproc)
        vd_data.name(T1_node_names[j])
        vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph1_cyc), len(IR_ph2_cyc), -1])
        vd_data.setaxis("ph1", IR_ph1_cyc / 4)
        vd_data.setaxis("ph2", IR_ph2_cyc / 4)
        vd_data.hdf5_write(myfilename)
    final_frq = p.dip_lock(
        uw_dip_center_GHz - uw_dip_width_GHz,
        uw_dip_center_GHz + uw_dip_width_GHz,
    )
    this_log = p.stop_log()
SpinCore_pp.stopBoard()
# }}}
with h5py.File(myfilename, "a") as f:
    log_grp = f.create_group("log")
    hdf_save_dict_to_group(log_grp, this_log.__getstate__())

