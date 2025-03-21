"""
/// NeoPixel Animator GUI ///
DESCRIPTION: Fully featured PyQt GUI for controlling NeoPixelAnimator
LICENSE: GPLv3
"""

import dataclasses
from enum import Enum
from functools import partial
import json
from random import randint
import sys
from loguru import logger
from platform import system

from qtpy.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QScroller,
    QGridLayout,
    QGroupBox,
    QToolButton,
    QLineEdit,
    QSpinBox,
    QRadioButton,
    QCheckBox
)
from qtpy.QtCore import Qt, QSize, QTimer, QUrl
from qtpy.QtGui import QPixmap, QIcon, QFontDatabase, QMouseEvent, QCursor
from qtpy.QtMultimedia import QSoundEffect
from qdarktheme import load_stylesheet
from qtawesome import icon
from qtawesome import dark as qtadark
from qtawesome import light as qtalight

from widgets import WarningBar, ColorBlock, LockButton, AnimationWidget
from gui_generators import generate_animation_config_unavailable, generate_topic_config_row
from palette import PaletteGrid, PALETTES

from animation_data import AnimationArgs
from mqtt import MqttClient
from settings import SettingsManager, CursorSetting

__version__ = "0.2.0"

if system() == "Windows":
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(  # type: ignore
        f"meowmeowahr.npanimator.client.{__version__}"
    )

client_id: str = f"mqtt-animator-{randint(0, 1000)}"

ANIMATION_LIST: dict[str, str] = {
    "Single Color": "SingleColor",
    "Rainbow": "Rainbow",
    "Glitter Rainbow": "GlitterRainbow",
    "Colorloop": "Colorloop",
    "Magic": "Magic",
    "Fire": "Fire",
    "Colored Lights": "ColoredLights",
    "Fade": "Fade",
    "Flash": "Flash",
    "Wipe": "Wipe",
    "Firework": "Firework",
    "Random": "Random",
    "Random Color": "RandomColor",
}

M_CONNECTION_WIDGET_INDEX = 0
M_CONTROL_WIDGET_INDEX = 1
M_ABOUT_PAGE_INDEX = 2
M_SETTINGS_PAGE_INDEX = 3
M_ANIM_CONF_INDEX = 4

A_UNKNOWN_INDEX = 0
A_SINGLE_COLOR_INDEX = 1
A_RAINBOW_INDEX = 2
A_GLITTER_RAINBOW_INDEX = 3
A_COLORLOOP_INDEX = 4
A_MAGIC_INDEX = 5
A_FIRE_INDEX = 6
A_COLORED_LIGHTS_INDEX = 7
A_FADE_INDEX = 8
A_FLASH_INDEX = 9
A_WIPE_INDEX = 10
A_FIREWORK_INDEX = 11
A_RANDOM_INDEX = 12
A_RANDOM_COLOR_INDEX = 13

ANIMATION_CONF_INDEXES: dict[str, int] = {
    "SingleColor": A_SINGLE_COLOR_INDEX,
    "Rainbow": A_RAINBOW_INDEX,
    "GlitterRainbow": A_GLITTER_RAINBOW_INDEX,
    "Colorloop": A_COLORLOOP_INDEX,
    "Magic": A_MAGIC_INDEX,
    "Fire": A_FIRE_INDEX,
    "ColoredLights": A_COLORED_LIGHTS_INDEX,
    "Fade": A_FADE_INDEX,
    "Flash": A_FLASH_INDEX,
    "Wipe": A_WIPE_INDEX,
    "Firework": A_FIREWORK_INDEX,
    "Random": A_RANDOM_INDEX,
    "RandomColor": A_RANDOM_COLOR_INDEX,
}


class PowerStates(Enum):
    """Power on states"""

    OFF = 0
    ON = 1
    UNKNOWN = 2


class BrightnessStates(Enum):
    """Is brightness known?"""

    KNOWN = 0
    UNKNOWN = 1


def hex_to_rgb(hexa: str) -> tuple:
    """Convert hex color string to RGB tuple

    Args:
        hexa (str): Hex color string Ex: "#00ff00"

    Returns:
        tuple: RGB color
    """
    return tuple(int(hexa[i: i + 2], 16) for i in (0, 2, 4))


def dict_to_dataclass(data_dict, dataclass_type):
    # Recursively convert nested dictionaries to dataclasses
    for field in dataclasses.fields(dataclass_type):
        field_name = field.name
        if hasattr(field.type, "__annotations__") and field_name in data_dict:
            data_dict[field_name] = dict_to_dataclass(data_dict[field_name], field.type)

    return dataclass_type(**data_dict)


