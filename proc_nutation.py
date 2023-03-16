from pylab import *
from pyspecdata import *
from scipy.optimize import minimize
from pyspecProcScripts import hermitian_function_test,zeroth_order_ph,lookup_table,fl_mod,DCCT,select_pathway
from sympy import symbols
from numpy import *
fl = fl_mod()
t2 = symbols('t2')
logger = init_logging("info")
max_kHz = 200
signal_pathway = {'ph1':1,'ph2':0}
for searchstr,exp_type,nodename,postproc,freq_slice in [
    #['201211_Ni_sol_probe_nutation_1','nutation','nutation',
    #    'spincore_nutation_v1',(-5000,13000)],
    #['210302_210302_Ni_cap_probe_nutation_1','nutation','nutation',
    #    'spincore_nutation_v1',(-4e3,1.2e4)]
    ['230315_lg_probe_nutation_4','ODNP_NMR_comp/nutation','nutation',
        'spincore_nutation_v3',(-200,350)]
    ]:
    s = find_file(searchstr,exp_type=exp_type,expno=nodename,postproc=postproc,
            lookup=lookup_table,fl=fl)
    s_fullsw = s.C
    s.ift('t2')
    s.reorder(['ph1','ph2','indirect','t2'])
    t_max = s.getaxis('t2')[-1]
    rx_offset_corr = s['t2':(0.75*t_max,None)] #should be quarter of t_slice onward
    rx_offset_corr = rx_offset_corr.mean(['t2'])
    s -= rx_offset_corr
    s.ft('t2')
    fl.next('raw')
    fl.image(s.C.mean('nScans'))
    d = s_fullsw
    if 'amp' in s.dimlabels:
        plen = s.get_prop('acq_params')['p90_us']*1e-6
        logger.info(strm('pulse length is:',plen))
    s = s['t2':freq_slice]
    s.ift('t2')
    s.set_units('t2','s')
    best_shift,_ = hermitian_function_test(select_pathway(s,signal_pathway),
            echo_before = s.get_prop('acq_params')['tau']*1e-6*1.5,
            fl = fl)
    print(best_shift)
    s.setaxis('t2',lambda x: x-best_shift).register_axis({'t2':0})
    #{{{zeroth order phasing
    s /= zeroth_order_ph(select_pathway(s['t2',0],signal_pathway))
    s.ft('t2')
    fl.next('phase corrected')
    fl.image(s.C.mean('nScans'))
    #}}}
    s.ift('t2')
    s = s['t2':(0,None)]
    s *= 2
    s['t2':0] *= 0.5
    s /= zeroth_order_ph(select_pathway(s['t2':0],signal_pathway))
    s.ft('t2')
    fl.next('phased')
    fl.plot(select_pathway(s.C.mean('nScans'),signal_pathway))
     # {{{ do the centering before anything else!
    # in particular -- if you don't do this before convolution, the
    # convolution doesn't work properly!
    filter_t_const = 10e-3
    d.ift('t2')
    d.set_units('t2','s')
    fl.next('time')
    fl.plot(select_pathway(d.C,signal_pathway),alpha = 0.25)
    apo_fn = exp(-abs((d.fromaxis('t2')-d.get_prop('acq_params')['tau']*1e-6))/filter_t_const)
    fl.plot(apo_fn*abs(d.C).max())
    d *= apo_fn
    d.ft('t2')
    fl.next('apodized')
    fl.plot(select_pathway(d,signal_pathway))
    #}}}
    #{{{ selecting coherence and convolving
    s = select_pathway(s,signal_pathway)
    fl.next('select $\\Delta p$')
    s.reorder(['nScans','indirect','t2'])
    fl.image(s)
    #}}}
    if 'amp' in s.dimlabels:
        s.setaxis('amp',lambda x:x*plen)
        s.set_units('amp','s')
        ind_dim = '\\tau_p a'
        s.rename('amp',ind_dim)
    elif 'p_90' in s.dimlabels:
        ind_dim = 'p_90'
    elif 'indirect' in s.dimlabels:
        p_90 = s.getaxis('indirect')
        s.setaxis('indirect',p_90)
        s.rename('indirect','p_90')
        ind_dim = 'p_90'
    else:
        raise ValueError("not sure what the indirect dimenison is!!")
    fl.real_imag('phased data',s)
    fl.next('FT')
    title('FT to get $\gamma B_1/a$')
    s.ft(ind_dim,shift=True)
    fl.image(s[ind_dim:(-1e3*max_kHz,1e3*max_kHz)])
    fl.show();quit()
    fl.next('absFT')
    title('FT to get $\gamma B_1/a$')
    fl.image(abs(s[ind_dim:(-1e3*max_kHz,1e3*max_kHz)]))
    gridandtick(gca(),gridcolor=[1,1,1])
fl.show()

