from instruments.DAC_SP1060 import DAC_SP1060
from instrument_interfaces.interfaces import Interface


class Sp1060(Interface):
    def __init__(self,
                 address: str = None,
                 name: str = 'sp1060',
                 channel_num: int = 24,
                 **kwargs):
        """
        :param name: sp1060
        :param address: 仪器的IP地址
        :param channel_num: 仪器的通道数，一般为24或者12
        :param kwargs: 仪器的其他参数，例如，仪器的型号，仪器的序列号等
        """
        super().__init__(name)
        self.instrument = DAC_SP1060(name, address, **kwargs)
        for ch in range(channel_num):
            self.add_channel(channel_name=f'Ch{ch+1}',
                             channel_num=ch+1,
                             channel_type='DC',
                             group=1,
                             Input=False,
                             high=1.0,
                             low=-1.0)

    def close(self):
        self.instrument.close()