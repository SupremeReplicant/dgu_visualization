import pyvista as pv
from typing import List

class BaseWindow:
    def __init__(self, groups: List[pv.PolyData], group_names: List[str]):
        self.groups = groups
        self.group_names = group_names

    def show(self) -> None:
        pass
