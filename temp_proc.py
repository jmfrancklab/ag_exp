from pylab import *
from pyspecdata import *
import SpinCore_pp
from datetime import datetime
with figlist_var() as fl:
    config_dict = SpinCore_pp.configuration('active.ini')
    date = datetime.now().strftime('%y%m%d')
    config_dict['type'] = 'echo'
    config_dict['date'] = date
    config_dict['echo_counter'] += 1
    filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
    d = find_file(filename, exp_type='ODNP_NMR_comp/Echoes',
            expno=config_dict['type']+'_'+str(config_dict['echo_counter']-1))
    d.ft('ph1', unitary=True)
    print(ndshape(d))
    if 'nScans' in d.dimlabels:
        d.mean('nScans')
    fl.next('raw data by coherence')
    for j in d.getaxis('ph1'):
        fl.plot(abs(d['ph1':j]), label=f'Δp={j}', alpha=0.5)
    d.ft('t2', shift=True)
    fl.next('ft')
    for j in d.getaxis('ph1'):
        fl.plot(abs(d['ph1':j]), label=f'Δp={j}', alpha=0.5)
    centerfrq = abs(d['ph1',+1]).argmax('t2').item()
    fl.next('zoomed')
    for j in d.getaxis('ph1'):
        fl.plot(abs(d['ph1':j]['t2':tuple(r_[-500,500]+centerfrq)]), label=f'Δp={j}', alpha=0.5)
    noise = d['ph1',r_[0,2,3]]['t2':centerfrq].run(std,'ph1')
    signal = abs(d['ph1',r_[0,2,3]]['t2':centerfrq])
    assert signal > 3*noise
    Field = config_dict['carrierFreq_MHz'] / config_dict['gamma_eff_MHz_G']
    config_dict['gamma_eff_MHz_G'] -= centerfrq*1e-6/Field
    config_dict.write()
