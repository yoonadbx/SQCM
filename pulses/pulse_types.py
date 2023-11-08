

class Pulse:
    """
    Pulse类，用于描述脉冲的基本信息，包括脉冲的名称，脉冲的id，脉冲的发送端，脉冲的接收端，脉冲的起始时间，脉冲的终止时间，脉冲的持续时间
    """
    def __init__(self,
                 name: str = None,
                 ID: int = None,
                 sender=None,
                 acceptor=None,
                 t_start: float = None,
                 t_stop: float = None,
                 duration: float = None):
        """
        :param name: 脉冲的名称
        :param ID: 脉冲的id
        :param sender: 脉冲的发送端, 格式是仪器名字.通道名字，例如，sp1060.Ch1
        :param acceptor: 脉冲的接收端, 格式是仪器名字.通道名字，例如，chip1.Gate1
        :param t_start: 脉冲的起始时间，单位为s
        :param t_stop: 脉冲的终止时间，单位为s
        :param duration: 脉冲的持续时间，单位为s
        """
        self.name = name
        if ID is None:
            ID = id(self)
        self.id = ID
        self.sender = sender
        self.acceptor = acceptor
        if t_stop is None and t_start is not None and duration is not None:
            self.t_stop = t_start + duration
        elif t_stop is not None and t_start is None and duration is not None:
            self.t_start = t_stop - duration
        elif t_stop is not None and t_start is not None and duration is None:
            self.duration = t_stop - t_start
        else:
            raise ValueError('Either t_stop or t_start and duration must be specified')

    def __repr__(self):
        return self._get_repr()

    def _get_repr(self):
        pulse_info = f'Pulse info\n ' \
                     f'\tpulse class: {self.__class__.__name__}\n ' \
                     f'\tname: {self.name}\n ' \
                     f'\tid: {self.id}\n ' \
                     f'\tsender: {self.sender}\n ' \
                     f'\tacceptor: {self.acceptor}\n ' \
                     f'\tt_start: {self.t_start}\n ' \
                     f'\tt_stop: {self.t_stop}\n ' \
                     f'\tduration: {self.duration}\n'
        return pulse_info

    def snapshot(self):
        print(self._get_repr())

    def __eq__(self, other):
        return self.name == other.name and self.id == other.id

    def __hash__(self):
        return hash((self.name, self.id))

    def __ne__(self, other):
        return not self.__eq__(other)


class DCFixedPulse(Pulse):
    """
    恒定电压值的DC脉冲类，基本信息包括脉冲的名称，脉冲的id，脉冲的发送端，脉冲的接收端，脉冲的起始时间，脉冲的终止时间，脉冲的持续时间，脉冲的幅度
    """
    def __init__(self,
                 name: str = None,
                 amplitude: float = None,
                 sender=None,
                 acceptor=None,
                 **kwargs):
        super().__init__(name=name, sender=sender, acceptor=acceptor, **kwargs)
        self.amplitude = amplitude

    def _get_repr(self):
        pulse_info = f'Pulse info\n ' \
                     f'\tpulse class: {self.__class__.__name__}\n ' \
                     f'\tname: {self.name}\n ' \
                     f'\tid: {self.id}\n ' \
                     f'\tsender: {self.sender}\n ' \
                     f'\tacceptor: {self.acceptor}\n ' \
                     f'\tamplitude: {self.amplitude}\n'
        return pulse_info

    def __repr__(self):
        return self._get_repr()

    def snapshot(self):
        print(self._get_repr())


class DCRampPulse(Pulse):
    """
    扫描给定电压范围的DC脉冲类，基本信息包括脉冲的名称，脉冲的id，脉冲的发送端，脉冲的接收端，脉冲的起始时间，脉冲的终止时间，脉冲的持续时间，脉冲的起始幅度，脉冲的终止幅度，脉冲的斜率
    """
    def __init__(self,
                 name: str,
                 amplitude_start: float,
                 amplitude_stop: float,
                 sender=None,
                 acceptor=None,
                 ramp_rate: float = None,
                 **kwargs):
        """
        :param name: 脉冲的名称
        :param amplitude_start: 振幅的起始值
        :param amplitude_stop: 振幅的终止值
        :param sender: 脉冲的发送端, 格式是仪器名字.通道名字，例如，sp1060.Ch1
        :param acceptor: 脉冲的接收端, 格式是仪器名字.通道名字，例如，chip1.Gate1
        :param ramp_rate: 脉冲的斜率，单位为V/s
        :param kwargs:
        """
        super().__init__(name=name, sender=sender, acceptor=acceptor, **kwargs)
        self.amplitude_start = amplitude_start
        self.amplitude_stop = amplitude_stop
        self.ramp_rate = ramp_rate

    def _get_repr(self):
        pulse_info = f'Pulse info\n ' \
                     f'\tpulse class: {self.__class__.__name__}\n ' \
                     f'\tname: {self.name}\n ' \
                     f'\tid: {self.id}\n ' \
                     f'\tsender: {self.sender}\n ' \
                     f'\tacceptor: {self.acceptor.get()}\n ' \
                     f'\tamplitude start: {self.amplitude_start}\n ' \
                     f'\tamplitude_stop:{self.amplitude_stop}'
        return pulse_info

    def __repr__(self):
        return self._get_repr()

    def snapshot(self):
        print(self._get_repr())


class DCPulse(Pulse):
    """
    用于AWG读写的DC脉冲类，基本信息包括脉冲的名称，脉冲的id，脉冲的发送端，脉冲的接收端，脉冲的起始时间，脉冲的终止时间，脉冲的持续时间，脉冲的幅度
    """
    def __init__(self,
                 name: str = None,
                 amplitude: float = None,
                 sender=None,
                 acceptor=None,
                 **kwargs):
        super().__init__(name=name, sender=sender, acceptor=acceptor, **kwargs)
        self.amplitude = amplitude

    def _get_repr(self):
        pulse_info = f'Pulse info\n ' \
                     f'\tpulse class: {self.__class__.__name__}\n ' \
                     f'\tname: {self.name}\n ' \
                     f'\tid: {self.id}\n ' \
                     f'\tsender: {self.sender}\n ' \
                     f'\tacceptor: {self.acceptor}\n ' \
                     f'\tamplitude: {self.amplitude}\n'
        return pulse_info

    def __repr__(self):
        return self._get_repr()

    def snapshot(self):
        print(self._get_repr())
