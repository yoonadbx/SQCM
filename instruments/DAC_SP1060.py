import time
from time import sleep
from urllib import response
import numpy as np
import ctypes  # only for DLL-based instrument
import json
import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
                    ManualParameter, MultiParameter,
                    validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.utils.helpers import create_on_off_val_mapping
from qcodes.utils.validators import Numbers, Enum
import logging
import pyvisa as visa
from typing import Any, Dict, Iterable, List, Optional, TextIO, Tuple, cast
# helper functions

def val_to_dacval(val):
    return format(int((val+10)*838860.75),'x')

def dacval_to_val(dacval):
    return round((dacval/838860.75-10),6)

def check_error(code):
    if code == 0: # no error
        return
    elif code == 1:             
        raise Exception('ERROR: invalid DAC channel')
    elif code == 2:           
        raise Exception('ERROR: missing DAC value or status')
    elif code == 3:      
        raise Exception('ERROR: DAC value out of range')
    elif code == 4:       
        raise Exception('ERROR: mistyped')
    elif code == 5:      
        raise Exception('ERROR: remote writing not allowed')
    else:                    
        raise Exception('Error: unknown')
    return code

def parse_on_off(stat):
    if stat.startswith('0'):
        stat = 'Off'
    elif stat.startswith('1'):
        stat = 'On'
    return stat
log = logging.getLogger(__name__)

class SP1060_POLY (InstrumentChannel):

    def __init__(self, parent: Instrument, name: str, channel: str) -> None:
        super().__init__(parent, name)
        
        self.add_parameter("coefficients", 
                            set_cmd="C POLY-{} {} {} {} {}".format(channel,"{}","{}","{}","{}","{}",),
                          
                            )


class SP1060_RMP (InstrumentChannel):

    def __init__(self, parent: Instrument, name: str, channel: str) -> None:
        super().__init__(parent, name)

        self.add_parameter("stop", 
                            get_cmd="C RMP-{} STOP".format(channel),
                          
                            )
        self.add_parameter("hold", 
                            get_cmd="C RMP-{} HOLD".format(channel),
        
                            )

        self.add_parameter("start", 
                            get_cmd="C RMP-{} START".format(channel),
                          
                            )
        self.add_parameter("state", 
                            get_cmd="C RMP-{} S?".format(channel),
                            
                            )
        self.add_parameter("cycles_done", 
                            get_cmd="C RMP-{} CD?".format(channel),
                          
                            )
        self.add_parameter("step_done", 
                            get_cmd="C RMP-{} SD?".format(channel),
                          
                            )
        self.add_parameter("step_size", 
                            get_cmd="C RMP-{} SSV?".format(channel),
                          
                            )
        self.add_parameter("step_per_cycle", 
                            get_cmd="C RMP-{} ST?".format(channel),
                          
                            )
        self.add_parameter("ch_ready", 
                            get_cmd="C RMP-{} AVA?".format(channel),
                          
                            )
        self.add_parameter("dac_ch", 
                            get_cmd="C RMP-{} CH?".format(channel),
                            set_cmd="C RMP-{} CH ".format(channel,"{}"),
                            )
        self.add_parameter("start_voltage", 
                            get_cmd="C RMP-{} STAV?".format(channel),
                            set_cmd="C RMP-{} STAV {}".format(channel,"{}"),
                            )
        self.add_parameter("stop_voltage", 
                            get_cmd="C RMP-{} STOV?".format(channel),
                            set_cmd="C RMP-{} STOV {}".format(channel,"{}"),
                            )
        self.add_parameter("time", 
                            get_cmd="C RMP-{} RT?".format(channel),
                            set_cmd="C RMP-{} RT {}".format(channel,"{}"),
                            )
        self.add_parameter("shape", 
                            get_cmd="C RMP-{} RS?".format(channel),
                            set_cmd="C RMP-{} RS {}".format(channel,"{}"),
                            )
        self.add_parameter("cycles_set", 
                            get_cmd="C RMP-{} CS?".format(channel),
                            set_cmd="C RMP-{} CS {}".format(channel,"{}"),
                            )
        self.add_parameter("step_or_ramp", 
                            get_cmd="C RMP-{} STEP?".format(channel),
                            set_cmd="C RMP-{} STEP {}".format(channel,"{}"),
                            )
            


