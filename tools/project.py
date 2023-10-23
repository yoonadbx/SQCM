import os
from tools.constants import File_path
from tools.logger import Logger
import numpy as np
import h5py
import sys


path = File_path()
project_path = path()


class Project:
    def __init__(self,
                 sample_name: str,
                 temperature: str,
                 tester: str,
                 start_id: int = 0,
                 station=None,
                 instruments: dict = None
                 ):
        self.sample_name = sample_name
        self.temperature = temperature
        self.tester = tester
        self.station = station
        self.instruments = instruments
        self.start_id = start_id
        self.manager = DataManager(path, self.start_id)
        self.logger = Logger(self.sample_name, self.temperature, self.tester, path())
        self.constants = {}


class DataManager:
    def __init__(self, data_path: File_path, run_id: int = 0):
        self.path = data_path
        self.date_path = data_path()  # e.g. 'D:/Data/2023-09-19/'
        self.date = path.date
        self.id = run_id
        self.data_keys = {"scan": ['scan/scan_range_x', 'scan/scan_range_y'],
                          'meas': 'meas/measurement'}
        self.data_cache = 0

    def count_hdf5_files(self):
        """
        获取当前日期目录下所有文件名
        过滤出以 '.h5' 结尾的文件名
        :return: hdf5文件数量
        """
        file_names = os.listdir(self.date_path)
        h5_file_names = [file_name for file_name in file_names if file_name.endswith('.h5')]
        return len(h5_file_names)

    def update_run_id(self):
        if self.path.update_date_dir():
            self.id = 0
            self.date_path = self.path()
            self.date = self.path.date
        else:
            self.id += 1

    @property
    def create_hdf5_file(self):
        file_name = self.date_path + f'{self.id}.hdf5'
        return file_name

    def progress_bar(self, length, idx, idz, current, idy=None):
        scale = 40
        unit_ = {'pA': 1e12, 'nA': 1e9, 'muA': 1e6, 'mA': 1e3, 'A': 1e0}
        print(
            "\rStart experimental run with id:{ID} idy:{idy} idz:{idz} idx:{idx} --- {current:.4f} nA [{done}{"
            "padding}]{percent:.1f}%".format(
                ID=self.id,
                idy=idy,
                idz=idz,
                idx=idx,
                current=current * 1e9,
                done="#" * int((idx + 1) / length * scale),
                padding=" " * (scale - int((idx + 1) / length * scale)),
                percent=(idx + 1) / length * 100
            ),
            end='',
            flush=True)

    def dataset_keys_exist(self, types: str, file: h5py.File) -> bool:
        if self.data_keys[types] in file.keys():
            return True
        else:
            return False

    def save_cache(self, data, unit: str = 'MB', threshold: int = 50):
        scale = {'B': 1, 'KB': 1024, 'MB': 1048576, 'GB': 1073741824}[unit]
        size = sys.getsizeof(data) // scale
        if size > threshold:
            msg = f'The size of data is larger than {threshold} {unit} and it is failed to save into a cache'
            print(msg)
            return msg
        self.data_cache = data
        return 'Save a cache successfully'
