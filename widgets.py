from qtpy.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton, QMessageBox, QVBoxLayout
from qtpy.QtCore import Qt, Signal, QSize, QTimer, Slot, QUrl
from qtpy.QtGui import QMouseEvent, QPainter, QPen, QColor
from qtpy.QtMultimedia import QSoundEffect

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
        self.warning_text = "Are you sure you want to unlock?"
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

    def set_color(self, color: str) -> None:
        """
        Sets the color of the widget
        """
        self.setStyleSheet(f"background-color: {color};")

    def set_rgb(self, rgb):
        """
        Sets the color of the widget in (r, g, b)
        """
        color_str = rgb_to_hex(rgb)
        self.setStyleSheet(f"background-color: #{color_str};")


class AnimationWidget(QFrame):
    clicked = Signal()

    def __init__(self, sfx: QSoundEffect, title: str = "Animation"):
        super().__init__()

        self.sfx = sfx

        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumWidth(160)

        self.root_layout = QVBoxLayout()
        self.setLayout(self.root_layout)

        self.icon = QLabel()

        if title == "Single Color":
            self.icon.setPixmap(_qta.icon("mdi6.moon-full", color="#FFEE58").pixmap(72, 72))
        elif title == "Rainbow":
            self.icon.setPixmap(_qta.icon("ph.rainbow", color="#FFEE58").pixmap(72, 72))
        elif title == "Colorloop":
            self.icon.setPixmap(_qta.icon("mdi6.refresh", color="#FFEE58").pixmap(72, 72))
        elif title == "Fire":
            self.icon.setPixmap(_qta.icon("mdi6.fire", color="#FFEE58").pixmap(72, 72))
        elif title == "Magic":
            self.icon.setPixmap(
                _qta.icon("mdi6.magic-staff", color="#FFEE58").pixmap(72, 72)
            )
        elif title == "Colored Lights":
            self.icon.setPixmap(
                _qta.icon("mdi6.string-lights", color="#FFEE58").pixmap(72, 72)
            )
        elif title == "Flash":
            self.icon.setPixmap(_qta.icon("mdi6.flash", color="#FFEE58").pixmap(72, 72))
        elif title == "Fade":
            self.icon.setPixmap(_qta.icon("mdi6.transition", color="#FFEE58").pixmap(72, 72))
        elif title == "Wipe":
            self.icon.setPixmap(
                _qta.icon("mdi6.chevron-double-right", color="#FFEE58").pixmap(72, 72)
            )
        elif title == "Firework":
            self.icon.setPixmap(
                _qta.icon("mdi6.firework", color="#FFEE58").pixmap(72, 72)
            )
        elif title == "Glitter Rainbow":
            self.icon.setPixmap(_qta.icon("mdi6.auto-mode", color="#FFEE58").pixmap(72, 72))
        else:
            self.icon.setPixmap(_qta.icon("mdi6.auto-fix", color="#FFEE58").pixmap(72, 72))

        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.addWidget(self.icon)

        self.title = QLabel(title)
        self.title.setObjectName("h4")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.addWidget(self.title)

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        self.sfx.setVolume(1)  # Set volume (0.0 to 1.0)
        self.sfx.play()
        print("here")
