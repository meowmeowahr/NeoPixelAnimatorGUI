from qtpy.QtWidgets import QFrame, QLabel, QHBoxLayout
from qtpy.QtCore import Qt

from enum import Enum


class Serverity(Enum):
    SEVERE = 0
    WARN = 1


class WarningBar(QFrame):
    def __init__(self, text="", closeable=False, severity=Serverity.WARN) -> None:
        super(WarningBar, self).__init__()

        self.closeable: bool = closeable

        self.setFrameShape(QFrame.Shape.Box)
        if severity == Serverity.SEVERE:
            self.setStyleSheet("background-color: #ef5350;")
        elif severity == Serverity.WARN:
            self.setStyleSheet("background-color: #ffc107;")
        self.setMinimumHeight(48)

        self._layout = QHBoxLayout()
        self.setLayout(self._layout)

        self._text = QLabel(text)
        # self.__text.setStyleSheet("font-weight: bold;")
        self._text.setObjectName("warning_bar_text")
        self._text.setProperty(
            "severity", "warn" if severity == Serverity.WARN else "severe"
        )
        self._text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._text)

        self.setFixedHeight(self.minimumSizeHint().height())

    def mousePressEvent(self, QMouseEvent):
        if self.closeable:
            self.setVisible(False)


def rgb_to_hex(rgb):
    return "%02x%02x%02x" % tuple(rgb)


class ColorBlock(QFrame):
    """
    A simple widget ot show a single color
    """

    def __init__(self) -> None:
        super(ColorBlock, self).__init__()

        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumWidth(64)
        self.setMinimumHeight(64)

        self.setMaximumSize(128, 128)

    def setColor(self, color: str) -> None:
        """
        Sets the color of the widget
        """
        self.setStyleSheet(f"background-color: {color};")

    def setRGB(self, rgb):
        """
        Sets the color of the widget in (r, g, b)
        """
        color_str = rgb_to_hex(rgb)
        self.setStyleSheet(f"background-color: #{color_str};")
