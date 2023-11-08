from pulses.pulse_sequcences import PulseLine
from pulses.pulse_types import Pulse
from instrument_interfaces.interfaces import Connection
from typing import List


class Layout:
    """
    代表一个以芯片为中心的布局，包含芯片的所有接口，以及接口之间的连接
    """

    def __init__(self, instrument_interfaces: list = None, connections: List[Connection] = None):
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
        self.pulse_sequence = {}

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

        output_channel = output_interface.get_channel(output_instrument + '.' + output_channel)
        input_channel = input_interface.get_channel(input_instrument + '.' + input_channel)

        connection = Connection(**kwargs)
        connection.connect(output_channel, input_channel)
        if not self._is_same_connection(connection):
            self.connections.append(connection)
        else:
            print('The connection already exists!')

    def add_connection_info(self, connection: int, attenuation: float, gain: float, filters: list = None):
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

    def config_pulse_line(self, line_name: str, connection: int, line_start: float = 0, init_pulse: List[Pulse] = None, pulse_elements: dict = None, order: list = None):
        """
        构造一个pulse line, 并放到pulse sequence中
        :param pulse_elements: 通过字典的方式添加脉冲重复单元，字典的格式是{"pulse_element_name": [delay, pulse_element1, pulse_element2, ..., repeat]}
        :param init_pulse: pulse line初始脉冲单元
        :param line_name: pulse line的名字
        :param connection: connection的序号
        :param line_start: pulse line开始的时间节点
        :param order: pulse elements的先后顺序
        :return:
        """
        self.pulse_sequence[line_name] = PulseLine(name=line_name,
                                                   connection=self.connections[connection],
                                                   t_start=line_start,
                                                   init_pulse=init_pulse)
        if pulse_elements is None:
            return None
        self.pulse_sequence[line_name].config_pulse_elements(pulse_elements)
        self.pulse_sequence[line_name].add_pulse_elements_to_pulse_line(order)
        self.pulse_sequence[line_name].get_time_line()

    def target_pulse_sequence(self):
        """
        将pulse_sequence中的pulse line传递给对应的instrument interface
        :return:
        """
        for key, value in self.pulse_sequence.items():
            if value.connection_conditions_satisfied():
                arg = value.sender.split('.')
                interface = self.instrument_interfaces[arg[0]]
                interface.pulse_implementation(value)

