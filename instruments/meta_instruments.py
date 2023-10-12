from qcodes import instrument
from qcodes.utils import validators as val


class Chip(instrument):
    """ 代表一个在稀释制冷机里面的工作芯片，该仪器只作为连接节点的终点或者起点。
    """
    def __init__(self, name:str, channels:list, **kwargs)->None:
        super().__init__(name, **kwargs)
        self.add_parameter(name='channels',
                           set_cmd=None,
                           initial_value=channels,
                           vals=val.Anything())


class ACQTask:
    def __init__(self, acq_name: str):
        self.acq = acq_name
        self._acq_controller = {'art': self.art, 'm2p': self.m2p}

    def __enter__(self):
        self._acq_controller[self.acq]()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def art():
        print('art action')

    @staticmethod
    def m2p():
        print('m2p action')

    def close(self):
        print('close')