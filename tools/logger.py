from tools.constants import get_date, get_time


# Todo:规定一下logging的输出格式
class Logger:
    def __init__(self,
                 sample_name: str,
                 mkor4k: str,
                 tester: str,
                 path: str):
        self.logging_path = path
        self.project_name = sample_name + mkor4k + 'test'
        self.sample_name = sample_name
        self.tester = tester
        self.create_time = get_time()
        self.date = get_date()
        self.full_path = None
        self.create()

    def create(self):
        self.full_path = self.logging_path + self.project_name + '.txt'
        msg = f'The logger of {self.project_name} is created at {self.create_time} {self.date}\n Sample name: {self.sample_name}\n tester: {self.tester}\n'
        with open(self.full_path, 'a') as file:
            file.write(msg)

    def write(self, msg: str):
        with open(self.full_path, 'a') as file:
            file.write(msg)
