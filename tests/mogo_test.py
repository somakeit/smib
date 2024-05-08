from datetime import datetime
from typing import TypeVar

import tzlocal
from mogo import connect, Model, Field

uri = "mongodb://root:example@localhost:27017/"

# Connect to MongoDB
connect("smib_plugins", uri=uri, tz_aware=True)


class SpaceState(Model):
    open: bool | None = Field[bool](default=None)
    last_updated: datetime | None = Field[datetime](default=datetime.utcnow())

    def set_open(self):
        self.open = True
        self.save()

    def set_closed(self):
        self.open = False
        self.save()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name != "last_updated":
            self.last_updated = datetime.utcnow()


def get_single_document(cls):
    single = cls.find_one() or cls()
    single.save()
    return single


# state = SpaceState.find_one() or SpaceState().save()

state = get_single_document(SpaceState)
print(state.last_updated)

# state.set_open()
# state.set_closed()
