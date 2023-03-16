from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
#from hermitian_function_test import hermitian_function_test, zeroth_order_ph
from sympy import symbols
import pywt
fl = figlist_var()
t2 = symbols('t2')
filter_bandwidth = 20e3
for date,id_string in [
       #('201104','NiSO4_B12_resonator_nutation_2'),
       #('201020','Ni_solenoid_probe_nutation_2'),
       #('201208','Ni_sol_probe_nutation_amp_1'),
       #('210127','Ni_cap_probe_CPMG_nutation_1'),
       #('210128','TEMPOL_cap_probe_nutation_2'),
       #('210224','4AT_cap_probe_nutation_1'),
       #('210423','Ni_cap_probe_nutation_2'),
       #('210816','Ni_water_cap_probe_nutation_1'),
       ('211222','150mM_TEMPOL_1'),
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'nutation'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                #exp_type = 'ODNP_NMR_comp/old'))
                exp_type = 'ODNP_NMR_comp/nutation'))
    nPoints = s.get_prop('acq_params')['nPoints']
    nEchoes = s.get_prop('acq_params')['nEchoes']
    nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
    SW_kHz = s.get_prop('acq_params')['SW_kHz']
    nScans = s.get_prop('acq_params')['nScans']
    s.reorder('t',first=False)
    fl.next('nutation')
    fl.image(s)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.reorder(['ph1','ph2','p_90'])
    s.reorder('t2',first=False)
    rough_center = abs(s).convolve('t2',0.01).mean_all_but('t2').argmax('t2').item()
    rough_center = abs(s).mean_all_but('t2').argmax('t2').item()
    s.setaxis(t2-rough_center)
    fl.next('raw data -- coherence channels')
    s.ft(['ph2','ph1'])
    fl.image(s)
    s.ft('t2',shift=True)
    fl.show();quit()
    fl.next('FT raw data -- coherence channels')
    s = s['t2':(-750,750)]
    s = s['ph1',1]['ph2',0]
    fl.image(abs(s)['t2':(-5000,5000)])
    fl.show();quit()
