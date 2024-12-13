from typing import Tuple, MutableSequence, MutableMapping, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from . import CommandValue, StoneCommand, StoneWidgetCommandType

class StoneWidget:
    """
    Base class for all STONE display widgets.
    Contains functionality to assemble and enqueue commands, with general shared commands already implemented.
    """

    #! to be set in a subclass, used in commands to identify widget type
    type_name = 'widget'

    def __init__(self, name:str) -> None:
        """
        Instantiate a new widget, with a defined name, that is used to identify it in commands.

        Args:
            name (str): The name of the widget instance, is used in this widgets commands so must match the name in the display.
        """

        from . import StoneWidgetCommandType
        # name of this specific widget instance
        self.instance_name = name
        # "queue" of commands to be sent by the application, only one command per command type is permitted, 
        # to prevent writing the same command multiple times
        self.command_queue:MutableMapping[str, 'StoneCommand'] = {}


        #* general commands
        # enabled
        self._enabled = True
        self.set_enabled = StoneWidgetCommandType(StoneWidget, 'set_enable')
        # visible
        self._visible = True
        self.set_visible = StoneWidgetCommandType(StoneWidget, 'set_visible')
        # x/y coordinates
        self._x = -1
        self._y = -1
        self.set_xy = StoneWidgetCommandType(StoneWidget, 'set_xy')
        # self.get_xy = StoneWidgetCommandType(StoneWidget, 'get_xy')

    def push_command(self, command:'StoneWidgetCommandType', **kwargs:'CommandValue') -> None:
        """
        Push a command object to the send queue, removing any other instance of the same command (with the same name).

        Args:
            command (StoneWidgetCommand): Command object to be added to the queue.
        """
        # create widget command from the widget command type, for this widget instance
        command_obj = command.for_widget(self).new()
        # write kwargs into command object
        for key, value in kwargs.items():
            command_obj[key] = value
        # ensure only one command with the same name can be in the queue
        # this throws away the old command if not yet sent
        self.command_queue[command.cmd_code] = command_obj

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value:bool) -> None:
        self._enabled = value
        self.push_command(self.set_enabled, enable = self._enabled)

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value:bool) -> None:
        self._visible = value
        self.push_command(self.set_visible, visible = self._visible)

    @property
    def xy(self) -> Tuple[int, int]:
        return (self._x, self._y)

    @xy.setter
    def xy(self, value:Tuple[int, int]) -> None:
        self._x, self._y = value
        self.push_command(self.set_xy, x = self._x, y = self._y)

    