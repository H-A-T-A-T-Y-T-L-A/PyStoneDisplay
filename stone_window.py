from typing import Optional
from . import StoneWidget, StoneCommandType, StoneWidgetCommandType

class StoneWindow(StoneWidget):

    type_name = 'window'
    back_win = StoneCommandType('back_win', type_name)

    def __init__(self, name: str, parent:Optional[StoneWidget] = None) -> None:
        super().__init__(name, parent)

        self.open_win = StoneWidgetCommandType('open_win', StoneWidget)
        self.close_win = StoneWidgetCommandType('close_win', StoneWidget)
        self.back_win_to = StoneWidgetCommandType('back_win_to', StoneWidget)

    def open(self) -> None:
        """
        Open the window, even if it is running in the background.
        """
        self.push_command(self.open_win)

    def close(self) -> None:
        """
        Close the window, data is not going to be cached. Use with caution.
        """
        self.push_command(self.close_win)

    def back(self) -> None:
        """
        Close the targeting window caching its data.
        """
        self.push_command(self.back_win)

    def back_to(self) -> None:
        """
        Other opened windows will remain in the background, while this window becomes target.
        """
        self.push_command(self.back_win_to)