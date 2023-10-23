from typing import List
from tools.project import Project
from instruments.meta_instruments import ACQTask
from qcodes.instrument import Parameter
from qcodes.utils.validators import Union
# from tools.logger import Logger
from numpy import ndarray
import numpy as np
import time
from tools.constants import snapshot, get_time
from collections import Iterable
# from visualization import generate_notes
import h5py


def safe(parameter, end_point):
    if isinstance(parameter, Iterable):
        for element in parameter:
            ramp(element, end_point)
    else:
        ramp(parameter, end_point)


def ramp(parameter, end_point, step=0.01):
    if end_point > 50 or step == 0:
        pass
    else:
        start_point = parameter()
        if start_point > end_point:
            step = -step
        interval = np.arange(start_point, end_point, step)
        for val in interval:
            parameter(val)
            time.sleep(0.005)
    parameter(end_point)


def output(parameter, val):
    if isinstance(parameter, Iterable):
        for element in parameter:
            element(val)
    else:
        parameter(val)


def ramp_all_to_zero(station):
    for parameter in station.components.values():
        if parameter.unit != 'V':
            pass
        else:
            try:
                ramp(parameter, 0)
            except:
                pass
    snapshot(station)


class Scan:

    def __init__(self,
                 para_meas: Parameter,
                 para_scan: Union[List[Parameter], Parameter],
                 project: Project,
                 scaler: float,
                 sleep: float = 0.01
                 ):
        """

        :param para_meas: 测量参数，类型为Parameter，支持多个或者一个
        :param para_scan: 扫描参数
        :param scaler: 最后结果为数据同scaler相乘
        :return: None
        """
        self.scaler = scaler
        self.current_unit = self.scaler_parser
        self.manager = project.manager
        self.para_meas, self.para_scan = self.parameter_validate(para_meas, para_scan)
        self._ranges = {"scan_1d": [np.array([0])],
                        "scan_2d": [np.array([0]), np.array([0])]}
        self.logger = project.logger
        self.sleep = sleep
        self.data: ndarray = np.array([[0], [0]])

    @property
    def scaler_parser(self):
        unit = {'pA': 1e12, 'nA': 1e9, 'muA': 1e6, 'mA': 1e3, 'A': 1e0}
        return [k for k, v in unit.items() if v == self.scaler][0]

    @staticmethod
    def parameter_validate(*args):
        args = list(args)
        for idx, x in enumerate(args):
            if type(x) != tuple and type(x) != list:
                args[idx] = (args[idx],)
        args = tuple(args)
        return args

    @staticmethod
    def range_scan_parser(range_scan):
        if isinstance(range_scan, list):
            range_scan = np.array(range_scan)
        return range_scan

    @staticmethod
    def range_scan_dimension(ranges: list):
        if len(ranges) == 1:
            return len(ranges[0]),
        if len(ranges) == 2:
            return len(ranges[0]), len(ranges[1])

    def set_range_1d(self, scan_range: Union[list, ndarray]):
        range_scan = self.range_scan_parser(scan_range)
        if np.ndim(range_scan) == 1:
            self._ranges['scan_1d'][0] = range_scan
        else:
            raise IndexError('Only one-dimensional data is accepted!')

    def set_range_2d(self, scan_x_range: Union[list, ndarray], scan_y_range: Union[list, ndarray]):
        range_scan_x = self.range_scan_parser(scan_x_range)
        range_scan_y = self.range_scan_parser(scan_y_range)
        if np.ndim(range_scan_x) * np.ndim(range_scan_y) == 1:
            self._ranges['scan_2d'][0] = range_scan_x
            self._ranges['scan_2d'][1] = range_scan_y
        else:
            raise IndexError('Only one-dimensional data is accepted!')

    def scan_1d(self, scan_x: int):
        # Todo：将scan_x同chip的channel联系起来
        """
        :param scan_x: 选定扫描参数
        :return:
        """
        range_1d, scan_x_para, data_file = self.scan_prepare(scan_type='scan_1d', scan_para_list=[scan_x])

        with h5py.File(data_file, 'a') as file:

            dataset = self.scan_dataset(file, range_1d)

            start_time = self.scan_start(scan_x_para, range_1d)

            self.scan_action(range_1d, scan_x_para, dataset)

            end_time = self.scan_end(scan_x_para)

    def scan_prepare(self, scan_type: str, scan_para_list: list) -> (list, Parameter, str):
        ranges = self._ranges[scan_type]
        scan_para = [self.para_scan[para] for para in scan_para_list]
        if len(ranges) == len(scan_para):
            self.data = np.zeros((len(self.para_meas),) + self.range_scan_dimension(ranges))
        else:
            raise ValueError('scan_para_list is out of range and it does not match the scan range.')
        self.manager.update_run_id()
        data_file = self.manager.create_hdf5_file
        return ranges, scan_para, data_file

    def scan_dataset(self, file, ranges):
        try:
            for num in range(len(ranges)):
                file.create_dataset(self.manager.data_keys['scan'][num], data=ranges[num])
            dataset = file.create_dataset(self.manager.data_keys['meas'], shape=np.shape(self.data))
        except ValueError:
            # Todo: 加入到logs里面
            print(f'The dataset is already created with id {self.manager.id}!')
            dataset = file[self.manager.data_keys['meas']]
        return dataset

    def scan_start(self, scan_para: list, ranges: list):
        start_time = get_time()
        for num, para in enumerate(scan_para):
            safe(para, ranges[num][0])
            start_msg = f"Scan {para.name} on {len(scan_para)}d with the result of {self.para_meas[0].name} of which the run id is {self.manager.id} at {start_time}\n"
            self.logger.write(start_msg)
        return start_time

    def scan_action(self, ranges: list, scan_para_list: list, dataset):
        if len(ranges) == 1:
            self.scan_action_1d(ranges, scan_para_list, dataset)
        elif len(ranges) == 2:
            self.scan_action_2d(ranges, scan_para_list, dataset)
        else:
            raise ValueError('The dimension of scan ranges excesses two !')

    def scan_action_1d(self, ranges, scan_para, dataset):
        with ACQTask(acq_name='art',
                     acq_channels='Dev1/ai4',
                     sample_rate=1e4,
                     memory_size=1000) as daq:
            for idx, vx in enumerate(ranges[0]):
                output(scan_para[0], vx)
                time.sleep(self.sleep)
                for idz, vz in enumerate(self.para_meas):
                    raw_data = daq.read() / self.scaler
                    self.data[idz, idx] = np.average(raw_data)
                    self.manager.progress_bar(current=self.data[idz, idx],
                                              idx=idx,
                                              idz=idz,
                                              length=len(ranges[0]))

                dataset[:, idx] = self.data[:, idx]

    def scan_action_2d(self, ranges, scan_para, dataset):
        with ACQTask(acq_name='art',
                     acq_channels='Dev1/ai4',
                     sample_rate=1e4,
                     memory_size=1000) as daq:
            for idy, vy in enumerate(ranges[1]):
                safe(scan_para[0], ranges[0][0])
                output(scan_para[1], vy)
                for idx, vx in enumerate(ranges[0]):
                    output(scan_para[0], vx)
                    time.sleep(self.sleep)
                    for idz, vz in enumerate(self.para_meas):
                        raw_data = daq.read() / self.scaler
                        self.data[idz, idx, idy] = np.average(raw_data)
                        self.manager.progress_bar(current=self.data[idz, idx, idy],
                                                  idy=idy,
                                                  idx=idx,
                                                  idz=idz,
                                                  length=len(ranges[0]))

                dataset[:, :, idy] = self.data[:, :, idy]

    def scan_end(self, scan_para: list):
        end_time = get_time()
        for num, para in enumerate(scan_para):
            safe(para, 0)
            end_msg = f'Scan {para.name} stops at {end_time}\n' + '-' * 20 + "\n"
            self.logger.write(end_msg)
        self.manager.save_cache(self.data)
        return end_time

    def scan_2d(self, scan_x: int, scan_y: int):

        range_2d, scan_xy_para, data_file = self.scan_prepare(scan_type='scan_2d', scan_para_list=[scan_x, scan_y])

        with h5py.File(data_file, 'a') as file:
            dataset = self.scan_dataset(file, range_2d)

            start_time = self.scan_start(scan_xy_para, range_2d)

            self.scan_action(range_2d, scan_xy_para, dataset)

            end_time = self.scan_end(scan_xy_para)