def map_range(inp: float, in_min: float, in_max: float, out_min: float, out_max: float):
    """Map bounds of input to bounds of output

    Args:
        inp (int): Input value
        in_min (int): Input lower bound
        in_max (int): Input upper bound
        out_min (int): Output lower bound
        out_max (int): Output upper bound

    Returns:
        int: Output value
    """
    return (inp - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class MainWindow(QMainWindow):
    def __init__(self, parent: QApplication):
        super().__init__()

        # Settings Manager
        self.settings = SettingsManager()

        # Theme
        self.set_custom_theming(self.settings.custom_theming)

        # Mqtt Client
        self.client = MqttClient()
        self.client.hostname = self.settings.mqtt_host
        self.client.port = self.settings.mqtt_port

        self.client.connected.connect(self.on_client_connect)
        self.client.messageSignal.connect(self.on_client_message)

        self.connection_attempts = 1

        # Led State
        self.led_powered = PowerStates.UNKNOWN
        self.brightness_value = 0
        self.brightness_known = BrightnessStates.UNKNOWN
        self.animation_args = AnimationArgs()
        self.num_leds = 100

        # SFX
        self.sfx = QSoundEffect()
        self.sfx.setSource(QUrl.fromLocalFile("assets/sounds/click.wav"))
        self.sfx.setVolume(self.settings.sfx_volume)

        self.setWindowTitle("NeoPixel Animator Client")
        self.setWindowIcon(QIcon("assets/icons/icon-128.svg"))

        self.root_widget = QStackedWidget()
        self.setCentralWidget(self.root_widget)

        self.connection_widget = QWidget()
        self.root_widget.insertWidget(M_CONNECTION_WIDGET_INDEX, self.connection_widget)

        # Connection
        self.connection_layout = QVBoxLayout()
        self.connection_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_widget.setLayout(self.connection_layout)

        self.connection_icon = QLabel()
        self.connection_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_icon.setPixmap(QPixmap("assets/mqtt-icon-transparent.svg"))
        self.connection_layout.addWidget(self.connection_icon)

        self.connection_label = QLabel("Connecting to MQTT Broker...")
        self.connection_label.setObjectName("h1")
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_layout.addWidget(self.connection_label)

        self.connection_attempts_label = QLabel(
            f"Connection Attempts: {self.connection_attempts}"
        )
        self.connection_attempts_label.setObjectName("h3")
        self.connection_attempts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_layout.addWidget(self.connection_attempts_label)

        self.connection_settings_button = QPushButton("Access Settings")
        self.connection_settings_button.clicked.connect(self.show_settings)
        self.connection_layout.addWidget(self.connection_settings_button)

        self.connection_timer = QTimer(self)
        self.connection_timer.setInterval(1000)
        self.connection_timer.timeout.connect(self.check_mqtt_connection)
        self.connection_timer.start()
        self.check_mqtt_connection()

        # Control
        self.control_widget = QWidget()
        self.root_widget.insertWidget(M_CONTROL_WIDGET_INDEX, self.control_widget)

        self.control_layout = QVBoxLayout()
        self.control_widget.setLayout(self.control_layout)

        self.control_top_bar = QHBoxLayout()
        self.control_layout.addLayout(self.control_top_bar)

        self.control_title = QLabel(self.settings.app_title)
        self.control_title.setObjectName("h2")
        self.control_title.setFixedWidth(self.control_title.minimumSizeHint().width())

        self.control_power = QPushButton()
        self.control_power.setFlat(True)
        self.control_power.setIcon(icon("mdi6.power", color="#9EA7AA"))
        self.control_power.setIconSize(QSize(72, 72))
        self.control_power.setFixedSize(QSize(72, 72))
        self.control_power.clicked.connect(self.toggle_led_power)
        self.control_power.clicked.connect(self.sfx.play)

        self.control_about = QPushButton()
        self.control_about.setFlat(True)
        self.control_about.setIcon(icon("mdi6.information-slab-circle"))
        self.control_about.setIconSize(QSize(24, 24))
        self.control_about.clicked.connect(self.show_about)
        self.control_about.clicked.connect(self.sfx.play)
        self.control_about.setFixedWidth(self.control_about.minimumSizeHint().height())

        self.control_settings = QPushButton()
        self.control_settings.setFlat(True)
        self.control_settings.setIcon(icon("mdi6.cog"))
        self.control_settings.setIconSize(QSize(24, 24))
        self.control_settings.clicked.connect(self.show_settings)
        self.control_settings.clicked.connect(self.sfx.play)
        self.control_settings.setFixedWidth(
            self.control_settings.minimumSizeHint().height()
        )

        self.control_top_bar.addWidget(self.control_title)
        self.control_top_bar.addStretch()
        self.control_top_bar.addWidget(self.control_power)
        # this is to evenly center the power control
        # gets size of title widget and subtracts width of about and settings buttons
        # accounts for layout spacing and paddings
        # results in a perfectly centered power control
        self.control_top_bar.addSpacing((self.control_title.width() - (
                    self.control_about.width() + self.control_settings.width() + (self.control_top_bar.spacing() * 2))))
        self.control_top_bar.addStretch()
        self.control_top_bar.addWidget(self.control_about)
        self.control_top_bar.addWidget(self.control_settings)

        self.control_brightness_box = QGroupBox("Brightness")
        self.control_layout.addWidget(self.control_brightness_box)

        self.control_brightness_layout = QHBoxLayout()
        self.control_brightness_box.setLayout(self.control_brightness_layout)

        self.control_brightness_warning = QLabel()
        self.control_brightness_warning.setPixmap(
            icon("mdi6.alert", color="#FDD835").pixmap(QSize(24, 24))
        )
        self.control_brightness_warning.setToolTip("Brightness data may be inaccurate")
        self.control_brightness_layout.addWidget(self.control_brightness_warning)

        self.control_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.control_brightness_slider.setObjectName("big_slider")
        self.control_brightness_slider.setRange(1, 255)
        self.control_brightness_slider.valueChanged.connect(self.update_brightness)
        self.control_brightness_layout.addWidget(self.control_brightness_slider)

        self.current_animation = QLabel("Current Animation: Unknown")
        self.current_animation.setObjectName("h4")
        self.current_animation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.control_layout.addWidget(self.current_animation)

        self.animation_layout = QHBoxLayout()
        self.control_layout.addLayout(self.animation_layout)

        self.control_animator_scroll = QScrollArea()
        self.control_animator_scroll.setWidgetResizable(True)
        self.control_animator_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        QScroller.grabGesture(
            self.control_animator_scroll,
            QScroller.ScrollerGestureType.LeftMouseButtonGesture,
        )
        self.animation_layout.addWidget(self.control_animator_scroll)

        self.control_animator_widget = QWidget()
        self.control_animator_scroll.setWidget(self.control_animator_widget)

        self.control_animator_layout = QGridLayout()
        self.control_animator_widget.setLayout(self.control_animator_layout)

        self.control_animation_list = []
        for idx, key in enumerate(ANIMATION_LIST.keys()):
            widget = AnimationWidget(self.sfx, key)
            widget.clicked.connect(partial(self.set_animation, key))
            self.control_animation_list.append(widget)
            self.control_animator_layout.addWidget(widget, idx % 2, idx // 2)

        self.animation_sidebar_frame = QFrame()
        self.animation_sidebar_frame.setFrameShape(QFrame.Shape.Box)
        self.animation_sidebar_frame.setEnabled(False)
        self.animation_layout.addWidget(self.animation_sidebar_frame)

        self.animation_sidebar_layout = QVBoxLayout()
        self.animation_sidebar_frame.setLayout(self.animation_sidebar_layout)

        self.animation_settings = QPushButton()
        self.animation_settings.setIcon(icon("mdi6.tune-vertical-variant"))
        self.animation_settings.setIconSize(QSize(42, 42))
        self.animation_settings.setFixedWidth(
            self.animation_settings.minimumSizeHint().height()
        )
        self.animation_settings.clicked.connect(self.anim_conf)
        self.animation_settings.clicked.connect(self.sfx.play)
        self.animation_settings.setFlat(True)
        self.animation_sidebar_layout.addWidget(self.animation_settings)

        # About
        self.about_widget = QWidget()
        self.root_widget.insertWidget(M_ABOUT_PAGE_INDEX, self.about_widget)

        self.about_layout = QVBoxLayout()
        self.about_widget.setLayout(self.about_layout)

        self.about_top_bar = QHBoxLayout()
        self.about_layout.addLayout(self.about_top_bar)

        self.about_back = QPushButton()
        self.about_back.setFlat(True)
        self.about_back.setIcon(icon("mdi6.arrow-left-box", color="#9EA7AA"))
        self.about_back.setIconSize(QSize(48, 48))
        self.about_back.clicked.connect(
            lambda: self.root_widget.setCurrentIndex(M_CONTROL_WIDGET_INDEX)
        )
        self.about_top_bar.addWidget(self.about_back)

        self.about_top_bar.addStretch()

        self.about_top_title = QLabel("About")
        self.about_top_title.setObjectName("h2")
        self.about_top_bar.addWidget(self.about_top_title)

        self.about_top_bar.addStretch()

        self.about_side_by_side = QHBoxLayout()
        self.about_side_by_side.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.about_layout.addLayout(self.about_side_by_side)

        self.about_icon = QLabel()
        self.about_icon.setPixmap(QPixmap("assets/icons/icon-512.svg"))
        self.about_icon.setScaledContents(True)
        self.about_icon.setFixedSize(QSize(240, 240))
        self.about_side_by_side.addWidget(self.about_icon)

        self.about_right_layout = QVBoxLayout()
        self.about_side_by_side.addLayout(self.about_right_layout)

        self.about_right_layout.addStretch()

        self.about_title = QLabel("NeoPixel Animator Client")
        self.about_title.setObjectName("h0")
        self.about_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.about_right_layout.addWidget(self.about_title)

        self.about_version = QLabel(__version__)
        self.about_version.setObjectName("h1")
        self.about_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.about_right_layout.addWidget(self.about_version)

        self.about_qt_button = QPushButton("About Qt")
        self.about_qt_button.setMaximumWidth(240)
        self.about_qt_button.clicked.connect(parent.aboutQt)
        self.about_right_layout.addWidget(self.about_qt_button)
        self.about_right_layout.setAlignment(
            self.about_qt_button, Qt.AlignmentFlag.AlignCenter
        )

        self.about_right_layout.addStretch()

        # Animation Conf
        self.anim_conf_widget = QWidget()
        self.root_widget.insertWidget(M_ANIM_CONF_INDEX, self.anim_conf_widget)

        self.anim_conf_layout = QVBoxLayout()
        self.anim_conf_widget.setLayout(self.anim_conf_layout)

        self.anim_conf_top_bar = QHBoxLayout()
        self.anim_conf_layout.addLayout(self.anim_conf_top_bar)

        self.anim_conf_back = QPushButton()
        self.anim_conf_back.setFlat(True)
        self.anim_conf_back.setIcon(icon("mdi6.arrow-left-box", color="#9EA7AA"))
        self.anim_conf_back.setIconSize(QSize(48, 48))
        self.anim_conf_back.clicked.connect(
            lambda: self.root_widget.setCurrentIndex(M_CONTROL_WIDGET_INDEX)
        )
        self.anim_conf_top_bar.addWidget(self.anim_conf_back)

        self.anim_conf_top_bar.addStretch()

        self.anim_conf_top_title = QLabel("Effect Settings")
        self.anim_conf_top_title.setObjectName("h2")
        self.anim_conf_top_bar.addWidget(self.anim_conf_top_title)

        self.anim_conf_top_bar.addStretch()

        self.anim_config_stack = QStackedWidget()
        self.anim_conf_layout.addWidget(self.anim_config_stack)

        self.unknown_anim_widget = QWidget()
        self.anim_config_stack.insertWidget(A_UNKNOWN_INDEX, self.unknown_anim_widget)

        self.unknown_anim_layout = QVBoxLayout()
        self.unknown_anim_widget.setLayout(self.unknown_anim_layout)

        self.unknown_anim_layout.addStretch()

        self.unknown_anim_icon = QLabel()
        self.unknown_anim_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unknown_anim_icon.setPixmap(
            icon("mdi6.alert-circle", color="#FDD835").pixmap(128, 128)
        )
        self.unknown_anim_layout.addWidget(self.unknown_anim_icon)

        self.unknown_anim_label = QLabel("Animation Unknown")
        self.unknown_anim_label.setObjectName("h1")
        self.unknown_anim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unknown_anim_layout.addWidget(self.unknown_anim_label)

        self.unknown_anim_layout.addStretch()

        self.anim_single_color_widget = QWidget()
        self.anim_config_stack.insertWidget(
            A_SINGLE_COLOR_INDEX, self.anim_single_color_widget
        )

        self.anim_single_color_layout = QHBoxLayout()
        self.anim_single_color_widget.setLayout(self.anim_single_color_layout)

        self.anim_single_color_palette = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_single_color_palette.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic,
                f'single_color,{{"color": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}",
            )
        )
        self.anim_single_color_layout.addWidget(self.anim_single_color_palette)

        self.anim_single_color_right_layout = QVBoxLayout()
        self.anim_single_color_layout.addLayout(self.anim_single_color_right_layout)

        self.anim_single_color_right_layout.addStretch()

        self.anim_single_color_current_label = QLabel("Current")
        self.anim_single_color_current_label.setObjectName("h2")
        self.anim_single_color_right_layout.addWidget(
            self.anim_single_color_current_label
        )

        self.anim_single_color_current = ColorBlock()
        self.anim_single_color_right_layout.addWidget(self.anim_single_color_current)

        self.anim_single_color_right_layout.addStretch()

        # Rainbow Conf
        self.anim_config_stack.insertWidget(
            A_RAINBOW_INDEX, generate_animation_config_unavailable()
        )

        # Glitter Rainbow Conf

        self.anim_grainbow_widget = QWidget()
        self.anim_config_stack.insertWidget(
            A_GLITTER_RAINBOW_INDEX, self.anim_grainbow_widget
        )

        self.anim_grainbow_layout = QVBoxLayout()
        self.anim_grainbow_widget.setLayout(self.anim_grainbow_layout)

        self.anim_grainbow_layout.addStretch()

        self.anim_grainbow_ratio_label = QLabel("Glitter to Normal Ratio")
        self.anim_grainbow_ratio_label.setObjectName("h3")
        self.anim_grainbow_layout.addWidget(self.anim_grainbow_ratio_label)

        self.anim_grainbow_ratio = QSlider(Qt.Orientation.Horizontal)
        self.anim_grainbow_ratio.setObjectName("big_slider")
        self.anim_grainbow_ratio.setRange(1, 50)
        self.anim_grainbow_ratio.valueChanged.connect(
            lambda: self.publish_and_update_args(
                self.settings.args_topic,
                f'glitter_rainbow,{{"glitter_ratio": {self.anim_grainbow_ratio.value() / 100}}}',
            )
        )
        self.anim_grainbow_ratio.sliderReleased.connect(
            lambda: self.publish_and_update_args(
                self.settings.args_topic,
                f'glitter_rainbow,{{"glitter_ratio": {self.anim_grainbow_ratio.value() / 100}}}',
            )
        )
        self.anim_grainbow_layout.addWidget(self.anim_grainbow_ratio)

        self.anim_grainbow_layout.addStretch()

        # Colorloop Conf
        self.anim_config_stack.insertWidget(
            A_COLORLOOP_INDEX, generate_animation_config_unavailable()
        )

        # Magic Conf
        self.anim_config_stack.insertWidget(
            A_MAGIC_INDEX, generate_animation_config_unavailable()
        )

        # Fire Conf
        self.anim_config_stack.insertWidget(
            A_FIRE_INDEX, generate_animation_config_unavailable()
        )

        # Colored Lights Conf
        self.anim_config_stack.insertWidget(
            A_COLORED_LIGHTS_INDEX, generate_animation_config_unavailable()
        )

        # Fade config
        self.anim_fade_widget = QWidget()
        self.anim_config_stack.insertWidget(A_FADE_INDEX, self.anim_fade_widget)

        self.anim_fade_layout = QHBoxLayout()
        self.anim_fade_widget.setLayout(self.anim_fade_layout)

        self.anim_fade_a_layout = QVBoxLayout()
        self.anim_fade_layout.addLayout(self.anim_fade_a_layout)

        self.anim_fade_palette_a = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_fade_palette_a.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic, f'fade,{{"colora": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}"
            )
        )
        self.anim_fade_a_layout.addWidget(self.anim_fade_palette_a)

        self.anim_fade_a_bottom_layout = QHBoxLayout()
        self.anim_fade_a_layout.addLayout(self.anim_fade_a_bottom_layout)

        self.anim_fade_a_bottom_layout.addStretch()

        self.anim_fade_current_a_label = QLabel("Current")
        self.anim_fade_current_a_label.setObjectName("h2")
        self.anim_fade_a_bottom_layout.addWidget(self.anim_fade_current_a_label)

        self.anim_fade_current_a = ColorBlock()
        self.anim_fade_current_a.setFixedHeight(32)
        self.anim_fade_a_bottom_layout.addWidget(self.anim_fade_current_a)

        self.anim_fade_a_bottom_layout.addStretch()

        self.anim_fade_divider = QFrame()
        self.anim_fade_divider.setFrameShape(QFrame.Shape.VLine)
        self.anim_fade_layout.addWidget(self.anim_fade_divider)

        self.anim_fade_b_layout = QVBoxLayout()
        self.anim_fade_layout.addLayout(self.anim_fade_b_layout)

        self.anim_fade_palette_b = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_fade_palette_b.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic, f'fade,{{"colorb": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}"
            )
        )
        self.anim_fade_b_layout.addWidget(self.anim_fade_palette_b)

        self.anim_fade_b_bottom_layout = QHBoxLayout()
        self.anim_fade_b_layout.addLayout(self.anim_fade_b_bottom_layout)

        self.anim_fade_b_bottom_layout.addStretch()

        self.anim_fade_current_b_label = QLabel("Current")
        self.anim_fade_current_b_label.setObjectName("h2")
        self.anim_fade_b_bottom_layout.addWidget(self.anim_fade_current_b_label)

        self.anim_fade_current_b = ColorBlock()
        self.anim_fade_current_b.setFixedHeight(32)
        self.anim_fade_b_bottom_layout.addWidget(self.anim_fade_current_b)

        self.anim_fade_b_bottom_layout.addStretch()

        # Flash config
        self.anim_flash_widget = QWidget()
        self.anim_config_stack.insertWidget(A_FLASH_INDEX, self.anim_flash_widget)

        self.anim_flash_layout = QHBoxLayout()
        self.anim_flash_widget.setLayout(self.anim_flash_layout)

        self.anim_flash_a_layout = QVBoxLayout()
        self.anim_flash_layout.addLayout(self.anim_flash_a_layout)

        self.anim_flash_palette_a = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_flash_palette_a.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic, f'flash,{{"colora": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}"
            )
        )
        self.anim_flash_a_layout.addWidget(self.anim_flash_palette_a)

        self.anim_flash_a_bottom_layout = QHBoxLayout()
        self.anim_flash_a_layout.addLayout(self.anim_flash_a_bottom_layout)

        self.anim_flash_a_bottom_layout.addStretch()

        self.anim_flash_current_a_label = QLabel("Current")
        self.anim_flash_current_a_label.setObjectName("h2")
        self.anim_flash_a_bottom_layout.addWidget(self.anim_flash_current_a_label)

        self.anim_flash_current_a = ColorBlock()
        self.anim_flash_current_a.setFixedHeight(32)
        self.anim_flash_a_bottom_layout.addWidget(self.anim_flash_current_a)

        self.anim_flash_a_bottom_layout.addStretch()

        self.anim_flash_divider = QFrame()
        self.anim_flash_divider.setFrameShape(QFrame.Shape.VLine)
        self.anim_flash_layout.addWidget(self.anim_flash_divider)

        self.anim_flash_b_layout = QVBoxLayout()
        self.anim_flash_layout.addLayout(self.anim_flash_b_layout)

        self.anim_flash_palette_b = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_flash_palette_b.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic, f'flash,{{"colorb": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}"
            )
        )
        self.anim_flash_b_layout.addWidget(self.anim_flash_palette_b)

        self.anim_flash_b_bottom_layout = QHBoxLayout()
        self.anim_flash_b_layout.addLayout(self.anim_flash_b_bottom_layout)

        self.anim_flash_b_bottom_layout.addStretch()

        self.anim_flash_current_b_label = QLabel("Current")
        self.anim_flash_current_b_label.setObjectName("h2")
        self.anim_flash_b_bottom_layout.addWidget(self.anim_flash_current_b_label)

        self.anim_flash_current_b = ColorBlock()
        self.anim_flash_current_b.setFixedHeight(32)
        self.anim_flash_b_bottom_layout.addWidget(self.anim_flash_current_b)

        self.anim_flash_b_bottom_layout.addStretch()

        self.anim_flash_speed = QSlider()
        self.anim_flash_speed.setObjectName("big_slider")
        self.anim_flash_speed.setRange(3, 50)
        self.anim_flash_speed.valueChanged.connect(
            lambda: self.publish_and_update_args(
                self.settings.args_topic, f'flash,{{"speed": ' f"{self.anim_flash_speed.value()}}}"
            )
        )
        self.anim_flash_speed.sliderReleased.connect(
            lambda: self.publish_and_update_args(
                self.settings.args_topic, f'flash,{{"speed": ' f"{self.anim_flash_speed.value()}}}"
            )
        )
        self.anim_flash_layout.addWidget(self.anim_flash_speed)

        # Wipe config
        self.anim_wipe_widget = QWidget()
        self.anim_config_stack.insertWidget(A_WIPE_INDEX, self.anim_wipe_widget)

        self.anim_wipe_layout = QHBoxLayout()
        self.anim_wipe_widget.setLayout(self.anim_wipe_layout)

        self.anim_wipe_a_layout = QVBoxLayout()
        self.anim_wipe_layout.addLayout(self.anim_wipe_a_layout)

        self.anim_wipe_palette_a = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_wipe_palette_a.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic, f'wipe,{{"colora": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}"
            )
        )
        self.anim_wipe_a_layout.addWidget(self.anim_wipe_palette_a)

        self.anim_wipe_a_bottom_layout = QHBoxLayout()
        self.anim_wipe_a_layout.addLayout(self.anim_wipe_a_bottom_layout)

        self.anim_wipe_a_bottom_layout.addStretch()

        self.anim_wipe_current_a_label = QLabel("Current")
        self.anim_wipe_current_a_label.setObjectName("h2")
        self.anim_wipe_a_bottom_layout.addWidget(self.anim_wipe_current_a_label)

        self.anim_wipe_current_a = ColorBlock()
        self.anim_wipe_current_a.setFixedHeight(32)
        self.anim_wipe_a_bottom_layout.addWidget(self.anim_wipe_current_a)

        self.anim_wipe_a_bottom_layout.addStretch()

        self.anim_wipe_divider = QFrame()
        self.anim_wipe_divider.setFrameShape(QFrame.Shape.VLine)
        self.anim_wipe_layout.addWidget(self.anim_wipe_divider)

        self.anim_wipe_b_layout = QVBoxLayout()
        self.anim_wipe_layout.addLayout(self.anim_wipe_b_layout)

        self.anim_wipe_palette_b = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_wipe_palette_b.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic, f'wipe,{{"colorb": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}"
            )
        )
        self.anim_wipe_b_layout.addWidget(self.anim_wipe_palette_b)

        self.anim_wipe_b_bottom_layout = QHBoxLayout()
        self.anim_wipe_b_layout.addLayout(self.anim_wipe_b_bottom_layout)

        self.anim_wipe_b_bottom_layout.addStretch()

        self.anim_wipe_current_b_label = QLabel("Current")
        self.anim_wipe_current_b_label.setObjectName("h2")
        self.anim_wipe_b_bottom_layout.addWidget(self.anim_wipe_current_b_label)

        self.anim_wipe_current_b = ColorBlock()
        self.anim_wipe_current_b.setFixedHeight(32)
        self.anim_wipe_b_bottom_layout.addWidget(self.anim_wipe_current_b)

        self.anim_wipe_b_bottom_layout.addStretch()

        self.anim_wipe_speed = QSlider()
        self.anim_wipe_speed.setObjectName("big_slider")
        self.anim_wipe_speed.setRange(1, 5)
        self.anim_wipe_speed.valueChanged.connect(
            lambda: self.publish_and_update_args(
                self.settings.args_topic, f'wipe,{{"leds_iter": ' f"{self.anim_wipe_speed.value()}}}"
            )
        )
        self.anim_wipe_speed.sliderReleased.connect(
            lambda: self.publish_and_update_args(
                self.settings.args_topic, f'wipe,{{"speed": ' f"{self.anim_wipe_speed.value()}}}"
            )
        )
        self.anim_wipe_layout.addWidget(self.anim_wipe_speed)

        # Firework
        self.anim_config_stack.insertWidget(
            A_FIREWORK_INDEX, generate_animation_config_unavailable()
        )

        # Random / Random Color
        self.anim_random_widget = QWidget()
        self.anim_config_stack.insertWidget(
            A_RANDOM_INDEX, self.anim_random_widget
        )

        self.anim_random_layout = QHBoxLayout()
        self.anim_random_widget.setLayout(self.anim_random_layout)

        self.anim_random_palette = PaletteGrid(PALETTES["kevinbot"], self.sfx, size=56)
        self.anim_random_palette.selected.connect(
            lambda c: self.publish_and_update_args(
                self.settings.args_topic,
                f'random,{{"color": ' f"{list(hex_to_rgb(c.lstrip('#')))}}}",
            )
        )
        self.anim_random_layout.addWidget(self.anim_random_palette)

        self.anim_random_right_layout = QVBoxLayout()
        self.anim_random_layout.addLayout(self.anim_random_right_layout)

        self.anim_random_right_layout.addStretch()

        self.anim_random_current_label = QLabel("Current")
        self.anim_random_current_label.setObjectName("h2")
        self.anim_random_right_layout.addWidget(
            self.anim_random_current_label
        )

        self.anim_random_current = ColorBlock()
        self.anim_random_right_layout.addWidget(self.anim_random_current)

        self.anim_random_right_layout.addStretch()

        self.anim_config_stack.insertWidget(
            A_RANDOM_COLOR_INDEX, generate_animation_config_unavailable()
        )

        # Application settings
        self.settings_widget = QWidget()
        self.root_widget.insertWidget(M_SETTINGS_PAGE_INDEX, self.settings_widget)

        self.settings_root_layout = QVBoxLayout()
        self.settings_widget.setLayout(self.settings_root_layout)

        self.settings_top_bar = QHBoxLayout()
        self.settings_root_layout.addLayout(self.settings_top_bar)

        self.settings_back = QPushButton()
        self.settings_back.setFlat(True)
        self.settings_back.setIcon(icon("mdi6.arrow-left-box"))
        self.settings_back.setIconSize(QSize(48, 48))
        self.settings_back.clicked.connect(
            lambda: self.root_widget.setCurrentIndex(M_CONTROL_WIDGET_INDEX)
        )
        self.settings_back.clicked.connect(self.sfx.play)

        self.settings_restart = QPushButton()
        self.settings_restart.setFlat(True)
        self.settings_restart.setIcon(icon("mdi6.restart"))
        self.settings_restart.setIconSize(QSize(48, 48))
        self.settings_restart.clicked.connect(self.restart)

        self.settings_lock = LockButton()
        self.settings_lock.set_warning_text(
            "Changing these settings may result in the system to stop functioning. Do you want to unlock the settings?")
        self.settings_lock.locked.connect(self.lock_settings)
        self.settings_lock.unlocked.connect(self.unlock_settings)

        self.settings_top_bar.addWidget(self.settings_back)
        self.settings_top_bar.addStretch()
        self.settings_top_bar.addWidget(self.settings_restart)
        self.settings_top_bar.addStretch()
        self.settings_top_bar.addWidget(self.settings_lock)

        self.settings_side_by_side = QHBoxLayout()
        self.settings_root_layout.addLayout(self.settings_side_by_side)

        self.settings_sidebar_widget = QFrame()
        self.settings_side_by_side.addWidget(self.settings_sidebar_widget)

        self.settings_sidebar_layout = QVBoxLayout()
        self.settings_sidebar_widget.setLayout(self.settings_sidebar_layout)

        self.settings_sidebar_items: list[QToolButton] = []

        self.settings_pages = QStackedWidget()
        self.settings_pages.setEnabled(False)
        self.settings_side_by_side.addWidget(self.settings_pages)

        self.add_setting_sidebar_item(
            "MQTT Server",
            "mdi6.server-network",
            self.generate_mqtt_server_config_page(),
        )
        self.add_setting_sidebar_item(
            "MQTT Topics",
            "mdi6.slash-forward-box",
            self.generate_mqtt_topics_config_page(),
        )
        self.add_setting_sidebar_item(
            "Application Style",
            "mdi6.application-variable",
            self.generate_gui_config_page(),
        )

        self.set_cursor()
        if self.settings.fullscreen:
            self.showFullScreen()
        else:
            self.show()

    def check_mqtt_connection(self) -> None:
        if self.client.state == MqttClient.Connected:
            if self.root_widget.currentIndex() not in [
                M_ABOUT_PAGE_INDEX,
                M_ANIM_CONF_INDEX,
                M_SETTINGS_PAGE_INDEX,
            ]:
                self.root_widget.setCurrentIndex(M_CONTROL_WIDGET_INDEX)
            return
        elif self.client.state == MqttClient.Connecting:
            self.connection_timer.start()
            self.connection_attempts_label.setText(
                f"Connection Attempts: {self.connection_attempts}"
            )
            if self.root_widget.currentIndex() not in [
                M_ABOUT_PAGE_INDEX,
                M_SETTINGS_PAGE_INDEX,
            ]:
                self.root_widget.setCurrentIndex(M_CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1
        elif self.client.state == MqttClient.ConnectError:
            self.connection_timer.start()
            self.connection_attempts_label.setText(
                f"Connection Failed: {self.client.result_code}"
            )
            self.root_widget.setCurrentIndex(M_CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1
        else:
            self.client.connectToHost()
            self.connection_timer.start()
            self.connection_attempts_label.setText(
                f"Connection Attempts: {self.connection_attempts}"
            )
            self.root_widget.setCurrentIndex(M_CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1

    def on_client_connect(self) -> None:
        self.client.subscribe(self.settings.return_state_topic)
        self.client.subscribe(self.settings.return_brightness_topic)
        self.client.subscribe(self.settings.return_anim_topic)
        self.client.subscribe(self.settings.return_data_request_topic)
        self.client.publish(self.settings.data_request_topic, "request_type_full")

    def on_client_message(self, topic: str, payload: str) -> None:
        if topic == self.settings.return_state_topic:
            if payload == "ON":
                self.led_powered = PowerStates.ON
                self.control_power.setIcon(icon("mdi6.power", color="#66BB6A"))
            else:
                self.led_powered = PowerStates.OFF
                self.control_power.setIcon(icon("mdi6.power", color="#F44336"))

        elif topic == self.settings.return_brightness_topic:
            self.brightness_known = BrightnessStates.KNOWN
            self.brightness_value = int(payload)
            self.control_brightness_warning.setPixmap(
                icon("mdi6.check-circle", color="#66BB6A").pixmap(QSize(24, 24))
            )

        elif topic == self.settings.return_anim_topic:
            if payload in list(ANIMATION_LIST.values()):
                animation_name = list(ANIMATION_LIST.keys())[
                    list(ANIMATION_LIST.values()).index(payload)
                ]
                self.animation_sidebar_frame.setEnabled(True)
                self.update_animation_page(payload)
            else:
                animation_name = "Unknown"
            self.current_animation.setText(f"Current Animation: {animation_name}")

        elif topic == self.settings.return_data_request_topic:
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                # TODO: Handle this!
                return

            if "state" in data:
                if data["state"] == "ON":
                    self.led_powered = PowerStates.ON
                    self.control_power.setIcon(icon("mdi6.power", color="#66BB6A"))
                else:
                    self.led_powered = PowerStates.OFF
                    self.control_power.setIcon(icon("mdi6.power", color="#F44336"))

            if "animation" in data:
                if data["animation"] in list(ANIMATION_LIST.values()):
                    animation_name = list(ANIMATION_LIST.keys())[
                        list(ANIMATION_LIST.values()).index(data["animation"])
                    ]
                    self.animation_sidebar_frame.setEnabled(True)
                    self.update_animation_page(data["animation"])
                else:
                    animation_name = "Unknown"
                self.current_animation.setText(f"Current Animation: {animation_name}")

            if "brightness" in data:
                self.control_brightness_slider.setValue(data["brightness"])
                self.brightness_known = BrightnessStates.KNOWN
                self.control_brightness_warning.setPixmap(
                    icon("mdi6.check-circle", color="#66BB6A").pixmap(QSize(24, 24))
                )

            if "args" in data:
                self.animation_args = dict_to_dataclass(
                    json.loads(data["args"]), AnimationArgs
                )
                self.anim_single_color_current.set_rgb(
                    self.animation_args.single_color.color
                )
                self.anim_random_current.set_rgb(
                    self.animation_args.random.color
                )
                self.anim_fade_current_a.set_rgb(self.animation_args.fade.colora)
                self.anim_fade_current_b.set_rgb(self.animation_args.fade.colorb)
                self.anim_flash_current_a.set_rgb(self.animation_args.flash.colora)
                self.anim_flash_current_b.set_rgb(self.animation_args.flash.colorb)
                self.anim_wipe_current_a.set_rgb(self.animation_args.wipe.colora)
                self.anim_wipe_current_b.set_rgb(self.animation_args.wipe.colorb)
                if not self.anim_grainbow_ratio.isSliderDown():
                    self.anim_grainbow_ratio.blockSignals(True)
                    self.anim_grainbow_ratio.setValue(
                        round(self.animation_args.glitter_rainbow.glitter_ratio * 100)
                    )
                    self.anim_grainbow_ratio.blockSignals(False)

                if not self.anim_flash_speed.isSliderDown():
                    self.anim_flash_speed.blockSignals(True)
                    self.anim_flash_speed.setValue(self.animation_args.flash.speed)
                    self.anim_flash_speed.blockSignals(False)

            if "num_leds" in data:
                self.num_leds = data["num_leds"]

    def toggle_led_power(self) -> None:
        if self.led_powered == PowerStates.ON:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(self.settings.state_topic, "OFF")
        elif self.led_powered == PowerStates.OFF:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(self.settings.state_topic, "ON")
        else:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(self.settings.state_topic, "OFF")

    def update_brightness(self) -> None:
        self.brightness_known = BrightnessStates.UNKNOWN
        self.control_brightness_warning.setPixmap(
            icon("mdi6.alert", color="#FDD835").pixmap(QSize(24, 24))
        )
        self.client.publish(self.settings.brightness_topic, self.control_brightness_slider.value())

    def set_animation(self, anim_name: str) -> None:
        self.animation_sidebar_frame.setEnabled(False)
        self.client.publish(self.settings.animation_topic, ANIMATION_LIST[anim_name])

    def show_about(self) -> None:
        self.root_widget.setCurrentIndex(M_ABOUT_PAGE_INDEX)

    def show_settings(self) -> None:
        self.root_widget.setCurrentIndex(M_SETTINGS_PAGE_INDEX)
        if not self.settings_pages.isEnabled():
            self.settings_lock.flash_outline()

    def anim_conf(self) -> None:
        self.root_widget.setCurrentIndex(M_ANIM_CONF_INDEX)

    def update_animation_page(self, animation: str) -> None:
        if animation in ANIMATION_CONF_INDEXES:
            self.anim_config_stack.setCurrentIndex(ANIMATION_CONF_INDEXES[animation])
        else:
            self.anim_config_stack.setCurrentIndex(A_UNKNOWN_INDEX)

    def publish_and_update_args(self, topic: str, data: str) -> None:
        self.client.publish(topic, data)
        self.client.publish(self.settings.data_request_topic, "request_type_args")

    def add_setting_sidebar_item(self, title: str, qta_icon: str, content: QWidget | QFrame):
        i: int = len(self.settings_sidebar_items)

        button = QToolButton()
        button.setObjectName("sidebar_button")
        button.setText(title)
        button.setIcon(icon(qta_icon))
        button.setIconSize(QSize(24, 24))
        button.setFixedWidth(180)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.settings_sidebar_items.append(button)
        self.settings_sidebar_layout.addWidget(button)

        self.settings_pages.insertWidget(i, content)
        button.clicked.connect(lambda: self.settings_pages.setCurrentIndex(i))
        button.clicked.connect(self.sfx.play)

    def generate_mqtt_server_config_page(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        layout = QVBoxLayout()
        frame.setLayout(layout)

        warning = WarningBar("A relaunch is required for these settings to apply")
        layout.addWidget(warning)

        host_config_layout = QHBoxLayout()
        layout.addLayout(host_config_layout)

        host_config_label = QLabel("MQTT Broker Hostname/IP")
        host_config_label.setObjectName("config_label")
        host_config_layout.addWidget(host_config_label)

        host_config = QLineEdit()
        host_config.setText(self.settings.mqtt_host)
        host_config.textChanged.connect(self.settings.set_mqtt_host)
        host_config_layout.addWidget(host_config)

        port_config_layout = QHBoxLayout()
        layout.addLayout(port_config_layout)

        port_config_label = QLabel("MQTT Broker Port")
        port_config_label.setObjectName("config_label")
        port_config_layout.addWidget(port_config_label)

        port_config = QSpinBox()
        port_config.setRange(1, 65535)
        port_config.setValue(self.settings.mqtt_port)
        port_config.valueChanged.connect(self.settings.set_mqtt_port)
        port_config_layout.addWidget(port_config)

        return frame

    def generate_mqtt_topics_config_page(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        layout = QVBoxLayout()
        frame.setLayout(layout)

        warning = WarningBar("A relaunch is required for these settings to fully apply")
        layout.addWidget(warning)

        grid = QGridLayout()
        layout.addLayout(grid)

        generate_topic_config_row(
            grid,
            0,
            "Data Request Topic",
            self.settings.set_data_request_topic,
            lambda: self.settings.data_request_topic,
            "MQTTAnimator/data_request",
        )
        generate_topic_config_row(
            grid,
            1,
            "Data Request Return Topic",
            self.settings.set_return_data_request_topic,
            lambda: self.settings.return_data_request_topic,
            "MQTTAnimator/rdata_request",
        )
        generate_topic_config_row(
            grid,
            2,
            "State Topic",
            self.settings.set_state_topic,
            lambda: self.settings.state_topic,
            "MQTTAnimator/state",
        )
        generate_topic_config_row(
            grid,
            3,
            "State Return Topic",
            self.settings.set_return_state_topic,
            lambda: self.settings.return_state_topic,
            "MQTTAnimator/rstate",
        )
        generate_topic_config_row(
            grid,
            4,
            "Brightness Topic",
            self.settings.set_brightness_topic,
            lambda: self.settings.brightness_topic,
            "MQTTAnimator/brightness",
        )
        generate_topic_config_row(
            grid,
            5,
            "Brightness Return Topic",
            self.settings.set_return_brightness_topic,
            lambda: self.settings.return_brightness_topic,
            "MQTTAnimator/rbrightness",
        )
        generate_topic_config_row(
            grid,
            6,
            "Args Topic",
            self.settings.set_args_topic,
            lambda: self.settings.args_topic,
            "MQTTAnimator/args",
        )
        generate_topic_config_row(
            grid,
            7,
            "Animation Topic",
            self.settings.set_animation_topic,
            lambda: self.settings.animation_topic,
            "MQTTAnimator/animation",
        )
        generate_topic_config_row(
            grid,
            8,
            "Animation Return Topic",
            self.settings.set_return_anim_topic,
            lambda: self.settings.return_anim_topic,
            "MQTTAnimator/ranimation",
        )

        return frame

    def generate_gui_config_page(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        layout = QVBoxLayout()
        frame.setLayout(layout)

        warning = WarningBar("Restart the app for title to fully apply")
        layout.addWidget(warning)

        cursor_config_layout = QHBoxLayout()
        layout.addLayout(cursor_config_layout)

        cursor_config_label = QLabel("Cursor")
        cursor_config_layout.addWidget(cursor_config_label)

        cursor_system_radio = QRadioButton("System")
        cursor_system_radio.clicked.connect(lambda: self.set_cursor(CursorSetting.DEFAULT))
        cursor_config_layout.addWidget(cursor_system_radio)

        cursor_none_radio = QRadioButton("None")
        cursor_none_radio.clicked.connect(lambda: self.set_cursor(CursorSetting.NONE))
        cursor_config_layout.addWidget(cursor_none_radio)

        cursor_blob_radio = QRadioButton("Blob")
        cursor_blob_radio.clicked.connect(lambda: self.set_cursor(CursorSetting.BLOB))
        cursor_config_layout.addWidget(cursor_blob_radio)

        cursor_system_radio.blockSignals(True)
        cursor_none_radio.blockSignals(True)
        cursor_blob_radio.blockSignals(True)

        textbox_grid = QGridLayout()
        layout.addLayout(textbox_grid)

        generate_topic_config_row(
            textbox_grid,
            0,
            "App Title",
            self.set_title,
            lambda: self.settings.app_title,
            "NeoPixel Animator"
        )

        if self.settings.cursor_style == CursorSetting.DEFAULT:
            cursor_system_radio.setChecked(True)
        elif self.settings.cursor_style == CursorSetting.NONE:
            cursor_none_radio.setChecked(True)
        elif self.settings.cursor_style == CursorSetting.BLOB:
            cursor_blob_radio.setChecked(True)

        cursor_system_radio.blockSignals(False)
        cursor_none_radio.blockSignals(False)
        cursor_blob_radio.blockSignals(False)

        check_grid = QGridLayout()
        layout.addLayout(check_grid)

        custom_theme_label = QLabel("Enable Theming (recommended)")
        check_grid.addWidget(custom_theme_label, 0, 0)

        custom_theme_check = QCheckBox("Custom Theming")
        custom_theme_check.setChecked(self.settings.custom_theming)
        custom_theme_check.clicked.connect(self.set_custom_theming)
        check_grid.addWidget(custom_theme_check, 0, 1)

        dark_mode_label = QLabel("Enable Dark Mode (only if above option is checked)")
        check_grid.addWidget(dark_mode_label, 1, 0)

        dark_mode_check = QCheckBox("Dark Mode")
        dark_mode_check.setChecked(self.settings.dark_mode)
        dark_mode_check.clicked.connect(self.set_dark_mode)
        check_grid.addWidget(dark_mode_check, 1, 1)

        dark_mode_layout = QHBoxLayout()
        layout.addLayout(dark_mode_layout)

        fullscreen_label = QLabel("Always show app in fullscreen")
        check_grid.addWidget(fullscreen_label, 2, 0)

        fullscreen_check = QCheckBox("Fullscreen")
        fullscreen_check.setChecked(self.settings.fullscreen)
        fullscreen_check.clicked.connect(self.set_fullscreen)
        check_grid.addWidget(fullscreen_check, 2, 1)

        sfx_vol_layout = QHBoxLayout()
        layout.addLayout(sfx_vol_layout)

        sfx_volume_label = QLabel("Click volume:")
        sfx_vol_layout.addWidget(sfx_volume_label)

        sfx_volume = QSlider(Qt.Orientation.Horizontal)
        sfx_volume.setRange(0, 100)
        sfx_volume.setValue(int(self.settings.sfx_volume * 100))
        sfx_volume.valueChanged.connect(self.set_sfx_volume)
        sfx_vol_layout.addWidget(sfx_volume)

        return frame

    def lock_settings(self):
        self.settings_pages.setEnabled(False)

    def unlock_settings(self):
        self.settings_pages.setEnabled(True)

    def on_settings_click(self, _: QMouseEvent):
        if not self.settings_pages.isEnabled():
            self.settings_lock.flash_outline()

    def set_cursor(self, cursor: CursorSetting | None = None):
        if cursor:
            self.settings.cursor_style = cursor
        else:
            cursor = self.settings.cursor_style

        if cursor == CursorSetting.DEFAULT:
            app.setOverrideCursor(QCursor())
        elif cursor == CursorSetting.NONE:
            app.setOverrideCursor(Qt.CursorShape.BlankCursor)
        elif cursor == CursorSetting.BLOB:
            app.setOverrideCursor(QCursor(QPixmap("assets/cursors/blob.png")))

    def set_title(self, title: str):
        self.settings.set_app_title(title)
        self.control_title.setText(title)

    def set_custom_theming(self, enable: bool = True):
        if self.settings.custom_theming != enable:
            self.settings.custom_theming = enable

        if enable:
            if self.settings.dark_mode:
                qtadark(app)
                with open("style.qss", "r", encoding="utf-8") as qss:
                    app.setStyleSheet(load_stylesheet(custom_colors={
                        "[dark]": {
                            "primary": "#F44336",
                            "background": "#000912",
                            "border": "#263238",
                        }
                    }) + "\n" + qss.read())
                QFontDatabase.addApplicationFont(
                    "assets/fonts/Roboto/Roboto/Roboto-Regular.ttf"
                )
            else:
                qtalight(app)
                with open("style.qss", "r", encoding="utf-8") as qss:
                    app.setStyleSheet(load_stylesheet(theme="light") + "\n" + qss.read())
                QFontDatabase.addApplicationFont(
                    "assets/fonts/Roboto/Roboto/Roboto-Regular.ttf"
                )
        else:
            app.setStyleSheet("")

    def set_dark_mode(self, enable: bool = True):
        self.settings.dark_mode = enable
        self.set_custom_theming(self.settings.custom_theming)

    def set_fullscreen(self, enable: bool = False):
        self.settings.fullscreen = enable
        if enable:
            self.showFullScreen()
        else:
            if self.isFullScreen():
                self.showNormal()
                return
            self.show()

    def set_sfx_volume(self, volume: int):
        self.sfx.setVolume(volume / 100)
        self.settings.sfx_volume = volume / 100

    def restart(self):
        self.deleteLater()
        logger.info("Application restarting")
        MainWindow.singleton = MainWindow(app)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(app)
    sys.exit(app.exec())
