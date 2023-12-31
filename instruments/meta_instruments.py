import artdaq
from artdaq.constants import AcquisitionType
from functools import partial
from random import gauss


class ConditionType:
    """
    Connection condition class 用于描述connection的类型
    """

    limitations = {'DC': ['low', 'high'], 'AC': ['cut_off'], 'Fast': ['max_power'], 'Acq': ['max_memory_size']}

    @classmethod
    def DC_condition(cls, low: float, high: float, amplitude: float):
        """
        DC_condition 用于描述DC信号的条件, 并判断输入的pulse电压是否满足条件
        :param high: DC信号的电压上限
        :param low: DC信号的电压下限
        :param amplitude: DC信号的幅度
        :return: 布尔值，True代表满足条件，False代表不满足条件
        """
        if low <= amplitude <= high:
            return True
        else:
            print(f'The amplitude {amplitude} V of the pulse is not in the range ({low} V, {high} V) of the DC channel')
            return False

    @classmethod
    def AC_condition(cls, cut_off: float, frequency: float):
        """
        AC_condition 用于描述AC信号的条件, 并判断输入的signal的频率，振幅，功率等是否满足条件
        :param cut_off: 截止频率
        :param frequency: AC信号的频率
        :return: 布尔值，True代表满足条件，False代表不满足条件
        """
        if frequency <= cut_off:
            return True
        else:
            print(f'The frequency {frequency} Hz of the pulse is above the range {cut_off} Hz of the AC channel')
            return False

    @classmethod
    def Fast_condition(cls, max_power: float, power: float):
        """
        Fast_condition 用于描述Fast信号的条件, 并判断输入的signal的功率等是否满足条件
        :param max_power: 最大的功率
        :param power: 输入的功率
        :return:
        """
        if power < max_power:
            return True
        else:
            print(f'The power {max_power} dBm of the pulse excess the range {power} dBm of the Fast channel')
            return False

    @classmethod
    def Acq_condition(cls, max_memory_size: int, memory_size: int):
        """
        Acq_condition 用于描述Acq信号的条件, 并判断输入的memory_size是否满足条件
        :param max_memory_size: 最大的memory_size
        :param memory_size: 输入的memory_size
        :return:
        """
        if memory_size < max_memory_size:
            return True
        else:
            print(f'The memory size {memory_size} of the pulse excess the range {max_memory_size} of the Acq channel')
            return False

    def __init__(self):
        pass

    @classmethod
    def collection_conditions(cls) -> dict:
        return {'DC': cls.DC_condition, 'AC': cls.AC_condition, 'Fast': cls.Fast_condition, 'Acq': cls.Acq_condition}


class ChannelType:
    DC = 'DC'
    AC = 'AC'
    Fast = 'Fast'
    Acq = 'Acq'
    Bias = 'DC+AC'
    collection = [DC, AC, Fast, Acq]


class Channel:
    # Todo：将Channel同qcodes的Channel联系起来或者添加parameter
    """
    Channel class 用于元组仪器的channel连接。
    类属性condition是一个函数，用于判断输入的pulse是否满足条件
    """

    def __init__(self,
                 channel_name: str,
                 channel_type: str,
                 ID: int,
                 group: int,
                 Input: bool = True,
                 **kwargs
                 ):
        """
        :param channel_type:通道类型, 可选值为ChannelType中的值
        :param ID:通道id
        :param group:通道所属的组别，例如，对于DC类型的通道而言，group 1 代表开关盒的第一组通道
        :param Input:是否为输入通道, True 为输入，反之为False，默认为True
        :param kwargs: 通道的条件参数，例如，
        对于DC类型的通道而言，需要配置high和low两个参数；
        对于AC类型的通道而言，需要配置cut_off参数;
        对于Fast类型的通道而言，需要配置max_power参数；
        对于Acq类型的通道而言，需要配置max_memory_size参数；
        """
        self.channel_name = channel_name
        self.channel_type = channel_type
        self.group = group
        self.id = ID
        self.input = Input

        for k, v in kwargs.items():
            if k in self.config_limitation:
                setattr(self, k, v)

        self.condition = (
            partial(self.config_condition(),
                    getattr(self, self.config_limitation[0]),
                    getattr(self, self.config_limitation[1])
                    if len(self.config_limitation) == 2
                    else getattr(self, self.config_limitation[0])))

    def __repr__(self):
        output_str = f"{self.channel_name} (group={self.group}, id={self.id}, type={self.channel_type})"
        if self.input:
            output_str += ' input'
        else:
            output_str += ' output'

        return output_str

    def __str__(self):
        output_str = f"{self.channel_name} (group={self.group}, id={self.id}, type={self.channel_type})"
        if self.input:
            output_str += ' input'
        else:
            output_str += ' output'

        return output_str

    def __hash__(self):
        return hash(self.channel_name)

    def __eq__(self, other):
        return self.channel_name == other.channel_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def config_condition(self):
        """
        根据channel类型来返回condition函数

        :return: 返回condition函数句柄
        """

        return ConditionType.collection_conditions()[self.channel_type]

    @property
    def config_limitation(self):
        """
        对于DC类型的通道而言，需要配置high和low两个参数；
        对于AC类型的通道而言，需要配置cut_off参数；
        对于Fast类型的通道而言，需要配置max_power参数
        对于Acq类型的通道而言，需要配置max_memory_size参数
        :return:
        """
        return ConditionType.limitations[self.channel_type]


