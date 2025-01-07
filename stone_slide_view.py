from typing import Optional
from . import StoneWidget, StoneWidgetCommandType

class StoneSlideViewPage(StoneWidget):

    def __init__(self, name: str, parent:Optional[StoneWidget] = None) -> None:
        super().__init__(name, parent)

class StoneSlideView(StoneWidget):

    type_name = 'slide_view'

    def __init__(self, name:str, parent:Optional[StoneWidget] = None) -> None:
        super().__init__(name, parent)
        self._index = 0
        self.set_view = StoneWidgetCommandType('set_view', StoneSlideView)
        self._auto_play:int = 0
        self.set_auto_play = StoneWidgetCommandType('set_auto_play', StoneSlideView)

    def add_page(self, name:str) -> StoneSlideViewPage:
        return StoneSlideViewPage(name, self)

    def add_child(self, child: StoneWidget) -> None:
        if not isinstance(child, StoneSlideViewPage):
            raise TypeError(f'{StoneSlideView.__name__} expects children of type {StoneSlideViewPage.__name__}, not {type(child).__name__}')
        return super().add_child(child)

    @property
    def current_index(self) -> int:
        return self._index

    @current_index.setter
    def current_index(self, value:int) -> None:
        if value >= len(self.children):
            raise IndexError(f'Index "{value}" outside of allowed range <0, {len(self.children) - 1}>')
        self._index = value
        self.push_command(self.set_view, index = self._index)

    @property
    def current_page(self) -> StoneSlideViewPage:
        page = self.children[self.current_index]
        if not isinstance(page, StoneSlideViewPage):
            raise TypeError(f'{StoneSlideView.__name__} expects children of type {StoneSlideViewPage.__name__}, not {type(page).__name__}')
        return page

    @property
    def auto_play(self) -> int:
        return self._auto_play

    @auto_play.setter
    def auto_play(self, value:int) -> None:
        self._auto_play = value
        self.push_command(self.set_auto_play, auto_play = value)