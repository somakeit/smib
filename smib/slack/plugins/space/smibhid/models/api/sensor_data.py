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
    units: ModuleUnits


class SensorLogs(BaseModel):
    logs: list[SensorLog]

    def __iter__(self):
        yield from self.logs