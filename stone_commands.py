from typing import Iterable, MutableMapping, Optional, Union, TypeVar, Type, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from . import StoneWidget

CommandValue = Union[str, int, float, bool]

class StoneCommandType:

    def __init__(self, cmd_type:str, cmd_code:str) -> None:
        self.cmd_code = cmd_code
        self.cmd_type = cmd_type

    def new(self) -> 'StoneCommand':
        return StoneCommand(self.cmd_type, self.cmd_code)

class StoneWidgetCommandType(StoneCommandType):

    def __init__(self, widget_type: Type['StoneWidget'], cmd_code: str) -> None:
        super().__init__(widget_type.type_name, cmd_code)
        self.widget_type = widget_type
        self.widget:Optional['StoneWidget'] = None

    def for_widget(self, widget:'StoneWidget') -> 'StoneWidgetCommandType':
        result = self.copy()
        result.widget = widget
        return result

    def copy(self) -> 'StoneWidgetCommandType':
        result = StoneWidgetCommandType(self.widget_type, self.cmd_code)
        result.widget = self.widget
        return result

    def new(self) -> 'StoneCommand':
        if self.widget is None:
            raise ValueError('Cannot create a Stone widget command if the widget reference is not set')
        return StoneWidgetCommand(self.widget, self.cmd_type, self.cmd_code)

class StoneCommand:

    def __init__(self, cmd_type:str, cmd_code:str) -> None:
        self.cmd_type = cmd_type
        self.cmd_code = cmd_code
        self.cmd_items = {}

    def __setitem__(self, key:str, value:CommandValue) -> None:
        key = f'"{key}"'
        if isinstance(value, str):
            value = f'"{value}"'
        self.cmd_items[key] = value

    @property
    def body(self) -> MutableMapping[str, str]:
        return {
            '"cmd_code"':f'"{self.cmd_code}"',
            '"type"':f'"{self.cmd_type}"',
        }

    @property
    def serialized(self) -> str:
        body = json.dumps({
            **self.body,
            **self.cmd_items
        })
        result = f'ST<{body}>ET'
        return result

    def __repr__(self) -> str:
        return self.serialized

class StoneWidgetCommand(StoneCommand):

    def __init__(self, widget:'StoneWidget', cmd_type:str, cmd_code:str) -> None:
        super().__init__(cmd_type, cmd_code)
        self.widget = widget

    @property
    def body(self) -> MutableMapping[str, str]:
        return {
            **super().body,
            '"widget"':f'"{self.widget.instance_name}"',
        }

class StoneWidgetResponse:
    raise NotImplemented