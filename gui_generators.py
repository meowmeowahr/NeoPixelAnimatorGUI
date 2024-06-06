from typing import Callable, Any

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QLineEdit
from qtpy.QtCore import Qt

from qtawesome import icon

def generate_animation_config_unavailable() -> QWidget:
    anim_widget = QWidget()

    anim_layout = QVBoxLayout()
    anim_widget.setLayout(anim_layout)

    anim_layout.addStretch()

    unknown_anim_icon = QLabel()
    unknown_anim_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    unknown_anim_icon.setPixmap(
        icon("mdi6.alert-circle", color="#FDD835").pixmap(128, 128)
    )
    anim_layout.addWidget(unknown_anim_icon)

    anim_label = QLabel("This animation does not have any settings")
    anim_label.setObjectName("h1")
    anim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    anim_layout.addWidget(anim_label)

    anim_layout.addStretch()

    return anim_widget

def generate_topic_config_row(
        grid: QGridLayout,
        vpos: int,
        name: str,
        setter: Callable[[str], Any],
        getter: Callable[[], str],
        default: str | None = None,
):
    label = QLabel(name)
    label.setObjectName("config_label")

    control = QLineEdit()
    if default:
        control.setPlaceholderText(default)
    control.setText(getter())
    control.textChanged.connect(setter)

    grid.addWidget(label, vpos, 0)
    grid.addWidget(control, vpos, 1)

    return label, control
