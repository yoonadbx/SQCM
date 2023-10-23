from qcodes.instrument import parameter
from qcodes.utils.validators import Numbers, Lists


class Pulse:
    def __init__(self,
                 name: str = None,
                 id: int = None,
                 sender=None,
                 acceptor=None,
                 amplitudes: list = None,
                 frequencies: list = None,
                 t_start: float = None,
                 t_stop: float = None,
                 duration: float = None):
        self.name = name
        self.id = id
        self.sender = parameter.Parameter('sender',
                                          initial_value=sender,
                                          set_cmd=None)
        self.acceptor = parameter.Parameter('acceptor',
                                            initial_value=acceptor,
                                            set_cmd=None)
        self.amplitudes = parameter.Parameter('amplitudes',
                                              initial_value=amplitudes,
                                              vals=Lists(),
                                              set_cmd=None,
                                              docstring="""振幅输入为一个list, 一个元素代表恒定值，两个代表扫描的范围，即[L, H]""")
        self.frequencies = parameter.Parameter('frequencies',
                                               initial_value=frequencies,
                                               vals=Lists(),
                                               set_cmd=None,
                                               docstring="""频率输入为一个list, 一个元素代表恒定值，两个代表扫描的范围，即[L, H]""")
        self.t_start = parameter.Parameter('t_start',
                                           initial_value=t_start,
                                           vals=Numbers(),
                                           set_cmd=None)
        self.t_stop = parameter.Parameter('t_stop',
                                          initial_value=t_stop,
                                          vals=Numbers(),
                                          set_cmd=None)
        self.t_stop = parameter.Parameter('duration',
                                          initial_value=duration,
                                          vals=Numbers(),
                                          set_cmd=None)

    # def __repr__(self):
    #     # Todo：后面增加成snapshot
    #     pulse_info = f'Pulse info\n name: {self.name}\n id: {self.id}\n sender: {self.sender}\n acceptor: {self.acceptor}'
    #     return self._get_repr(pulse_info)

    # def _get_repr(self, pulse_info):
    #     pulse_class = self.__class__.__name__
    #     return f'{pulse_class}({pulse_info})'
    # Todo: 增加判断Pulse是否相同的函数接口


class DCFixedPulse(Pulse):
    def __init__(self,
                 name: str = None,
                 amplitude: float = None,
                 sender=None,
                 acceptor=None,
                 **kwargs):
        super().__init__(name=name, sender=sender, acceptor=acceptor, **kwargs)
        self.amplitude = parameter.Parameter('amplitude',
                                             initial_value=amplitude,
                                             unit='V',
                                             set_cmd=None)

    def _get_repr(self):
        pulse_info = f'Pulse info\n ' \
                     f'\tpulse class: {self.__class__.__name__}\n ' \
                     f'\tname: {self.name}\n ' \
                     f'\tid: {self.id}\n ' \
                     f'\tsender: {self.sender.get()}\n ' \
                     f'\tacceptor: {self.acceptor.get()}\n ' \
                     f'\tamplitude: {self.amplitude.get()}\n'
        return pulse_info

    def __repr__(self):
        return self._get_repr()

    def snapshot(self):
        print(self._get_repr())


class DCRampPulse(Pulse):
    def __init__(self,
                 name: str,
                 amplitude_start: float,
                 amplitude_stop: float,
                 sender=None,
                 acceptor=None,
                 **kwargs):
        super().__init__(name=name, sender=sender, acceptor=acceptor, **kwargs)
        self.amplitude_start = parameter.Parameter('amp_start',
                                                   initial_value=amplitude_start,
                                                   unit='V',
                                                   vals=Numbers())
        self.amplitude_stop = parameter.Parameter('amp_stop',
                                                  initial_value=amplitude_stop,
                                                  unit='V',
                                                  vals=Numbers())

    def _get_repr(self):
        pulse_info = f'Pulse info\n ' \
                     f'\tpulse class: {self.__class__.__name__}\n ' \
                     f'\tname: {self.name}\n ' \
                     f'\tid: {self.id}\n ' \
                     f'\tsender: {self.sender.get()}\n ' \
                     f'\tacceptor: {self.acceptor.get()}\n ' \
                     f'\tamplitude start: {self.amplitude_start.get()}\n ' \
                     f'\tamplitude_stop:{self.amplitude_stop.get()}'
        return pulse_info

    def __repr__(self):
        return self._get_repr()

    def snapshot(self):
        print(self._get_repr())


if __name__ == '__main__':
    dc = DCFixedPulse('la', amplitude=1)
    print(dc)
    dc.snapshot()
