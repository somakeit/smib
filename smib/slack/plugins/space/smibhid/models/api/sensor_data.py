from pydantic import BaseModel, RootModel


class SensorData(RootModel):
    root: dict[str, float | int]

class ModuleData(RootModel):
    root: dict[str, SensorData]

class SensorUnits(RootModel):
    root: dict[str, str]

class ModuleUnits(RootModel):
    root: dict[str, SensorUnits]

class SensorLog(BaseModel):
    timestamp: int
    human_timestamp: str
    data: ModuleData


class SensorLogs(BaseModel):
    readings: list[SensorLog]
    units: ModuleUnits

    def __iter__(self):
        yield from self.readings