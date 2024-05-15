from smib.slack.db import Model, Field


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