class SP1060_WAV (InstrumentChannel):

    def __init__(self, parent: Instrument, name: str, channel: str) -> None:

        super().__init__(parent, name)
        self.add_parameter("mem_size",
                           get_cmd="C WAV-{} MS?".format(channel),
                           )
        self.add_parameter("mem_clear",
                           get_cmd="C WAV-{} CLR".format(channel),
                           )
        self.add_parameter("mem_save",
                           get_cmd="C WAV-{} SAVE".format(channel),
                           )
        self.add_parameter("mem_linearization_DAC",
                           get_cmd="C WAV-{} LINCH?".format(channel),
                           )
        self.add_parameter("write_to_AWG",
                           get_cmd="C WAV-{} WRITE".format(channel),
                           )

        self.add_parameter("writting_busy",
                           get_cmd="C WAV-{} BUSY?".format(channel),
                           )
        self.channel = channel               
        
    def query_full_WAVmem(self):

        WAVmem_size = self.mem_size()
        crl = int(np.ceil(int(WAVmem_size)/1000))
        val = np.zeros(int(crl*1000))
        for i in range(crl):
            val[int(i*1000):int((i+1)*1000)] = self._parent.query_block_WAVmem(self.channel, i*1000)

        #val = self._parent.query_block_WAVmem(self.channel,start)
        return WAVmem_size,crl,val

class SP1060_AWG (InstrumentChannel):

    def __init__(self, parent: Instrument, name: str, channel: str) -> None:

        super().__init__(parent, name)
        self.add_parameter("state",
                           get_cmd="C AWG-{} S?".format(channel),
                           )
        self.add_parameter("period", 
                            get_cmd="C AWG-{} DP?".format(channel),
                          
                            )
        self.add_parameter("stop", 
                            get_cmd="C AWG-{} STOP".format(channel),
                          
                            )
        self.add_parameter("start", 
                            get_cmd="C AWG-{} START".format(channel),
                          
                            )
        self.add_parameter("cycles_done", 
                            get_cmd="C AWG-{} CD?".format(channel),
                          
                            )
        self.add_parameter("cycles", 
                            get_cmd="C AWG-{} CS?".format(channel),
                            set_cmd="C AWG-{} CS {}".format(channel,"{}"),
                            )

        self.add_parameter("dac_ch", 
                            get_cmd="C AWG-{} CH?".format(channel),
                            set_cmd="C AWG-{} CH {}".format(channel,"{}"),
                            )

        self.add_parameter("mem_size", 
                            get_cmd="C AWG-{} MS?".format(channel),
                            set_cmd="C AWG-{} MS {}".format(channel,"{}"),
                            )
        self.add_parameter("ext_trigger_mode", 
                            get_cmd="C AWG-{} TM?".format(channel),
                            set_cmd="C AWG-{} TM {}".format(channel,"{}"),
                            )
        
        self.add_parameter("auto_start", 
                            get_cmd="C AWG-{} AS?".format(channel),
                            set_cmd="C AWG-{} AS {}".format(channel,"{}"),
                            )

        self.add_parameter("reload_mem", 
                            get_cmd="C AWG-{} RLD?".format(channel),
                            set_cmd="C AWG-{} RLD {}".format(channel,"{}"),
                            )
        self.add_parameter("apply_polynomial", 
                            get_cmd="C AWG-{} AP?".format(channel),
                            set_cmd="C AWG-{} AP {}".format(channel,"{}"),
                            )
        self.add_parameter("adaptive_shift_voltage", 
                            get_cmd="C AWG-{} SHIV?".format(channel),
                            set_cmd="C AWG-{} SHIV {}".format(channel,"{}"),
                            )
        #self.add_parameter("full_mem",
        #                   get_cmd = self.query_full_WAVmem,
        #                    )
        self.channel=channel       


    def query_full_AWGmem(self):

        WAVmem_size = self.mem_size()
        crl = int(np.ceil(int(WAVmem_size)/1000))
        val = np.zeros(int(crl*1000))
        for i in range(crl):
            val[int(i*1000):int((i+1)*1000)] = self._parent.query_block_AWGmem(self.channel, i*1000)

        #val = self._parent.query_block_WAVmem(self.channel,start)
        return WAVmem_size,crl,val
    

