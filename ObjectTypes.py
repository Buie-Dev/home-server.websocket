from typing import List, Optional, TypedDict


class Subzone(TypedDict):
    id: int
    state: int


class IrrigationState(TypedDict):
    id: int
    state: int
    subzones: Optional[List[Subzone]]


CurrentState = Optional[List[IrrigationState]]


class IrrigationMessage(TypedDict):
    zone: int
    duration: int
    subzones: Optional[List[Subzone]]


class PriorityQueueItem(TypedDict):
    id: str
    duration: float
    zone: int
    priority: int
    subzones: Optional[List[Subzone]]


PriorityQueue = Optional[List[PriorityQueueItem]]
