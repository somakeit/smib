from smib.slack.db import Model, Field, get_plugin_database
from injectable import inject

client = get_plugin_database()


class Space(Model):
    open: bool = Field[bool](default=None)

    @classmethod
    def single(cls):
        return cls.find_one() or cls()

    def set_open(self):
        self.open = True
        self.save()

    def set_closed(self):
        self.open = False
        self.save()
