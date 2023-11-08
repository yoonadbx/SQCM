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
                channel.condition(pulse.amplitude)
            elif channel.channel_type == ChannelType.AC:
                channel.condition(pulse.frequency)
            elif channel.channel_type == ChannelType.Fast:
                channel.condition(pulse.power)
            elif channel.channel_type == ChannelType.Acq:
                channel.condition(pulse.memory_size)


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


class Layout:
    """
    代表一个以芯片为中心的布局，包含芯片的所有接口，以及接口之间的连接
    """

    def __init__(self, instrument_interfaces: list = None, connections: list = None):
        """
        :param instrument_interfaces: 一个列表，包含所有的仪器接口
        :param connections: 一个列表，包含所有的连接
        """
        if instrument_interfaces is None:
            instrument_interfaces = []
        self.instrument_interfaces = self.instrument_interfaces_as_dict(instrument_interfaces)
        if connections is None:
            connections = []
        self.connections = connections
        self.pulse_sequence = None

    def __eq__(self, other):
        """
        重载==操作符，使得可以通过layout1 == layout2的方式判断两个layout是否相同
        """
        return self.instrument_interfaces == other.instrument_interfaces and self.connections == other.connections

    @staticmethod
    def instrument_interfaces_as_dict(instrument_interfaces: list):
        """
        将输入的instrument_interfaces转化为字典
        :return:返回一个以仪器名为key，仪器接口为value的字典
        """
        interface_dict = {}
        for interface in instrument_interfaces:
            interface_dict[interface.name] = interface
        return interface_dict

    def load_connections(self, connections_dicts: list):
        """
        从一个列表中加载所有的连接
        :param connections_dicts: 一个列表，包含所有的连接
        :return:
        """
        for connection_dict in connections_dicts:
            self.add_connection(**connection_dict)

    def add_connection(self, output_arg: str, input_arg: str, **kwargs):
        """
        添加一个连接
        :param output_arg: 输出端口，格式为'仪器名.通道名'
        :param input_arg: 输入端口，格式为'仪器名.通道名'
        :param kwargs: 连接的其他参数，例如，衰减量，增益，滤波器信息等
        :return:
        """
        output_arg = output_arg.split('.')
        input_arg = input_arg.split('.')

        output_instrument = output_arg[0]
        output_channel = output_arg[1]
        input_instrument = input_arg[0]
        input_channel = input_arg[1]

        output_interface = self.instrument_interfaces[output_instrument]
        input_interface = self.instrument_interfaces[input_instrument]

        output_channel = output_interface.get_channel(output_instrument+'.'+output_channel)
        input_channel = input_interface.get_channel(input_instrument+'.'+input_channel)

        connection = Connection(**kwargs)
        connection.connect(output_channel, input_channel)
        if not self._is_same_connection(connection):
            self.connections.append(connection)
        else:
            print('The connection already exists!')

    def add_connection_infoes(self, connection: int, attenuation: float, gain: float, filters: list = None):
        """
        添加连接的信息
        :param connection: connection的序号
        :param attenuation: 信号衰减量，单位为dBm
        :param gain: 信号增益，单位为a.u.
        :param filters: 信号通过的滤波器信息，包括滤波器的类型和截止频率
        :return:
        """
        self.connections[connection].attenuation = attenuation
        self.connections[connection].gain = gain
        self.connections[connection].filter_info = filters

    def _is_same_connection(self, connection):
        """
        判断connection是否已经存在，如果存在则返回True，反之返回False
        :param connection: 判断对象
        :return: bool
        """
        for con in self.connections:
            if con == connection:
                return True
        return False

    def target_pulse_sequence(self, pulse_sequence):
        """
        将pulse_sequence中的pulse转化为target_pulse_sequence中的pulse
        :param pulse_sequence: 输入的pulse_sequence
        :return:
        """
        self.pulse_sequence = pulse_sequence
        self.pulse_sequence.target_pulse_sequence(self.connections)



