from qcodes import Instrument
from qcodes.instrument.parameter import Parameter
from qcodes.utils.validators import Numbers


class InstrumentType:
    DAC = 'DAC'
    AWG = 'AWG'
    PSG = 'PSG'
    Chip = 'Chip'
    SwitchBox = 'SwitchBox'
    collection = [DAC, AWG, PSG,Chip,SwitchBox]


class Channel:
    def __init__(self,
                 instrument_name: str,
                 group:str=None,
                 id:int=None,
                 input:bool=False,
                 output:bool=False
                 ):
        self.insturment_name = instrument_name
        self.group = group
        self.id = id
        self.name = self.group+str(self.id)
        self.input = input
        self.output = output

    def __repr__(self):
        output_str = f"Channel {self.name} (group={self.group}, id={self.id})"
        if self.input:
            output_str += 'input'
        if self.output:
            output_str += 'output'

        return output_str


class connection:
    def __init__(self,
                 attenuation:float=0,
                 gain:float=1,
                 label:int=None,
                 input_channel=None,
                 output_channel=None):
        self.connector = (input_channel, output_channel)
        self.attenuation = Parameter('attenuation',
                                     initial_value=attenuation,
                                     vals=Numbers(),
                                     unit='dBm')
        self.gain = Parameter('gain',
                              initial_value=gain,
                              vals=Numbers(),
                              unit='a.u.')
        self.input_channel = input_channel
        self.output_channel = output_channel

    def check_conditions(self, pulse):
        if self.input_channel.amplitude_range.get():
            #ToDo: 将channenl同connection连接起来
            pass


class InstrumentInterface(Instrument):
    def __init__(self,
                 instrument_name:str,
                 **kwargs):
        super().__init__(name=instrument_name+'_interface', **kwargs)
        self.instrument = self.find_instrument(instrument_name)
        self._input_channels = {}
        self._output_channels = {}
        self._channels = {}
        self.pulse_sequence = {}


