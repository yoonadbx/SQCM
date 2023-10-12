import os
from tools.constants import File_path
from Test.test_for_scan import dummyget, dummyset
import numpy as np
import h5py
import sys
# from qcodes import initialise_or_create_database_at

"载入当天日期的文件夹路径，用来放置数据"


class DataManager:
    def __init__(self, path=File_path(), run_id: int = 0):
        self.path = path
        self.date_path = path()  # e.g. 'D:/Data/2023-09-19/'
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
        file_name = self.date_path+f'{self.id}.hdf5'
        return file_name

    def progress_bar(self, length, idx, idz, current, idy=None):
        scale = 40
        print(
            "\rStart experimental run with id:{ID} idy:{idy} idz:{idz} idx:{idx} --- {current:.4f} nA [{done}{padding}]{percent:.1f}%".format(
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

    def save_cache(self, data, unit:str = 'MB', threshold:int = 50):
        scale = {'B': 1, 'KB': 1024, 'MB': 1048576, 'GB': 1073741824}[unit]
        size = sys.getsizeof(data) // scale
        if size > threshold:
            msg = f'The size of data is larger than {threshold} {unit} and it is failed to save into a cache'
            print(msg)
            return msg
        self.data_cache = data
        return 'Save a cache successfully'


class ACQTask:
    __slots__ = 'read', '__dict__'

    def __init__(self, acq_name: str):
        self.acq = acq_name
        self._acq_controller = {'art': self.art, 'm2p': self.m2p}

    def __enter__(self):
        self.read = self._acq_controller[self.acq]()
        return self

    @classmethod
    def get_acq(cls, acq_name):
        return getattr(cls, acq_name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def art():
        #         task = artdaq.Task()
        #         task.ai_channels.add_ai_voltage_chan(f"Dev1/ai0:3")
        #         task.timing.cfg_samp_clk_timing(sr, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=int(memsize))
        return dummyget

    @staticmethod
    def m2p():
        return dummyget

    def close(self):
        print('close')







