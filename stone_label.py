from typing import Union, Optional
from . import StoneWidget, StoneWidgetCommandType

class StoneLabel(StoneWidget):

    type_name = 'label'

    def __init__(self, name:str, parent:Optional[StoneWidget] = None) -> None:
        super().__init__(name, parent)

        self._text = ''
        self._value = 0.
        self._format = ''
        self.set_text = StoneWidgetCommandType('set_text', StoneLabel)
        self.set_value = StoneWidgetCommandType('set_value', StoneLabel)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value:str) -> None:
        self._text = value
        self._value = 0
        self.push_command(self.set_text, text = self._text)

    @property
    def value(self) -> Union[float, int]:
        return self._value

    @value.setter
    def value(self, value:Union[float, int]) -> None:
        self._value = value
        self._text = ''
        self.push_command(self.set_value, value = self._value, format = self._format)

    @property
    def format(self) -> str:
        return self._format

    @format.setter
    def format(self, value:str) -> None:
        self._format = value
        self.push_command(self.set_value, value = self._value, format = self._format)