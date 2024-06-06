from qtpy.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton, QMessageBox
from qtpy.QtCore import Qt, Signal, Slot, QSize, QTimer
from qtpy.QtGui import QMouseEvent, QPainter, QPen, QColor

from enum import Enum
import qtawesome as _qta


class Severity(Enum):
    SEVERE = 0
    WARN = 1


class WarningBar(QFrame):
    def __init__(self, text="", closeable=False, severity=Severity.WARN) -> None:
        super(WarningBar, self).__init__()

        self.closeable: bool = closeable

        self.setFrameShape(QFrame.Shape.Box)
        if severity == Severity.SEVERE:
            self.setStyleSheet("background-color: #ef5350;")
        elif severity == Severity.WARN:
            self.setStyleSheet("background-color: #ffc107;")
        self.setMinimumHeight(48)

        self._layout = QHBoxLayout()
        self.setLayout(self._layout)

        self._text = QLabel(text)
        # self.__text.setStyleSheet("font-weight: bold;")
        self._text.setObjectName("warning_bar_text")
        self._text.setProperty(
            "severity", "warn" if severity == Severity.WARN else "severe"
        )
        self._text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._text)

        self.setFixedHeight(self.minimumSizeHint().height())

    def mousePressEvent(self, ev: QMouseEvent):
        if self.closeable:
            self.setVisible(False)


class LockButton(QPushButton):
    locked = Signal()
    unlocked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.warning_text = None
        self.checked = False

        self.setFlat(True)
        self.setIconSize(QSize(48, 48))
        self.setIcon(_qta.icon('mdi6.lock', color="#F44336"))
        self.setToolTip("Click to unlock")
        self.clicked.connect(self.on_clicked)

        self._flashing = False
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._update_flash)

    def set_warning_text(self, text: str):
        self.warning_text = text

    def on_clicked(self):
        self.checked = not self.checked
        if self.checked:
            reply = QMessageBox.warning(
                self,
                "Warning",
                self.warning_text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.setIcon(_qta.icon('mdi6.lock-open', color="#4CAF50"))
                self.setToolTip("Click to lock")
                self.unlocked.emit()
            else:
                self.setChecked(False)
        else:
            self.setIcon(_qta.icon('mdi6.lock', color="#F44336"))
            self.setToolTip("Click to unlock")
            self.locked.emit()

    def flash_outline(self, duration=2000, interval=250):
        self._flashing = True
        self._flash_timer.start(interval)
        QTimer.singleShot(duration, self.stop_flash)

    def stop_flash(self):
        self._flashing = False
        self._flash_timer.stop()
        self.update()  # Ensure the outline is cleared

    def _update_flash(self):
        self._flashing = not self._flashing
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._flashing:
            painter = QPainter(self)
            painter.setRenderHints(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor("#FFC107"), 4)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 2, 2)


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
