from pathlib import Path

from .option_record import OptionRecord


class EtasRecord(OptionRecord):
    @property
    def path(self):
        file_option = self.option_pairs['FILE']
        assert file_option is not None
        return Path(file_option)

    @path.setter
    def path(self, value):
        self.set_option('FILE', str(value))
