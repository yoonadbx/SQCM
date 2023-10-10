#%%

from tools.scan import Scan
from qcodes.instrument import Parameter
import numpy as np
from qcodes.utils.validators import Numbers
from random import random
from tools.project import DataManager
from tools.logger import Logger

#%%

def dummyset(voltage):
    return voltage


def dummyget():
    return random()


#%%

I_sd = Parameter(name='I_sd', label='SET current', unit='A', set_cmd=None, get_cmd=dummyget)
v_sd = Parameter(name='v_sd', label='SET sd', unit='V', initial_value=0,
                 set_cmd=dummyset, get_cmd=None, vals=Numbers(max_value=1, min_value=-1))

#%%

scan_range = np.linspace(-1, 1, 100)

#%%

my_manager = DataManager()

#%%

my_logger = Logger(mkor4k='mk',
                   sample_name='DummyTest',
                   tester='xf')

#%%

my_scan = Scan(para_meas=I_sd,
               para_scan=v_sd,
               data_manager=my_manager,
               logger=my_logger,
               scaler=1e9)

#%%

my_scan.scan_1d(scan_x=0)
