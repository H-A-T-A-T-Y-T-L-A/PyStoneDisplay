from typing import Iterable, MutableMapping, Optional, Union, Type, TYPE_CHECKING
from enum import Enum
import json

if TYPE_CHECKING:
    from . import StoneWidget

# types of values allowed in a command
CommandPrimitiveValue = Union[str, int, float, bool, Enum]
CommandValue = Union[CommandPrimitiveValue, Iterable[CommandPrimitiveValue]]

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
        """
        Generate new command object instance. Values can then be inserted into the command

        Returns:
            StoneCommand: Instance of a command object with its type information filled in, without values.
        """
        return StoneCommand(self.cmd_code, self.cmd_type)

class StoneWidgetCommandType(StoneCommandType):
    """
    Object describing commands to the STONE HMI display relating to specific widgets.
    """

    def __init__(self, cmd_code: str, widget_type: Type['StoneWidget']) -> None:
        """
        Initialize a widget STONE command type.

        Args:
            cmd_code (str): Specific command code according to STONE docs.
            widget_type (Type[StoneWidget]): Type of widget that this command type is related to.
                Not necessarily the assigned widget instance.
        """
        super().__init__(cmd_code, widget_type.type_name)
        self.widget_type = widget_type
        self.widget:Optional['StoneWidget'] = None

    def for_widget(self, widget:'StoneWidget') -> 'StoneWidgetCommandType':
        """
        Get a copy of the command type object, with a STONE widget assigned to it.

        Args:
            widget (StoneWidget): Reference to the widget which is to be assigned to the command.

        Returns:
            StoneWidgetCommandType: A new instenace of the command type, containing the same command type info,
                but also a reference to the widget its assigned to.
        """
        result = self.copy()
        result.widget = widget
        return result

    def copy(self) -> 'StoneWidgetCommandType':
        """
        Create a copy of the StoneWidgetCommandType.

        Returns:
            StoneWidgetCommandType: A new copy of the original command type, with all the same contents.
        """
        result = StoneWidgetCommandType(self.cmd_code, self.widget_type)
        result.widget = self.widget
        return result

    def new(self) -> 'StoneCommand':
        """
        Generate new command object instance. Values can then be inserted into the command

        Raises:
            ValueError: In case a widget reference, which is allways required for widget commands, was not assigned fist.

        Returns:
            StoneCommand: A new command object instance.
        """
        if self.widget is None:
            raise ValueError('Cannot create a Stone widget command if the widget reference is not set')
        return StoneWidgetCommand(self.cmd_code, self.cmd_type, self.widget)

class StoneCommand:

    def __init__(self, cmd_code:str, cmd_type:str = 'system') -> None:
        self.cmd_code = cmd_code
        self.cmd_type = cmd_type
        self.cmd_items = {}

    def __setitem__(self, key:str, value:CommandValue) -> None:
        if isinstance(value, Enum):
            value = value.value
        self.cmd_items[key] = value

    @property
    def body(self) -> MutableMapping[str, str]:
        return {
            'cmd_code': self.cmd_code,
            'type': self.cmd_type,
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
            'widget': self.widget.instance_name,
        }

class StoneWidgetResponse:
    ...