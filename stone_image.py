from typing import Optional
from enum import Enum
from . import StoneWidget, StoneWidgetCommandType

class StoneImage(StoneWidget):

    type_name = 'image'

    class DrawType(Enum):
        DEFAULT = 0
        CENTER = 1
        ICON = 2
        STRETCH = 3
        SCALE = 4
        SHRINK = 5
        WIDTH_SCALE = 6
        HEIGHT_SCALE = 7
        TILE = 8
        TILE_HORIZONTAL = 9
        TILE_VERTICAL = 10
        TILE_VERTICAL_REVERSED = 11

    def __init__(self, name: str, parent:Optional[StoneWidget] = None) -> None:
        super().__init__(name, parent)

        self._image = ''
        self._set_image = ''
        self.set_image = StoneWidgetCommandType('set_image', StoneImage)
        self._draw_type = StoneImage.DrawType.DEFAULT
        self.set_draw_type = StoneWidgetCommandType('set_draw_type', StoneImage)

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, value:str) -> None:
        self._set_image = value
        if self.is_displayed:
            self.invalidate()

    def invalidate(self) -> None:
        super().invalidate()
        if self._image != self._set_image:
            self._image = self._set_image
            self.push_command(self.set_image, image = self._image)

    @property
    def draw_type(self) -> DrawType:
        return self._draw_type

    @draw_type.setter
    def draw_type(self, value:DrawType) -> None:
        self._draw_type = value
        self.push_command(self.set_draw_type, draw_type = self._draw_type)