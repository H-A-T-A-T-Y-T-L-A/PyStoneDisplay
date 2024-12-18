from typing import (
    Deque,
    Tuple,
    MutableSequence,
    MutableMapping,
    Iterable,
    Optional,
    Union,
    TypeVar,
    Type,
    TYPE_CHECKING
)
from collections import deque
from datetime import datetime, timedelta
import serial

if TYPE_CHECKING:
    from . import (
        StoneWidget,
        StoneWindow,
        StoneCommand,
        StoneCommandType,
        StoneResponseMatcher,
        StoneResponseType,
    )

class StoneDisplay:

    def __init__(self) -> None:
        from . import StoneWindow
        # children
        self._home_window = StoneWindow('home_page')
        self.windows:MutableSequence[StoneWindow] = [ self.home_window ]

        # serial port config
        self.port = ''
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.serial_timeout:Optional[float] = None

        # response handling
        self.response_buffer = StoneResponseMatcher()
        self.home_window.add_response_handler(self.sys_hello_response, self._set_connected)

        # system commands
        self.set_buzzer = StoneCommandType('set_buzzer')
        self._brightness = 100
        self.set_brightness = StoneCommandType('set_brightness')
        self.sys_hello = StoneCommandType('sys_hello')

        # status
        self._connected = False
        self.connection_test_timeout_time:Optional[datetime] = None

    sys_hello_response = StoneResponseType(0x0001, lambda data: {'connected': data == b'\x01'})

    def config_serial(
        self,
        port:Optional[str] = None,
        baudrate:Optional[int] = None,
        bytesize:Optional[int] = None,
        parity:Optional[str] = None,
        stopbits:Optional[int] = None,
        serial_timeout:Optional[float] = None,
    ):
        if port is not None: self.port = port
        if baudrate is not None: self.baudrate = baudrate
        if bytesize is not None: self.bytesize = bytesize
        if parity is not None: self.parity = parity
        if stopbits is not None: self.stopbits = stopbits
        if serial_timeout is not None: self.serial_timeout = serial_timeout

    @property
    def home_window(self) -> 'StoneWindow':
        return self._home_window

    @property
    def connected(self) -> bool:
        return self._connected

    def _set_connected(self, connected:bool) -> None:
        self._connected = connected

    @property
    def all_widgets(self) -> Iterable['StoneWidget']:
        widget_queue:Deque['StoneWidget'] = deque(self.windows)
        while len(widget_queue) > 0:
            next_widget = widget_queue.pop()
            widget_queue.extendleft(next_widget.children)
            yield next_widget

    def gather_commands(self) -> Iterable['StoneCommand']:
        for widget in self.all_widgets:
            while widget.has_commands:
                yield widget.pop_command()

    def add_window(self, name:str) -> 'StoneWindow':
        from . import StoneWindow
        new_window = StoneWindow(name)
        return new_window

    @property
    def serial(self) -> serial.Serial:
        return serial.Serial(
            self.port,
            self.baudrate,
            self.bytesize,
            self.parity,
            self.stopbits,
            self.serial_timeout,
        )

    def write_commands(self) -> None:
        with self.serial as ser:
            for command in self.gather_commands():
                packet = command.serialized.encode('ASCII')
                ser.write(packet)

    def read_commands(self) -> None:
        from . import StoneResponseType, StoneWidgetResponse
        with self.serial as ser:
            read_result = ser.read_all()
            if read_result:
                self.response_buffer.push(read_result)
        for packet in self.response_buffer:
            response = StoneResponseType.decode(packet)
            if isinstance(response, StoneWidgetResponse):
                self.find_by_name(response.widget_name).handle_response(response)
            else:
                self.home_window.handle_response(response)

    def find_by_name(self, key:str) -> 'StoneWidget':
        for widget in self.all_widgets:
            if widget.instance_name == key:
                return widget
        raise KeyError(f'Widget with name "{key}" was not found on the display')

    T = TypeVar('T', bound = 'StoneWidget')
    def __getitem__(self, key:Tuple[str, Type[T]]) -> T:
        widget_name, widget_type = key
        widget = self.find_by_name(widget_name)
        if isinstance(widget, widget_type):
            return widget
        raise KeyError(f'Widget of type "{widget_type.__name__}" with name "{key}" was not found on the display')

    def beep(self, time = 100) -> None:
        self.home_window.push_command(self.set_buzzer, time = time)

    def conn_test(self, timeout_s:float = 5.) -> None:
        self.home_window.push_command(self.sys_hello)

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value:int) -> None:
        if value > 100 or value < 0:
            raise ValueError(f'Cannot set brightness level outside of interval <0, 100> (tried value {value})')
        self.home_window.push_command(self.set_brightness, brightness = value)