from instrument_interfaces.interfaces import Connection
from pulses.pulse_types import Pulse


class PulseLine:
    """
    描述同个connection的脉冲序列，通过添加脉冲重复单元的方式来构建脉冲序列，脉冲重复单元可以是脉冲，也可以是脉冲序列
    """

    def __init__(self,
                 name: str = None,
                 ID: int = None,
                 init_pulse: list = None,
                 t_start: float = None,
                 connection: Connection = None):
        """
        :param name: 脉冲序列的名称
        :param ID: 脉冲序列的id
        :param init_pulse: 脉冲序列一开始的脉冲元素
        :param t_start: 脉冲序列的起始时间，单位为s
        :param connection: 脉冲序列的connection，用于确定脉冲序列的发送端和接收端，以及脉冲序列需要满足的条件
        """
        self.name = name
        if ID is None:
            ID = id(self)
        self.id = ID
        self.connection = connection
        self.sender = self.connection.sender
        self.acceptor = self.connection.acceptor
        # 把pulse_element装进字典中
        self.pulse_elements = {}
        if init_pulse is not None:
            self.pulse_elements["init_pulse"] = init_pulse
            self._config_repeat_and_delay('init_pulse')
        else:
            self.pulse_elements["init_pulse"] = []

        self.t_start = t_start
        self.duration = 0
        self.stop = 0
        # pulse_elements 按时间顺序写进列表中
        self.pulse_line = []
        # 时间线
        self.time_line = []

    def __repr__(self):
        return self._get_repr()

    def _get_repr(self):
        pulse_line_info = f'Pulse line info\n '\
                          f'\tname: {self.name}\n '\
                          f'\tstart time: {self.t_start} s'\
                          f'\tduration: {self.duration} s'\
                          f'\t pulse elements: {self.pulse_elements}'

        return pulse_line_info

    def __getitem__(self, pulse_element_name):
        return self.pulse_elements[pulse_element_name]

    def _config_repeat_and_delay(self, pulse_element_name, delay: float = 0, repeat: int = 1):
        """
        配置脉冲序列的重复次数, 脉冲序列的最后一位数字是重复次数
        :param pulse_element_name: 脉冲元素的名称
        :param repeat: 脉冲序列的重复次数
        :return:
        """
        # 如果repeat小于1，抛出异常
        if repeat < 1:
            raise ValueError(f"repeat {repeat} must be larger than 1")
        self.pulse_elements[pulse_element_name] = self.pulse_elements[pulse_element_name].append(repeat)
        self.pulse_elements[pulse_element_name] = self.pulse_elements[pulse_element_name].insert(0, delay)

    def check_repeat_and_delay(self, pulse_element: list = None, pulse_element_name: str = None)-> bool:
        """
        pulse_element和pulse_element_name两者输入其一
        :param pulse_element: 需要check的pulse_element
        :param pulse_element_name: 需要check的pulse_element的名字
        :return:
        """
        if pulse_element:
            if not isinstance(pulse_element[0], float):
                raise TypeError(f'The fist element of pulse_element should be delay not {type(pulse_element[0])}')
            if not isinstance(pulse_element[-1], int):
                raise TypeError(f'The fist element of pulse_element should be repeat not {type(pulse_element[-1])}')
            return True
        if pulse_element_name:
            if pulse_element_name in self.pulse_elements:
                if not isinstance(self.pulse_elements[pulse_element_name][0], float):
                    raise TypeError(f'The fist element of pulse_element should be delay not {type(pulse_element[0])}')
                if not isinstance(self.pulse_elements[pulse_element_name][-1], int):
                    raise TypeError(f'The fist element of pulse_element should be repeat not {type(pulse_element[-1])}')
                return True
            else:
                raise ValueError(f'pulse_element_name {pulse_element_name} does not exist')

    def add_pulse_element(self, pulse_element_name: str, pulse_element: list, delay: float = 0, repeat: int = 1):
        """
        添加一个脉冲重复单元
        :param delay: 脉冲重复单元的起始延迟时间，默认为0，单位为秒
        :param repeat: 重复次数，默认为1
        :param pulse_element_name: 脉冲重复单元的名称
        :param pulse_element: 脉冲重复单元，[pulse_element1, pulse_element2, ...]
        :return:
        """
        # 如果pulse_element 是空的，抛出异常
        if pulse_element is None:
            raise ValueError("pulse_element is None")
        # 如果pulse_element_name已经存在，抛出异常
        if pulse_element_name in self.pulse_elements:
            raise ValueError(f"pulse_element_name {pulse_element_name} already exists")
        self.pulse_elements[pulse_element_name] = pulse_element
        self._config_repeat_and_delay(pulse_element_name, delay, repeat)

    def config_pulse_elements(self, pulse_elements: dict):
        """
        通过字典的方式添加脉冲重复单元，字典的格式是{"pulse_element_name": [delay, pulse_element1, pulse_element2, ..., repeat]}
        :param pulse_elements:
        :return:
        """
        for pulse_element_name, pulse_element in pulse_elements.items():
            self.pulse_elements[pulse_element_name] = pulse_element

    def add_pulse_elements_to_pulse_line(self, order: list):
        """
        按照order的顺序将pulse_elements添加到pulse_line中, pulse_line格式是
        [[delay, pulse_element1, pulse_element2, ..., repeat], [delay, pulse_element3, pulse_element4, ..., repeat],...]
        :param order: pulse_elements的顺序
        :return:
        """
        if order is None:
            for pulse_element in self.pulse_elements.values():
                self.pulse_line.extend(pulse_element)
        else:
            for pulse_element_name in order:
                self.pulse_line.extend(self.pulse_elements[self.get_pulse_element_name[pulse_element_name]])

    def remove_pulse_elements_from_pulse_line(self, pulse_element_name: str):
        """
        将pulse_elements从pulse_line中移除
        :param pulse_element_name: 需要移除的pulse_elements名称
        :return:
        """
        if pulse_element_name in self.pulse_elements:
            self.pulse_line.remove(self.pulse_elements[pulse_element_name])
        else:
            raise ValueError(f"pulse_element_name {pulse_element_name} does not exist")

    def get_time_line(self):
        """
        将pulse_elements中脉冲单元的时间线统一到pulse_line的时间线上，计算出总的时长，并将脉冲单元的起始时间放到time_line中
        """
        stop = self.t_start
        for pulse_element in self.pulse_line:
            if self.check_repeat_and_delay(pulse_element):
                for pulse in pulse_element[1:-1]*pulse_element[-1]:
                    self.time_line.append(pulse_element[0]+pulse.t_start+stop)
                    stop += pulse_element[0]+pulse.t_start+pulse.duration
        self.duration = stop - self.t_start
        self.stop = stop

    @property
    def get_pulse_element_name(self):
        """
        获取pulse_elements的名称
        :return: pulse_elements的名称
        """
        names = []
        for name in self.pulse_elements.keys():
            names.append(name)
        return names