class SP1060_Channel(InstrumentChannel):
    """
    This class is used to address the 8 channel
    """
    def __init__(self, parent: Instrument, name: str, channel: int) -> None:
        """
        Args:
            parent: The Instrument instance to which the channel is to be attached.
            name: The 'colloquial' name of the channel
            channel: The channel on the DAC SP927 in the range 1-8
        """
        #if channel not in range(1,9):
        #    raise ValueError('channel must be in range 1-9')
        super().__init__(parent, name)
        
        self.add_parameter('voltage',
                           label='Voltage',
                           get_cmd=self.get_voltage,
                           #get_cmd = '{} V?'.format(channel),
                           set_cmd=self.set_voltage,
                           #set_cmd=self.set_voltage,
                           get_parser=float,
                           unit='V',
                           )

        self.add_parameter('state',
                           label='Ouput enabled',
                           get_cmd='{} S?'.format(channel),
                           set_cmd='{} {}'.format(channel,'{:s}'),
                           vals=Enum('on', 'On', 'ON',
                                    'off', 'Off', 'OFF',1,0),
                           val_mapping={1: 'ON',
                                        0: 'OFF'}         
                           )

        self.add_parameter('bandwidth',
                           label='Ouput bandwidth',
                           get_cmd='{} BW?'.format(channel),
                           set_cmd='{} {}'.format(channel,'{:s}'),
                           vals=Enum("LBW","HBW"),
                            )
        self.add_parameter('dac_mode',
                           label='DAC or AWG',
                           get_cmd='{} M?'.format(channel),
                            )
        
        

        self.channel=channel
    


    def get_voltage(self):
        var_get =self._parent.ask('{} V?'.format(self.channel))
        self._parent.empty_buffer()
        head = "0x"
        var = head + var_get
        #print(var)
        Dec_get=int(var,16)
        return dacval_to_val(Dec_get)

    def get_hex(self):
        return self._parent.ask('{} V?'.format(self.channel))
    def set_voltage(self,voltage):
        Dec_set=int((voltage+10)*838860.75)
        Hex_set=hex(Dec_set)
        self._parent.write_cmd('{} {}'.format(self.channel,Hex_set[2:]))
        self._parent.empty_buffer()
        code = self._parent._write_response
        check_error(int(code))
        #if int(code) !=0:
        #    raise ValueError('Voltage setting faild, please check')
