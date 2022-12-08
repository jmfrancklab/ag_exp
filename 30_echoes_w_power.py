import numpy as np
from numpy import r_
from pyspecdata import *
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from pyspecdata import strm
import os, sys, time
import h5py
import SpinCore_pp
from SpinCore_pp.power_helper import gen_powerlist
from SpinCore_pp.ppg import run_spin_echo, run_IR
from Instruments import power_control
from datetime import datetime

logger = init_logging(level="debug")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
fl = figlist_var()
# {{{ import acquisition parameters
parser_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(parser_dict["acq_time_ms"] * parser_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
parser_dict["type"] = "ODNP"
parser_dict["date"] = date
parser_dict["odnp_counter"] += 1
filename = f"{parser_dict['date']}_{parser_dict['chemical']}_{parser_dict['type']}_{parser_dict['odnp_counter']}"
filename_out = filename + ".h5"
# }}}
# {{{phase cycling
Ep_ph1_cyc = r_[0, 1, 2, 3]
total_points = len(Ep_ph1_cyc) * nPoints
assert total_points < 2 ** 14, (
    "For Ep: You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
# }}}
# {{{ check for file
if os.path.exists(filename_out):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!"
        % filename_out
    )
# }}}
# {{{run enhancement
with power_control() as p:
    # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(
        parser_dict["uw_dip_center_GHz"] - parser_dict["uw_dip_width_GHz"] / 2,
        parser_dict["uw_dip_center_GHz"] + parser_dict["uw_dip_width_GHz"] / 2,
    )
    p.set_power(35.0)
    p.start_log()
    DNP_ini_time = time.time()
    DNP_data = run_spin_echo(
        nScans=parser_dict["nScans"],
        indirect_idx=0,
        indirect_len=29 + 1,
        ph1_cyc=Ep_ph1_cyc,
        adcOffset=parser_dict["adc_offset"],
        carrierFreq_MHz=parser_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=parser_dict["nEchoes"],
        p90_us=parser_dict["p90_us"],
        repetition_us=parser_dict["repetition_us"],
        tau_us=parser_dict["tau_us"],
        SW_kHz=parser_dict["SW_kHz"],
        indirect_fields=("start_times", "stop_times"),
        ret_data=None,
    )  # assume that the power axis is 1 longer than the
    #                         "powers" array, so that we can also store the
    #                         thermally polarized signal in this array (note
    #                         that powers and other parameters are defined
    #                         globally w/in the script, as this function is not
    #                         designed to be moved outside the module
    DNP_thermal_done = time.time()
    time_axis_coords = DNP_data.getaxis("indirect")
    time_axis_coords[0]["start_times"] = DNP_ini_time
    time_axis_coords[0]["stop_times"] = DNP_thermal_done
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j in range(29):
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= 35.0:
                break
        if p.get_power_setting() < 35.0:
            raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        time_axis_coords[j + 1]["start_times"] = time.time()
        run_spin_echo(
            nScans=parser_dict["nScans"],
            indirect_idx=j + 1,
            indirect_len= 29 + 1,
            adcOffset=parser_dict["adc_offset"],
            carrierFreq_MHz=parser_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=parser_dict["nEchoes"],
            p90_us=parser_dict["p90_us"],
            repetition_us=parser_dict["repetition_us"],
            tau_us=parser_dict["tau_us"],
            SW_kHz=parser_dict["SW_kHz"],
            ret_data=DNP_data,
        )
        time_axis_coords[j + 1]["stop_times"] = time.time()
    DNP_data.set_prop("stop_time", time.time())
    DNP_data.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
    DNP_data.setaxis("ph1", Ep_ph1_cyc / 4)
    DNP_data.setaxis("nScans", r_[0 : parser_dict["nScans"]])
    DNP_data.reorder(["ph1", "nScans", "t2"])
    DNP_data.name('echo')
    nodename = DNP_data.name()
    try:
        DNP_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("There is already a temp.h5 -- I'm removing it")
            os.remove("temp.h5")
            DNP_data.hdf5_write("temp.h5", directory=target_directory)
            filename_out = "temp.h5"
            input("change the name accordingly once this is done running!")
    logger.info("FILE SAVED")
    logger.debug(strm("Name of saved enhancement data", DNP_data.name()))
    logger.debug("shape of saved enhancement data", ndshape(DNP_data))
    this_log = p.stop_log()
    # }}}
parser_dict.write()
with h5py.File(os.path.join(target_directory, f"{filename_out}"), "a") as f:
    log_grp = f.create_group("log")
    hdf_save_dict_to_group(log_grp, this_log.__getstate__())
forplot = DNP_data.C
forplot.ft('t2',shift=True)
forplot.ft(['ph1'])
forplot.reorder(['ph1','nScans','indirect','t2'])
fl.next('raw freq')
fl.image(forplot)
fl.show()

