from qcodes.instrument.parameter import Parameter
from qcodes.utils.validators import Strings, Numbers, Bool, Optional, Anything
from pulses.pulse_types import Pulse


class PulseAssemblingRequirements:
    def __init__(self,
                 connection=None,
                 order: list = None,
                 cycles: int = None,
                 alignment: Anything = None):
        self.reqs = {'connection': connection,
                     'order': order,
                     'cycles': cycles,
                     'alignment': alignment}


class PulseSequence:
    def __init__(self,
                 name: str,
                 pulse_elements: Optional[list[Pulse]],
                 sequence_start: float = 0,
                 sequence_delay: float = 0,
                 enabled: bool = True):
        self.name = Parameter('name',
                              set_cmd=None,
                              vals=Strings(),
                              initial_value=name)
        self.enabled = Parameter('enabled',
                                 set_cmd=None,
                                 vals=Bool(),
                                 initial_value=enabled)
        self.sequence_start = Parameter('start',
                                        set_cmd=None,
                                        vals=Numbers(),
                                        initial_value=sequence_start,
                                        unit='s')
        self.sequence_start = Parameter('delay',
                                        set_cmd=None,
                                        vals=Numbers(),
                                        initial_value=sequence_delay,
                                        unit='s')

        self.pulse_elements = pulse_elements
        self.pulse_sequence = {}

    @property
    def sender_sorted(self):
        dict_sorted = {}
        for k, v in enumerate(self.pulse_elements):
            if v.sender.get() in dict_sorted.keys():
                dict_sorted[v.sender.get()].append(k)
            else:
                dict_sorted[v.sender.get()] = [k]
        return dict_sorted

    @property
    def acceptor_sorted(self):
        dict_sorted = {}
        for k, v in enumerate(self.pulse_elements):
            dict_sorted[k] = v.acceptor.get()
        return dict_sorted

    def pulse_assembling(self, requirements: PulseAssemblingRequirements):
        # ToDo: 组装之前需要对传入的要求同pulse和conncetion呼应，然后每一项比对，
        # 全部通过之后核对channel的condition，然后开始

        if requirements.reqs['connection']:
            pass

    def sequence_generator(self):
        # ToDo: 遍历需要的connection,然后用pulse_aseembling对每一个connection组装需要的脉冲，然后返回脉冲序列的属性，
        # 包括脉冲的持续时间，脉冲的形状，脉冲功率，脉冲的触发时间。
        pass


if __name__ == '__main__':
    dc = Pulse(name='dac', sender='DAC', acceptor='okk')
    pulses = [dc]
    pulse_seq = PulseSequence(name='test', pulse_elements=pulses)
    print(pulse_seq.sender_sorted)
    print(pulse_seq.acceptor_sorted)