class InstrumentChannels:
    """ 代表一个仪器，包含所需要的channel信息，以及仪器的名称。
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.channels = []

    def add_channel(self, channel_name: str, channel_type: str, channel_num: int, group, Input, **kwargs):
        """
        添加一个channel
        :param channel_name: 通道名字为仪器名字加上通道名字，例如，仪器名字为chip1，通道名字为Gate1，则通道名字为chip1.Gate1
        :param channel_num: 通道数
        :param channel_type: 通道类型, 可选值为ChannelType中的值
        :param group: 通道所属的组别，例如，对于DC类型的通道而言，group 1 代表开关盒的第一组通道
        :param Input: 是否为输入通道
        :param kwargs: 通道的条件参数，例如，
        对于DC类型的通道而言，需要配置high和low两个参数；
        对于AC类型的通道而言，需要配置cut_off参数;
        对于Fast类型的通道而言，需要配置max_power参数；
        对于Acq类型的通道而言，需要配置max_memory_size参数；
        :return:
        """
        channel_name = self.name + '.' + channel_name
        cha = Channel(channel_name, channel_type, channel_num, group, Input, **kwargs)
        if not self._is_same_channel(cha):
            self.channels.append(cha)
        else:
            print(f'The channel {cha} already exists!')

    def add_channels(self, channel_dict: dict, group: int, channel_type: str = ChannelType.DC, Input: bool = True, **kwargs):
        """

        :param channel_dict: channel 字典，key为channel_name, value为channel id
        :param group: 通道所属的组别，例如，对于DC类型的通道而言，group 1 代表开关盒的第一组通道
        :param channel_type: channel 类型
        :param Input: 是否为输入通道
        :param kwargs: 通道的条件参数，例如，
        对于DC类型的通道而言，需要配置high和low两个参数；
        对于AC类型的通道而言，需要配置cut_off参数;
        对于Fast类型的通道而言，需要配置max_power参数；
        对于Acq类型的通道而言，需要配置max_memory_size参数；
        :return: None
        """
        for k, v in channel_dict.items():
            self.add_channel(channel_name=k, channel_num=v, channel_type=channel_type, group=group, Input=Input, **kwargs)

    def _is_same_channel(self, cha) -> bool:
        """
        判断channel是否已经存在，如果存在则返回True，反之返回False
        :param cha: 判断对象
        :return: bool
        """
        for ch in self.channels:
            if cha == ch:
                return True
        return False


class ACQTask:
    """ 代表一个采集任务，包含了采集的参数，采集的方法，采集的数据。"""
    __slots__ = 'task', 'read', '__dict__'

    def __init__(self, acq_name: str, acq_channels: str, sample_rate: float, memory_size: int):
        self.acq = acq_name
        self.channels = acq_channels
        self.sr = sample_rate
        self.memsize = memory_size
        self._acq_controller = {'art': self.art, 'm2p': self.m2p}

    def __enter__(self):
        self.task, self.read = self._acq_controller[self.acq]()
        return self

    @classmethod
    def get_acq(cls, acq_name):
        return getattr(cls, acq_name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def art(self):
        task = artdaq.Task()
        task.ai_channels.add_ai_voltage_chan(self.channels)
        task.timing.cfg_samp_clk_timing(self.sr,
                                        sample_mode=AcquisitionType.CONTINUOUS,
                                        samps_per_chan=int(self.memsize))
        return task, partial(task.read,
                             number_of_samples_per_channel=self.memsize)

    @staticmethod
    def m2p():
        return dummyget

    def param_configure(self, acq_name: str, acq_channels: str, sample_rate: float, memory_size: int):
        """
        用于配置采集的参数
        :param acq_name: 采集卡名字
        :param acq_channels: 采集的通道
        :param sample_rate: 采样率
        :param memory_size: 寄存器大小
        :return:
        """
        self.acq = acq_name
        self.channels = acq_channels
        self.sr = sample_rate
        self.memsize = memory_size

    def close(self):
        self.task.close()


def dummyset(voltage):
    return voltage


def dummyget():
    return gauss(10, 5)


if __name__ == '__main__':
    # chip = InstrumentChannels('chip1')
    # chip.add_channels({'Gate1': 1, 'Gate2': 2}, group=1, channel_type=ChannelType.DC, Input=False)
    # print(chip.channels)
    print(ConditionType.collection_conditions)
    print(ConditionType.collection_conditions()['AC'](1, 2))
    channel = Channel('Gate1', ChannelType.DC, 1, 1, Input=False, high=1, low=0)
    print(channel)
    print(channel.condition(0.5))
