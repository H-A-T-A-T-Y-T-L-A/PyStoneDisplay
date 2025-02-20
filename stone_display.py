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
        StoneResponseType,
    )

class StoneDisplay:

    def __init__(self) -> None:
        from . import StoneWindow, StoneCommandType, StoneResponseType, StoneResponseBuffer
        #! children
        self._home_window = StoneWindow('home_page')
        self.windows:MutableSequence[StoneWindow] = [ self.home_window ]

        #! serial port config
        self.port = ''
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.serial_timeout = .0
        self.serial:Optional[serial.Serial] = None

        #! response handling
        self.response_buffer = StoneResponseBuffer()

        # ping (hello) response
        if not StoneDisplay.sys_hello_response: 
            StoneDisplay.sys_hello_response = StoneResponseType(0x0001, lambda data: {'connected': data == b'\x01'})
        self.home_window.add_response_handler(StoneDisplay.sys_hello_response, self._set_connected)
        self._connected = False
        self.ping_timeout_time:Optional[datetime] = None

        #! system commands
        self.set_buzzer = StoneCommandType('set_buzzer')
        self._brightness = 100
        self.set_brightness = StoneCommandType('set_brightness')
        self.sys_hello = StoneCommandType('sys_hello')
        self.sys_reboot = StoneCommandType('sys_reboot')

    # response types should be class variables, to be shared between instances,
    # but to avoid import conflicts, lazy loading is prefered
    # (create the instance in the init function, but only the first time)
    sys_hello_response:Optional['StoneResponseType'] = None

    def config_serial(
        self,
        port:Optional[str] = None,
        baudrate:Optional[int] = None,
        bytesize:Optional[int] = None,
        parity:Optional[str] = None,
        stopbits:Optional[int] = None,
        timeout:Optional[float] = None,
    ):
        if port is not None: self.port = port
        if baudrate is not None: self.baudrate = baudrate
        if bytesize is not None: self.bytesize = bytesize
        if parity is not None: self.parity = parity
        if stopbits is not None: self.stopbits = stopbits
        if timeout is not None: self.serial_timeout = timeout
        if self.serial:
            self.serial.close()
        self.serial = serial.Serial(
            self.port,
            self.baudrate,
            self.bytesize,
            self.parity,
            self.stopbits,
            self.serial_timeout,
        )

    def reboot(self) -> None:
        self.home_window.push_command(self.sys_reboot)

    @property
    def home_window(self) -> 'StoneWindow':
        return self._home_window

    @property
    def connected(self) -> bool:
        # to make sure that old information is not returned,
        # and that timeout is applied even if ping is not called again
        if self._is_timed_out:
            self._set_connected(False)
        # return current state
        return self._connected

    @property
    def _is_timed_out(self) -> bool:
        try:
            return self.ping_timeout_time is not None and datetime.now() >= self.ping_timeout_time
        except:
            return False

    def _set_connected(self, connected:bool) -> None:
        self.ping_timeout_time = None
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
        self.windows.append(new_window)
        return new_window

    def write_commands(self) -> None:
        if not self.serial:
            return
        if not self.serial.is_open:
            self.serial.open()
        for command in self.gather_commands():
            packet = command.serialized.encode('UTF-8')
            self.serial.write(packet)

    def read_responses(self) -> None:
        from . import StoneResponseType, StoneWidgetResponse, StoneResponse
        if not self.serial:
            return
        if not self.serial.is_open:
            self.serial.open()
        read_result = self.serial.read_all()
        if read_result:
            self.response_buffer.push(read_result)
        while packet := self.response_buffer.pop():
            response = StoneResponseType.decode(packet)
            if isinstance(response, StoneWidgetResponse):
                self.find_by_name(response.widget_name).handle_response(response)
            elif isinstance(response, StoneResponse):
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
        raise KeyError(f'Widget of type "{widget_type.__name__}" with name "{widget_name}" was not found on the display')

    def beep(self, time = 100) -> None:
        self.home_window.push_command(self.set_buzzer, time = time)

    def ping(self, timeout_s:float = 3.) -> None:
        if self.ping_timeout_time is None:
            self.home_window.push_command(self.sys_hello)
            self.ping_timeout_time = datetime.now() + timedelta(seconds = timeout_s)
        # to allow another ping immediately if the current one times out
        elif self._is_timed_out:
            self._set_connected(False)

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value:int) -> None:
        if value > 100 or value < 0:
            raise ValueError(f'Cannot set brightness level outside of interval <0, 100> (tried value {value})')
        self._brightness = value
        self.home_window.push_command(self.set_brightness, brightness = self._brightness)
