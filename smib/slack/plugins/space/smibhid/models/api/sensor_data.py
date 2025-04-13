from pydantic import BaseModel, RootModel


class SensorData(RootModel):
    root: dict[str, float | int]

class ModuleData(RootModel):
    root: dict[str, SensorData]

class SensorLog(BaseModel):
    timestamp: int
    human_timestamp: str
    data: ModuleData


class SensorLogs(BaseModel):
    logs: list[SensorLog]

    def __iter__(self):
        yield from self.logs