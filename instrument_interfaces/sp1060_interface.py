from instruments.DAC_SP1060 import DAC_SP1060
from instrument_interfaces.interfaces import Interface
from time import sleep


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
        if channel_num == 24:
            # 通道数为24时，AWG有4个，True代表AWG未被占用
            self.AWGs_state = {'A': True, 'B': True, 'C': True, 'D': True}
        elif channel_num == 12:
            # 通道数为12时，AWG有2个，True代表AWG未被占用
            self.AWGs_state = {'A': True, 'B': True}

    def AWG_assign(self):
        """
        分配AWG给pulse line使用
        :return:
        """
        for key, value in self.AWGs_state.items():
            if value:
                self.AWGs_state[key] = False
                return key
        raise ValueError('AWG is occupied')

    def close(self):
        self.instrument.close()

    def pulse_line_implementation(self, pulse_line: list, ch: str, **kwargs):
        """
        将pulse line转化为仪器的指令
        :param ch: pulse line所属的通道
        :param pulse_line: 输入的pulse line
        :return: 仪器的指令
        """
        awg = self.AWG_assign()
        ch = int(ch[2])
        self.pulse_external_trigger(awg)
        self.clear_wave_memory(awg)
        for pulse_element in pulse_line:
            for pulse in pulse_element[1:-1]*pulse_element[-1]:
                self.offset_generator(pulse)
            self.write_waveform_to_AWG(awg, ch, pulse_element[-1])
            self.add_wave_to_mem(awg)
        sleep(0.2)

    def offset_generator(self, pulse):
        """
        产生offset
        :param pulse: 输入的pulse
        :return:
        """
        # 生成一个新的波形，0代表新建波形，1代表保存波形
        self.instrument.SWG_new_or_save_waveform(0)
        sleep(0.05)
        # 设置波形类型，7代表一个DC电压
        self.instrument.SWG_wavefunction(7)
        sleep(0.05)
        # 设置波形持续时间
        self.instrument.SWG_desired_freq(pulse.duration)
        sleep(0.05)
        # 设置offset
        self.instrument.SWG_dc_offset(pulse.amplitude)
        sleep(0.05)
        # 保存波形
        self.instrument.SWG_apply_wavefunction_to_mem()
        sleep(0.02)

    def pulse_external_trigger(self, AWG: str):
        """
        设置外部触发
        :return:
        """
        # 设置时钟频率，这里设置1kHz
        # Todo: 假定AWG只涉及A和B两个通道，后续根据sp1060的实际情况修改
        self.instrument.AWG_AB_clock_period(1000)
        sleep(0.2)
        # 设置触发模式为外部触发，1代表AWG在收到触发信号的上升沿后，输出波形
        self.instrument.write(f'C AWG-{AWG} TM 1')
        sleep(0.2)
        # 设置触发信号由外部信号触发, 0代表由外部信号触发
        self.instrument.write(f'C AWG-{AWG} AS 0')
        sleep(0.2)

    def clear_wave_memory(self, AWG: str):
        """
        清除仪器的波形内存
        # ToDo: 暂时仅清除A和B的内存，后续根据sp1060的实际情况修改
        :return:
        """
        self.instrument.write(f'C AWG-{AWG} CLR')
        sleep(0.2)

    def add_wave_to_mem(self, AWG: str):
        """
        将波形添加到内存中
        :param AWG: 0代表AWG A, 1代表AWG B
        :return:
        """
        _unit = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        # 给AWG A分配波形内存
        self.instrument.SWG_waveform_mem(_unit[AWG])
        sleep(0.2)
        # 将波形添加到内存中
        self.instrument.SWG_selected_function(2)
        sleep(0.2)
        # DAC 通道线性化
        self.instrument.SWG_linearization_to_DAC(1)
        sleep(0.2)

    def write_waveform_to_AWG(self, AWG: str , ch: int, cycle: int):
        """
        将波形写入AWG
        :param AWG: AWG的代称，例如，A代表AWG A
        :param cycle: 重复次数
        :param ch: 通道数
        :return:
        """
        # 选择AWG 通道
        self.instrument.write(f"C AWG-{AWG} CH {ch}")
        sleep(0.2)
        # 设置重复次数
        self.instrument.write(f"C AWG-{AWG} CS {cycle}")
        # 写入波形到AWG内存中
        self.instrument.write(f"C AWG-{AWG} WRITE")
        sleep(0.2)

