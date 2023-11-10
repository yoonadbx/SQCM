from instruments.meta_instruments import Channel, InstrumentChannels, ChannelType
from pulses.pulse_types import Pulse


class Connection:
    """
    连接多个channel的connection类
    """

    # Todo：传入输入源和输出源，然后以connection为主体来命名input channel
    def __init__(self,
                 attenuation: float = 0,
                 gain: float = 1,
                 filters: list = None):
        """
        :param attenuation: 信号衰减量，单位为dBm
        :param gain: 信号增益，单位为a.u.
        :param filters: 信号通过的滤波器信息，包括滤波器的类型和截止频率
        """
        # self.connector = (input_channel, output_channel)
        self.attenuation = attenuation
        self.gain = gain
        self.filter_info = filters
        self.chain = tuple()
        self.chain_type = None

    def __repr__(self):
        """
        重载repr()操作符，使得可以通过print(connection)的方式打印connection的信息
        """
        return (f'Connection with channels:\n' +
                '\n'.join([str(channel)+'->' for channel in self.chain]) +
                f'\nattenuation: {self.attenuation} dBm, gain: {self.gain} a.u., \nfilter info: {self.filter_info}')

    def __str__(self):
        """
        重载str()操作符，使得可以通过print(connection)的方式打印connection的信息
        """
        return (f'Connection with channels:\n' +
                '\n'.join([str(channel) for channel in self.chain]) +
                f'\nattenuation: {self.attenuation} dBm, gain: {self.gain} a.u., \nfilter info: {self.filter_info}')

    def __eq__(self, other):
        """
        重载==操作符，使得可以通过connection1 == connection2的方式判断两个connection是否相同
        """
        return self.chain == other.chain

    def __len__(self):
        """
        重载len()操作符，使得可以通过len(connection)的方式获取connection中channel的数量
        """
        return len(self.chain)

    def __getitem__(self, item):
        """
        重载[]操作符，使得可以通过connection[index]的方式访问connection中的channel
        """
        return self.chain[item]

    def connect(self, output_channel: Channel, input_channel: Channel):
        """

        :param output_channel: 从仪器输出的channel，输入到connection中, 格式为'仪器名.通道名'，例如sp1060.ch1
        :param input_channel: 从connection输出的channel，输入到仪器中, 格式为'仪器名.通道名'，例如chip.ch1
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

    @property
    def sender(self):
        """
        获取connection的sender
        :return: sender
        """
        if len(self.chain) == 0:
            print('The connection is empty')
            return None
        return self.chain[0]

    @property
    def acceptor(self):
        """
        获取connection的acceptor
        :return: acceptor
        """
        if len(self.chain) == 0:
            print('The connection is empty')
            return None
        return self.chain[-1]

    def check_pulse(self, pulse: Pulse) -> bool:
        """
        检查输入的pulse的sender和acceptor是否在connection中
        :param pulse: 输入到connection中的pulse
        :return: 布尔值，True代表满足条件，False代表不满足条件
        """

        if pulse.sender is self.chain[0] and pulse.acceptor is self.chain[-1]:
            return True
        else:
            print('The sender or acceptor of the pulse are not in the connection')
            return False

    def check_conditions(self, pulse):
        for channel in self.chain:
            if channel.channel_type == ChannelType.DC:
                return channel.condition(pulse.amplitude)
            elif channel.channel_type == ChannelType.AC:
                return channel.condition(pulse.frequency)
            elif channel.channel_type == ChannelType.Fast:
                return channel.condition(pulse.power)
            elif channel.channel_type == ChannelType.Acq:
                return channel.condition(pulse.memory_size)
            else:
                raise ValueError(f'The channel type {channel.channel_type} does not exist')


class Interface(InstrumentChannels):

    def __init__(self, name: str, inst=None):
        super().__init__(name)
        self.instrument = inst

    def __repr__(self):
        out = f'{self.name} with channels:\n' + '\n'.join([str(channel) for channel in self.channels])
        return out

    def get_channel(self, channel_name):
        for channel in self.channels:
            if channel.channel_name == channel_name:
                return channel
        raise ValueError(f'No such channel named {channel_name}')
