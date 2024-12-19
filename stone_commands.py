from typing import Deque, Iterator, Iterable, Tuple, Callable, MutableSequence, MutableMapping, Optional, Union, Type, TYPE_CHECKING
from enum import Enum
from collections import deque
import json

if TYPE_CHECKING:
    from . import StoneWidget

# types of values allowed in a command
CommandPrimitiveValue = Union[str, int, float, bool, Enum]
CommandValue = Union[CommandPrimitiveValue, Iterable[CommandPrimitiveValue]]
message_start = 'ST<'
message_end = '>ET'

#!#########################!#
#!         COMMAND         !#
#!#########################!#
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
        result = f'{message_start}{body}{message_end}'
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

#!##########################!#
#!         RESPONSE         !#
#!##########################!#

class StoneResponseBuffer:

    def __init__(self) -> None:
        self.buffer:Deque[int] = deque()
        self.buffering = False
        self.queue:Deque[bytes] = deque()

    def push(self, data:bytes) -> None:
        for byte in data:
            self.process_byte(byte)

    def pop(self) -> Optional[bytes]:
        if len(self.queue) > 0:
            return self.queue.popleft()
        return None

    @property
    def empty(self) -> bool:
        return len(self.queue) == 0

    @property
    def buffered_str(self) -> str:
        return ''.join(chr(byte) for byte in self.buffer)

    def process_byte(self, byte:int) -> None:
        self.buffer.append(byte)
        if self.buffering and self.buffered_str.endswith(message_end):
            self.queue.append(bytes(self.buffer)[:-len(message_end)])
            self.buffering = False
        if self.buffered_str.endswith(message_start):
            self.buffer.clear()
            self.buffering = True

class StoneResponseType:

    existing_types:MutableMapping[int, 'StoneResponseType'] = {}

    def __init__(
        self,
        cmd_code:int,
        data_parser:Callable[[bytes], MutableMapping[str, object]],
    ) -> None:
        self.cmd_code = cmd_code
        self.parser = data_parser

        # register response type
        if self.cmd_code in self.existing_types:
            raise KeyError(f'Cannot create two response type objects with the same command code ({self.cmd_code})')
        self.existing_types[self.cmd_code] = self

    @staticmethod
    def decode(raw:bytes) -> Optional['StoneResponse']:
        cmd_code = int.from_bytes(raw[0:2], 'big')
        cmd_len = int.from_bytes(raw[2:4], 'big')
        raw_data = raw[4:]
        if len(raw_data) != cmd_len:
            raise ValueError(f'True length of data ({len(raw_data)}) did not match the defined length ({cmd_len})')
        try:
            response_type = StoneResponseType.existing_types[cmd_code]
            return response_type.new(raw_data)
        except KeyError:
            return None

    def new(self, raw_data:bytes) -> 'StoneResponse':
        return StoneResponse(self.cmd_code, self.parser(raw_data))

class StoneWidgetResponseType(StoneResponseType):

    @staticmethod
    def parse_widget_name(raw:bytes) -> str:
        widget_name, *_ = raw.decode('ascii').split(' ')
        return widget_name

    def __init__(
        self,
        cmd_code:int,
        data_parser:Callable[[bytes], MutableMapping[str, object]],
        widget_name_parser:Callable[[bytes], str] = parse_widget_name,
    ) -> None:
        super().__init__(cmd_code, data_parser)
        self.widget_name_parser = widget_name_parser

    def new(self, raw_data: bytes) -> 'StoneResponse':
        return StoneWidgetResponse(self.cmd_code, self.parser(raw_data), self.widget_name_parser(raw_data))

class StoneResponse:

    def __init__(
        self,
        cmd_code:int,
        cmd_data:MutableMapping[str, object],
    ) -> None:
        self.cmd_code = cmd_code
        self.cmd_data = cmd_data

    def __getitem__(self, key:str) -> object:
        return self.cmd_data[key]

class StoneWidgetResponse(StoneResponse):

    def __init__(
        self,
        cmd_code:int,
        cmd_data:MutableMapping[str, object],
        widget_name:str,
    ) -> None:
        super().__init__(cmd_code, cmd_data)
        self.widget_name = widget_name