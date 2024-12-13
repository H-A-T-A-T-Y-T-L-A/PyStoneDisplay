from typing import Iterable, MutableMapping, Optional, Union, TypeVar, Type, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from . import StoneWidget

# types of values allowed in a command
CommandValue = Union[str, int, float, bool]

class StoneCommandType:
    """
    Object describing basic commands to the STONE HMI display.
    """

    def __init__(self, cmd_code:str, cmd_type:str = 'system') -> None:
        """
        Initialize a generic STONE command type.

        Args:
            cmd_code (str): Specific command code according to STONE docs.
            cmd_type (str, optional): String for the type of command according to STONE docs. Defaults to 'system'.
        """
        self.cmd_code = cmd_code
        self.cmd_type = cmd_type

    def new(self) -> 'StoneCommand':
        return StoneCommand(self.cmd_code, self.cmd_type)

class StoneWidgetCommandType(StoneCommandType):

    def __init__(self, cmd_code: str, widget_type: Type['StoneWidget']) -> None:
        super().__init__(cmd_code, widget_type.type_name)
        self.widget_type = widget_type
        self.widget:Optional['StoneWidget'] = None

    def for_widget(self, widget:'StoneWidget') -> 'StoneWidgetCommandType':
        result = self.copy()
        result.widget = widget
        return result

    def copy(self) -> 'StoneWidgetCommandType':
        result = StoneWidgetCommandType(self.cmd_code, self.widget_type)
        result.widget = self.widget
        return result

    def new(self) -> 'StoneCommand':
        if self.widget is None:
            raise ValueError('Cannot create a Stone widget command if the widget reference is not set')
        return StoneWidgetCommand(self.cmd_code, self.cmd_type, self.widget)

class StoneCommand:

    def __init__(self, cmd_code:str, cmd_type:str) -> None:
        self.cmd_code = cmd_code
        self.cmd_type = cmd_type
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

    def __init__(self, cmd_code:str, cmd_type:str, widget:'StoneWidget') -> None:
        super().__init__(cmd_code, cmd_type)
        self.widget = widget

    @property
    def body(self) -> MutableMapping[str, str]:
        return {
            **super().body,
            '"widget"':f'"{self.widget.instance_name}"',
        }

class StoneWidgetResponse:
    raise NotImplemented