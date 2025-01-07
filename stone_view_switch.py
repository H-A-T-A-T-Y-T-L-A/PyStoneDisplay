from typing import Optional
from . import StoneWidget, StoneWidgetCommandType

# this widget is purely virtual, does not exist on the display
# only as an abstraction of multiple overlayed widgets
class StoneViewSwitch(StoneWidget):

    def __init__(self, name:str, parent:Optional[StoneWidget] = None) -> None:
        super().__init__(name, parent)
        self._index = 0

    def add_page(self, name:str) -> StoneWidget:
        return StoneWidget(name, self)

    @property
    def current_index(self) -> int:
        return self._index

    @current_index.setter
    def current_index(self, value:int) -> None:
        if value >= len(self.children):
            raise IndexError(f'Index "{value}" outside of allowed range <0, {len(self.children) - 1}>')
        self._index = value
        self.refresh_views()

    @property
    def current_view(self) -> StoneWidget:
        return self.children[self.current_index]

    @property
    def current_name(self) -> str:
        return self.current_view.name

    @current_name.setter
    def current_name(self, value:str) -> None:
        for i, name in enumerate(view.name for view in self.children):
            if name == value:
                self.current_index = i

    def refresh_views(self) -> None:
        for view in self.children:
            view.visible = view is self.current_view