from asyncio import Future, Task
from typing import TypeVar

Report = TypeVar("Report", Task, Future)