class DAC_SP1060(VisaInstrument):
    """
    This is the QCoDeS driver for the Yokogawa GS200 voltage and current source.

    Args:
      name: What this instrument is called locally.
      address: The GPIB address of this instrument
      kwargs: kwargs to be passed to VisaInstrument class
      terminator: read terminator for reads/writes to the instrument.
    """

    def __init__(self, name: str, address: str, terminator: str = "\r\n",
                 **kwargs) -> None:
        super().__init__(name, address, terminator=terminator, **kwargs)

        for ch in range(1,25):
            ch_name = 'ch{}'.format(ch)
            channel = SP1060_Channel(self, ch_name, ch)
            self.add_submodule(ch_name, channel)

        
        for ch in ["A","B","C","D"]:
            
            ch_name = 'AWG_{}'.format(ch)
            channel = SP1060_AWG(self, ch_name, ch)
            self.add_submodule(ch_name, channel)

        for ch in ["A","B","C","D"]:
            
            ch_name = 'WAV_{}'.format(ch)
            channel = SP1060_WAV(self, ch_name, ch)
            self.add_submodule(ch_name, channel)

        for ch in ["A","B","C","D","ALL"]:
            
            ch_name = 'RMP_{}'.format(ch)
            channel = SP1060_RMP(self, ch_name, ch)
            self.add_submodule(ch_name, channel)

        for ch in ["A","B","C","D"]:
            
            ch_name = 'POLY_{}'.format(ch)
            channel = SP1060_POLY(self, ch_name, ch)
            self.add_submodule(ch_name, channel)


        self.add_parameter('all_state_status',
                           label='All ouput status',
                           get_cmd='all S?',
                           set_cmd='all {}'.format('{}'),
                           vals=Enum('on', 'On', 'ON',
                                    'off', 'Off', 'OFF'),
                           )
        self.add_parameter('all_ch_bandwidth',
                           label='All channel bandwidth',
                           get_cmd='all BW?',
                           set_cmd='all {}'.format('{}'),
                           vals=Enum("LBW","HBW"),
                           )
        self.add_parameter('all_ch_voltage',
                           label='All channel voltage',
                           get_cmd=self.get_all_val,
                           set_cmd=self.set_all_val,
                            )
        self.add_parameter("AWG_AB_only",
                           get_cmd="C AWG-AB ONLY?",
                           set_cmd = "C AWG-AB ONLY {}".format("{}"),
                           
                           )
        self.add_parameter("AWG_CD_only",
                           get_cmd="C AWG-CD ONLY?",
                           set_cmd = "C AWG-CD ONLY {}".format("{}"),
                           
                           )
        self.add_parameter("AWG_AB_clock_period", 
                            get_cmd="C AWG-AB CP?",
                            set_cmd="C AWG-AB CP {}".format("{}"),
                            )
        self.add_parameter("AWG_CD_clock_period", 
                            get_cmd="C AWG-CD CP?",
                            set_cmd="C AWG-CD CP {}".format("{}"),
                            )
        self.add_parameter("AWG_1MHz_ref", 
                            get_cmd="C AWG 1MHz?",
                            set_cmd="C AWG 1MHz {}".format("{}"),
                            )
        self.add_parameter("SWG_new_or_saved_waveform", 
                            get_cmd="C SWG MODE?",
                            set_cmd="C SWG MODE {}".format("{}"),
                            )
        self.add_parameter("SWG_wavefunction", 
                            get_cmd="C SWG WF?",
                            set_cmd="C SWG WF {}".format("{}"),
                            docstring=  "0 = Sine function – for a Cosine function select a Phase [°] of 90°\r\n"
                                        "1 = Triangle function \r\n"
                                        "2 = Sawtooth function\r\n"
                                        "3 = Ramp function\r\n"
                                        "4 = Pulse function – the parameter Duty-Cycle [%] is applied",
                            )           
        self.add_parameter("SWG_desired_freq", 
                            get_cmd="C SWG DF?",
                            set_cmd="C SWG DF {}".format("{}"),
                            )    
        self.add_parameter("SWG_keep_or_adapt_AWG_freq", 
                            get_cmd="C SWG ACLK?",
                            set_cmd="C SWG ACLK {}".format("{}"),
                            )
        self.add_parameter("SWG_amplitude", 
                            get_cmd="C SWG AMP?",
                            set_cmd="C SWG AMP {}".format("{}"),
                            )
        self.add_parameter("SWG_dc_offset", 
                            get_cmd="C SWG DCV?",
                            set_cmd="C SWG DCV {}".format("{}"),
                            )
        self.add_parameter("SWG_phase", 
                            get_cmd="C SWG PHA?",
                            set_cmd="C SWG PHA {}".format("{}"),
                            )
        self.add_parameter("SWG_pulse_duty", 
                            get_cmd="C SWG DUC?",
                            set_cmd="C SWG DUC {}".format("{}"),
                            )
        self.add_parameter("SWG_mem_size", 
                            get_cmd="C SWG MS?",
                            set_cmd="C SWG MS {}".format("{}"),
                            )
        self.add_parameter("SWG_nearest_freq", 
                            get_cmd="C SWG NF?",
                            )
        self.add_parameter("SWG_clipping_status", 
                            get_cmd="C SWG CLP?",
                            )
        self.add_parameter("SWG_clock_period", 
                            get_cmd="C SWG CP?",
                            )
        self.add_parameter("SWG_waveform_mem", 
                            get_cmd="C SWG WMEM?",
                            set_cmd="C SWG WMEM {}".format("{}"),
                            val_mapping={"A":0,"B":1,"C":2,"D":3},
                            )
        self.add_parameter("SWG_selected_function", 
                            get_cmd="C SWG WFUN?",
                            set_cmd="C SWG WFUN {}".format("{}"),
                            docstring=  "0 = COPY to Wave-MEM -> Overwrite;\r\n"
                                        "1= APPEND to Wave-MEM @START\r\n"
                                        "2 = APPEND to Wave-MEM @END\r\n"
                                        "3 = SUM Wave-MEM @START\r\n"
                                        "4 = SUM Wave-MEM @END\r\n"
                                        "5 = MULTIPLY Wave-MEM @START\r\n"
                                        "6 = MULTIPLY Wave-MEM @END\r\n"
                                        "7 = DIVIDE Wave-MEM @START\r\n"
                                        "8 = DIVIDE Wave-MEM @END",
                                           
                            )
        
        self.add_parameter("SWG_linearization_to_DAC", 
                            get_cmd="C SWG LIN?",
                            set_cmd="C SWG LIN {}".format("{}"),
                            )
    def SWG_apply_wavefunction_to_mem(self):
        self.write_cmd("C SWG APPLY")

    def query_block_AWGmem(self, mem, block_start):
        self.empty_buffer()
        start = (hex(block_start))
        reply = self.write('AWG-{} {} BLK?'.format(mem,start[2:]))
        hex_val = reply.replace("\r\n","").split(';')

        head = "0x"
        val = np.zeros(len(hex_val))
        for i in range(len(hex_val)):
            val[i] = dacval_to_val(int(head + hex_val[i],16))
        return val

    def query_block_WAVmem(self, mem, block_start):
        self.empty_buffer()
        start = (hex(block_start))
        reply = self.write('WAV-{} {} BLK?'.format(mem,start[2:]))
        hex_val = reply.replace("\r\n","").split(';')
        val = np.zeros(len(hex_val))
        for i in range(len(hex_val)):
            val[i] = float(hex_val[i])

        return val
    

    


    def AWG_AB_start(self):
        
        self.write_cmd("C AWG-AB START")
        self.empty_buffer()
    def AWG_AB_stop(self):
        
        self.write_cmd("C AWG-AB STOP")
        self.empty_buffer()  

    def AWG_CD_start(self):
        
        self.write_cmd("C AWG-CD START")
        self.empty_buffer()
    def AWG_CD_stop(self):
        
        self.write_cmd("C AWG-CD STOP")
        self.empty_buffer() 

    def AWG_all_start(self):
        
        self.write_cmd("C AWG-ALL START")
        self.empty_buffer()
    def AWG_all_stop(self):
        
        self.write_cmd("C AWG-ALL STOP")
        self.empty_buffer() 


    def set_newWaveform(self, channel = '12', waveform = '0', frequency = '100.0', 
                        amplitude = '5.0', wavemem = '0'):
        """
        Write the Standard Waveform Function to be generated
        - Channel: [1 ... 24]
        Note: AWG-A and AWG-B only DAC-Channel[1...12], AWG-C and AWG-D only DAC-Channel[13...24]
        - Waveforms: 
            0 = Sine function, for a Cosine function select a Phase [°] of 90°
            1 = Triangle function
            2 = Sawtooth function
            3 = Ramp function
            4 = Pulse function, the parameter Duty-Cycle is applied
            5 = Gaussian Noise (Fixed), always the same seed for the random/noise-generator
            6 = Gaussian Noise (Random), random seed for the random/noise-generator
            7 = DC-Voltage only, a fixed voltage is generated
        - Frequency: AWG-Frequency [0.001 ... 10.000]
        - Amplitude: [-50.000000 ... 50.000000]
        - Wave-Memory (WAV-A/B/C/D) are represented by 0/1/2/3 respectively
        """
        memsave = ''
        if (wavemem == '0'):
            memsave = 'A'
        elif (wavemem == '1'):
            memsave = 'B'
        elif (wavemem == '2'):
            memsave = 'C'
        elif (wavemem == '3'):
            memsave = 'D'

        sleep_time = 0.02

        self.write('C WAV-B CLR') # Wave-Memory Clear.
        time.sleep(sleep_time)
        self.write('C SWG MODE 0') # generate new Waveform.
        time.sleep(sleep_time)
        self.write('C SWG WF ' + waveform) # set the waveform.
        time.sleep(sleep_time)
        self.write('C SWG DF ' + frequency) # set frequency.
        time.sleep(sleep_time)
        self.write('C SWG AMP ' + amplitude) # set the amplitude.
        time.sleep(sleep_time)
        self.write('C SWG WMEM ' + wavemem) # set the Wave-Memory.
        time.sleep(sleep_time)
        self.write('C SWG WFUN 0') # COPY to Wave-MEM -> Overwrite.
        time.sleep(sleep_time)
        self.write('C SWG LIN ' + channel) # COPY to Wave-MEM -> Overwrite.
        time.sleep(sleep_time)
        self.write('C AWG-' + memsave + ' CH ' + channel) # Write the Selected DAC-Channel for the AWG.
        time.sleep(sleep_time)
        self.write('C SWG APPLY') # Apply Wave-Function to Wave-Memory Now.
        time.sleep(sleep_time)
        self.write('C WAV-' + memsave + ' SAVE') # Save the selected Wave-Memory (WAV-A/B/C/D) to the internal volatile memory.
        time.sleep(sleep_time)
        self.write('C WAV-' + memsave + ' WRITE') # Write the Wave-Memory (WAV-A/B/C/D) to the corresponding AWG-Memory (AWG-A/B/C/D).
        time.sleep(0.5)
        self.write('C AWG-' + memsave + ' START') # Apply Wave-Function to Wave-Memory Now.

    def empty_buffer(self):
        # make sure every reply was read from the DAC 
       # while self.visa_handle.bytes_in_buffer:
       #     print(self.visa_handle.bytes_in_buffer)
       #     print("Unread bytes in the buffer of DAC SP1060 have been found. Reading the buffer ...")
       #     print(self.visa_handle.read_raw())
       #      self.visa_handle.read_raw()
       #     print("... done")
        self.visa_handle.clear() 

    def write(self, cmd):
        """
        Since there is always a return code from the instrument, we use ask instead of write
        TODO: interpret the return code (0: no error)
        """
        # make sure there is nothing in the buffer
        self.empty_buffer()  
        
        return self.ask(cmd)

    def write_cmd(self, cmd: str) -> None:
        self.visa_handle.write(cmd)
        for _ in range(cmd.count(';')+1):
            self._write_response = self.visa_handle.read()

    def set_all_val(self,val):
        self.write('ALL {}'.format(val_to_dacval(val)[:]))
        self._parent.empty_buffer()
        code = self._write_response
        check_error(int(code))

    def get_all_val(self):
        var_get = self.ask('ALL V?')
        I = np.zeros(24)
        i=0
        for p in var_get.split(';'):
            I[i] = dacval_to_val(int("0x"+p,16))
            i+=1
        return I

    '''def write(self, cmd: str) -> None:
        self.visa_handle.write(cmd)
        for _ in range(cmd.count(';')+1):
            self._write_response = self.visa_handle.read()'''

    def read(self) -> str:
        return self.visa_handle.read()

    def _wait_and_clear(self, delay: float = 0.5) -> None:
        time.sleep(delay)
        self.visa_handle.clear()

    def check_health(self):
        response = self.write("HEALTH?")
        return response
    def get_ip(self):
        reply = self.write("IP?")
        self.empty_buffer()
        return reply
    def get_serial(self):
        """
        Returns the serial number of the device
        Note that when querying "HARD?" multiple statements, each terminated
        by \r\n are returned, i.e. the device`s reply is not terminated with 
        the first \n received

        """
        self.write('HARD?')
        self._parent.empty_buffer()
        reply = self.visa_handle.read()
        time.sleep(0.01)
       # while self.visa_handle.bytes_in_buffer:
       #     self.visa_handle.read_raw()
       #     time.sleep(0.01)
        self.empty_buffer()
        return reply.strip()[3:]
    
    def get_firmware(self):
        """
        Returns the firmware of the device
        Note that when querying "HARD?" multiple statements, each terminated
        by \r\n are returned, i.e. the device`s reply is not terminated with 
        the first \n received

        """
        self.write('SOFT?')
        reply = self.visa_handle.read()
        time.sleep(0.01)
       # while self.visa_handle.bytes_in_buffer:
       #     self.visa_handle.read_raw()
       #     time.sleep(0.01)
        self.empty_buffer()
        return reply.strip()[-5:]
        
    
    def get_idn(self):
        SN = self.get_serial()
        FW = self.get_firmware()
        return dict(zip(('vendor', 'model', 'serial', 'firmware'), 
                        ('BasPI', 'LNHR DAC SP1060', SN, FW)))

        

    