from instrument_interfaces.interfaces import Interface


class ChipInterface(Interface):
    """
    代表一个芯片的接口，包含芯片的所有通道
    """

    def __init__(self,
                 name: str,
                 channel_dicts: list = None,
                 inst=None
                 ):
        """
        :param name: 芯片的名字
        :param inst:
        :param channel_dicts: 一个列表，包含所有的通道；元素给是一个字典，包含通道的信息，格式为
        {'channel_name': '通道名',
        'channel_num': 通道ID,
        'channel_type': 通道类型,
        'group': 通道所属的组别，例如，对于DC类型的通道而言，group 1 代表开关盒的第一组通道,
        'Input': 是否为输入通道,
        'kwargs': 通道的条件参数，
        例如，对于DC类型的通道而言，需要配置high和low两个参数；
        对于AC类型的通道而言，需要配置cut_off参数;
        对于Fast类型的通道而言，需要配置max_power参数；
        对于Acq类型的通道而言，需要配置max_memory_size参数；}
        """
        super().__init__(name, inst)
        if channel_dicts is None:
            channel_dicts = []

        for ch in channel_dicts:
            self.add_channel(**ch)
