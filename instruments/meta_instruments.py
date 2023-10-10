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

