from qcodes import Instrument
from instruments.meta_instruments import Channel, InstrumentChannels, ChannelType
from qcodes.instrument.parameter import Parameter
from qcodes.utils.validators import Numbers
from pulses.pulse_types import Pulse


class Connection:
    """
    连接多个channel的connection类
    """
    # Todo：传入输入源和输出源，然后以connection为主体来命名input channel
    def __init__(self,
                 attenuation: float = 0,
                 gain: float = 1,
                 filter_info: dict = None):
        """
        :param attenuation: 信号衰减量，单位为dBm
        :param gain: 信号增益，单位为a.u.
        :param filter_info: 信号通过的滤波器信息，包括滤波器的类型和截止频率
        """
        # self.connector = (input_channel, output_channel)
        self.attenuation = Parameter('attenuation',
                                     initial_value=attenuation,
                                     vals=Numbers(),
                                     unit='dBm')
        self.gain = Parameter('gain',
                              initial_value=gain,
                              vals=Numbers(),
                              unit='a.u.')
        self.filter_info = filter_info
        self.chain = tuple()
        self.chain_type = None

    def connect(self, output_channel: Channel, input_channel: Channel):
        """

        :param output_channel: 从仪器输出的channel，输入到connection中
        :param input_channel: 从connection输出的channel，输入到仪器中
        :return:
        """

        if output_channel.channel_type != input_channel.channel_type:
            raise TypeError('The channel type of output channel and input channel should be the same')

        if output_channel.input:
            raise TypeError('The output channel should not be an input channel')

        if not input_channel.input:
            raise TypeError('The input channel should not be an output channel')

        if self.chain_type is None:
            self.chain_type = output_channel.channel_type
        elif self.chain_type != output_channel.channel_type:
            raise TypeError(
                'The channel type of output channel and input channel should be the same as the previous channel')

        self.chain = self.chain + (output_channel, input_channel)

    def check_pulse(self, pulse: Pulse) -> bool:
        """
        检查输入的pulse的sender和acceptor是否在connection中
        :param pulse: 输入到connection中的pulse
        :return: 布尔值，True代表满足条件，False代表不满足条件
        """

        if pulse.sender is self.chain[0] and pulse.acceptor is self.chain[-1]:
            return True
        else:
            return False

    def check_conditions(self, pulse):
        for channel in self.chain:
            if channel.channel_type == ChannelType.DC:
                if not channel.condition(pulse.amplitude.get()):
                    return False
            elif channel.channel_type == ChannelType.AC:
                if not channel.condition(pulse.frequency.get()):
                    return False
            elif channel.channel_type == ChannelType.Fast:
                if not channel.condition(pulse.power.get()):
                    return False


"""
写interfaces的一般原则：
继承InstrumentChannels，将仪器类作为参数传入.
利用InstrumentChannels添加相应的channel，作为connection使用
"""


class ChipInterface(InstrumentChannels):

    def __int__(self, name: str):
        super().__init__(name)
        self._connections = {}
        self._instruments = {}


class InstrumentInterface(Instrument):
    def __init__(self,
                 instrument_name: str,
                 **kwargs):
        super().__init__(name=instrument_name + '_interface', **kwargs)
        self.instrument = self.find_instrument(instrument_name)
        self._input_channels = {}
        self._output_channels = {}
        self._channels = {}
        self.pulse_sequence = {}


if __name__ == '__main__':
    print('hello world')
