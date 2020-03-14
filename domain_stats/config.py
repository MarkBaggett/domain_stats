from collections import UserDict
import yaml

class Config(UserDict):

    def __init__(self, filename=""):
        super().__init__()
        self.filename = filename
        self.load_config(filename)

    def load_config(self, filename = None):
        filename = filename or self.filename
        with open(filename) as fh:
            self.data = yaml.safe_load(fh.read())

    def save_config(self, filename = None):
        filename = filename or self.filename
        with open(filename, 'w') as fp:
            yaml.dump(self.data, fp, default_flow_style=False)
        