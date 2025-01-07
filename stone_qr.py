from typing import Union, Optional
from . import StoneWidget, StoneWidgetCommandType

class StoneQr(StoneWidget):

    type_name = 'qr'

    def __init__(self, name:str, parent:Optional[StoneWidget] = None) -> None:
        super().__init__(name, parent)

        self._text = ''
        self.set_text = StoneWidgetCommandType('set_text', StoneQr)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value:str) -> None:
        self._text = value
        self.push_command(self.set_text, text = self._text)