from typing import Tuple, MutableSequence, MutableMapping, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from . import CommandValue, StoneCommandType, StoneWidgetCommandType, StoneCommand

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

        # name of this specific widget instance
        self.instance_name = name
        # "queue" of commands to be sent by the application, only one command per command type is permitted, 
        # to prevent writing the same command multiple times
        self.command_queue:MutableMapping[str, 'StoneCommand'] = {}


        #* general commands
        # enabled
        self._enabled = True
        self.set_enable = StoneWidgetCommandType('set_enable', StoneWidget)
        # visible
        self._visible = True
        self.set_visible = StoneWidgetCommandType('set_visible', StoneWidget)
        # x/y coordinates
        self._x = -1
        self._y = -1
        self.set_xy = StoneWidgetCommandType('set_xy', StoneWidget)
        # self.get_xy = StoneWidgetCommandType(StoneWidget, 'get_xy')

    def push_command(self, command:Union['StoneCommandType', 'StoneCommand'], **kwargs:'CommandValue') -> None:
        """
        Push a command object to the send queue, removing any other instance of the same command (with the same name).

        Args:
            command (StoneWidgetCommand): Command object to be added to the queue.
        """
        from . import StoneCommandType, StoneWidgetCommandType
        # if the command type is a widget type 
        # create widget command type with a reference to this widget
        if isinstance(command, StoneWidgetCommandType):
            command = command.for_widget(self)

        # in case the command is a type, not an instance,
        # create an instance from the type
        if isinstance(command, StoneCommandType):
            command = command.new()

        # write kwargs into command object
        for key, value in kwargs.items():
            command[key] = value

        # ensure only one command with the same name can be in the queue
        # this throws away the old command if not yet sent
        self.command_queue[command.cmd_code] = command

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value:bool) -> None:
        self._enabled = value
        self.push_command(self.set_enable, enable = self._enabled)

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

    