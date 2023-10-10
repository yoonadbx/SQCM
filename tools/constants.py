import os
from datetime import datetime
import numpy as np


class File_path:
    def __init__(self):
        self.data_root_path = 'D:/Data/'
        self.logger_root_path = "D:/Logger/"
        self.root_path = [self.data_root_path, self.logger_root_path]
        self.date = get_date()
        self.date_path = self.create_date_dir()
        self.is_existing(self.root_path)

    def create_date_dir(self):
        dir_name = []
        for path in self.root_path:
            dir_name.append(path + self.date + '/')
        self.is_existing(dir_name)
        return dir_name

    def update_date_dir(self) -> bool:
        """
        注意所有的日期文件都会被更新
        :return: 布尔值，表示是否更新
        """
        date = get_date()
        if date != self.date:
            self.date = date
            self.date_path = self.create_date_dir()
            return True
        else:
            return False

    @staticmethod
    def is_existing(path: list = None):
        for path in path:
            if not os.path.exists(path):
                os.makedirs(path)
                print(f'{path} is created successfully')
            # print('All the paths are prepared well! ')


def get_time():
    now = datetime.now()
    time = now.strftime('%H-%M-%S')
    return time


def get_date():
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    return date


def snapshot(station):
    for parameter in station.components.values():
        try:
            name = parameter.name
            unit = parameter.unit
            val = parameter()
            if type(val) == np.ndarray or unit == "A":
                val = np.average(val)
            value = "%.4g" % val
            print("     :", value, end='')
            print(unit, end='')
            print("\r" + name)
        except:
            pass


def generate_text(station, tup1=None, tup2=None):
    text = ''
    para_dict = station.components.copy()
    try:
        if tup1:
            for parameter in tup1:
                del para_dict[parameter.name]
        if tup2:
            for parameter in tup2:
                del para_dict[parameter.name]
    except:
        pass

    for parameter in para_dict.values():
        # del para of 0
        try:
            if parameter.settable:
                value = np.average(parameter())
                if value == 0 or value == -1e-6:
                    continue
                unit = parameter.unit
                text += parameter.name + " = " + "%.4g " % value + unit + "\n"
        except:
            pass
    return text


