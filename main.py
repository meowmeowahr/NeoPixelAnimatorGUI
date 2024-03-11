import dataclasses
import enum
import functools
import json
import random
import sys
import traceback
import logging
import platform

import yaml

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import qdarktheme
import qtawesome as qta

import palette

import animation_data
import mqtt

__version__ = "0.1.0"

import widgets

if platform.system() == "Windows":
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"meowmeowahr.npanimator.client.{__version__}")

# Import yaml config
with open("config.yaml", encoding="utf-8") as stream:
    try:
        configuration = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        traceback.print_exc()
        logging.critical("YAML Parsing Error, %s", exc)
        sys.exit(0)

mqtt_config: dict = configuration.get("mqtt", {})
mqtt_topics: dict = mqtt_config.get("topics", {})
mqtt_reconnection: dict = mqtt_config.get("reconnection", {})

gui_config: dict = configuration.get("gui", {})

mqtt_borker: str = mqtt_config.get("host", "localhost")
mqtt_port: int = mqtt_config.get("port", 1883)
client_id = f"mqtt-animator-{random.randint(0, 1000)}"

data_request_topic: str = mqtt_topics.get("data_request_topic", "MQTTAnimator/data_request")
state_topic: str = mqtt_topics.get("state_topic", "MQTTAnimator/state")
brightness_topic: str = mqtt_topics.get("brightness_topic", "MQTTAnimator/brightness")
args_topic: str = mqtt_topics.get("args_topic", "MQTTAnimator/args")
animation_topic: str = mqtt_topics.get("animation_topic", "MQTTAnimator/animation")

data_request_return_topic: str = mqtt_topics.get("return_data_request_topic",
                                                 "MQTTAnimator/rdata_request")
state_return_topic: str = mqtt_topics.get("return_state_topic", "MQTTAnimator/rstate")
anim_return_topic: str = mqtt_topics.get("return_anim_topic", "MQTTAnimator/ranimation")
brightness_return_topic: str = mqtt_topics.get("return_brightness_topic",
                                               "MQTTAnimator/rbrightness")

application_title: str = gui_config.get("title", "NeoPixel Animator")
app_fullscreen: bool = gui_config.get("fullscreen", False)
app_custom_theme: bool = gui_config.get("custom_theming", True)

fixed_size_config: dict = gui_config.get("fixed_size", {})

fixed_size_enabled: bool = fixed_size_config.get("enabled", False)
fixed_size_width: int = fixed_size_config.get("width", 1024)
fixed_size_height: int = fixed_size_config.get("height", 600)

ANIMATION_LIST = {
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
    "Random": "Random",
    "Random Color": "RandomColor"
}

M_CONNECTION_WIDGET_INDEX = 0
M_CONTROL_WIDGET_INDEX = 1
M_ABOUT_PAGE_INDEX = 2
M_ANIM_CONF_INDEX = 3

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
A_RANDOM_INDEX = 11
A_RANDOM_COLOR_INDEX = 12

ANIMATION_CONF_INDEXES = {
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
    "Random": A_RANDOM_INDEX,
    "RandomColor": A_RANDOM_COLOR_INDEX
}


class PowerStates(enum.Enum):
    OFF = 0
    ON = 1
    UNKNOWN = 2


class BrightnessStates(enum.Enum):
    KNOWN = 0
    UNKNOWN = 1


def hex_to_rgb(hexa):
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def dict_to_dataclass(data_dict, dataclass_type):
    # Recursively convert nested dictionaries to dataclasses
    for field in dataclasses.fields(dataclass_type):
        field_name = field.name
        if hasattr(field.type, "__annotations__") and field_name in data_dict:
            data_dict[field_name] = dict_to_dataclass(data_dict[field_name], field.type)

    return dataclass_type(**data_dict)

def map_range(x: float, in_min: float, in_max: float, out_min: float, out_max: float):
    """Map bounds of input to bounds of output

    Args:
        x (int): Input value
        in_min (int): Input lower bound
        in_max (int): Input upper bound
        out_min (int): Output lower bound
        out_max (int): Output upper bound

    Returns:
        int: Output value
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Mqtt Client
        self.client = mqtt.MqttClient()
        self.client.hostname = mqtt_borker
        self.client.port = mqtt_port

        self.client.connected.connect(self.on_client_connect)
        self.client.messageSignal.connect(self.on_client_message)

        self.connection_attempts = 1

        # Led State
        self.led_powered = PowerStates.UNKNOWN
        self.brightness_value = 0
        self.brightness_known = BrightnessStates.UNKNOWN
        self.animation_args = animation_data.AnimationArgs()

        self.setWindowTitle("NeoPixel Animator Client")
        self.setWindowIcon(QIcon("assets/icons/icon-128.svg"))

        if fixed_size_enabled:
            self.setFixedSize(QSize(fixed_size_width, fixed_size_height))

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

        self.connection_attempts_label = QLabel(f"Connection Attempts: {self.connection_attempts}")
        self.connection_attempts_label.setObjectName("h3")
        self.connection_attempts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_layout.addWidget(self.connection_attempts_label)

        self.connection_timer = QTimer(self)
        self.connection_timer.setInterval(1000)
        self.connection_timer.timeout.connect(self.check_mqtt_connection)
        self.connection_timer.start()

        # Control
        self.control_widget = QWidget()
        self.root_widget.insertWidget(M_CONTROL_WIDGET_INDEX, self.control_widget)

        self.control_layout = QVBoxLayout()
        self.control_widget.setLayout(self.control_layout)

        self.control_top_bar = QHBoxLayout()
        self.control_layout.addLayout(self.control_top_bar)

        self.control_title = QLabel(application_title)
        self.control_title.setObjectName("h2")
        self.control_top_bar.addWidget(self.control_title)

        self.control_top_bar.addStretch()

        self.control_power = QPushButton()
        self.control_power.setFlat(True)
        self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
        self.control_power.setIconSize(QSize(56, 56))
        self.control_power.clicked.connect(self.toggle_led_power)
        self.control_top_bar.addWidget(self.control_power)

        self.control_about = QPushButton()
        self.control_about.setFlat(True)
        self.control_about.setIcon(qta.icon("mdi6.information-slab-circle"))
        self.control_about.setIconSize(QSize(24, 24))
        self.control_about.clicked.connect(self.show_about)
        self.control_about.setFixedWidth(self.control_about.minimumSizeHint().height())
        self.control_top_bar.addWidget(self.control_about)

        self.control_brightness_box = QGroupBox("Brightness")
        self.control_layout.addWidget(self.control_brightness_box)

        self.control_brightness_layout = QHBoxLayout()
        self.control_brightness_box.setLayout(self.control_brightness_layout)

        self.control_brightness_warning = QLabel()
        self.control_brightness_warning.setPixmap(qta.icon("mdi6.alert", color="#FDD835").pixmap(QSize(24, 24)))
        self.control_brightness_warning.setToolTip("Brightness data may be inaccurate")
        self.control_brightness_layout.addWidget(self.control_brightness_warning)

        self.control_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.control_brightness_slider.setRange(1, 255)
        self.control_brightness_slider.valueChanged.connect(self.update_brightness)
        self.control_brightness_layout.addWidget(self.control_brightness_slider)

        self.current_animation = QLabel("Current Animation: Unknown")
        self.current_animation.setObjectName("h4")
        self.current_animation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.control_layout.addWidget(self.current_animation)

        self.animation_layout = QHBoxLayout()
        self.control_layout.addLayout(self.animation_layout)

        self.control_animatior_scroll = QScrollArea()
        self.control_animatior_scroll.setWidgetResizable(True)
        self.control_animatior_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        QScroller.grabGesture(self.control_animatior_scroll, QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        self.animation_layout.addWidget(self.control_animatior_scroll)

        self.control_animator_widget = QWidget()
        self.control_animatior_scroll.setWidget(self.control_animator_widget)

        self.control_animator_layout = QGridLayout()
        self.control_animator_widget.setLayout(self.control_animator_layout)

        self.control_animation_list = []
        for idx, key in enumerate(ANIMATION_LIST.keys()):
            widget = AnimationWidget(key)
            widget.mousePressEvent = functools.partial(self.set_animation, key)
            self.control_animation_list.append(widget)
            self.control_animator_layout.addWidget(widget, idx % 2, idx // 2)

        self.animation_sidebar_frame = QFrame()
        self.animation_sidebar_frame.setFrameShape(QFrame.Shape.Box)
        self.animation_sidebar_frame.setEnabled(False)
        self.animation_layout.addWidget(self.animation_sidebar_frame)

        self.animation_sidebar_layout = QVBoxLayout()
        self.animation_sidebar_frame.setLayout(self.animation_sidebar_layout)

        self.animation_settings = QPushButton()
        self.animation_settings.setIcon(qta.icon("mdi6.tune-vertical-variant"))
        self.animation_settings.setIconSize(QSize(42, 42))
        self.animation_settings.setFixedWidth(self.animation_settings.minimumSizeHint().height())
        self.animation_settings.clicked.connect(self.anim_conf)
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
        self.about_back.setIcon(qta.icon("mdi6.arrow-left-box", color="#9EA7AA"))
        self.about_back.setIconSize(QSize(48, 48))
        self.about_back.clicked.connect(lambda: self.root_widget.setCurrentIndex(M_CONTROL_WIDGET_INDEX))
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
        self.about_qt_button.clicked.connect(app.aboutQt)
        self.about_right_layout.addWidget(self.about_qt_button)
        self.about_right_layout.setAlignment(self.about_qt_button, Qt.AlignmentFlag.AlignCenter)

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
        self.anim_conf_back.setIcon(qta.icon("mdi6.arrow-left-box", color="#9EA7AA"))
        self.anim_conf_back.setIconSize(QSize(48, 48))
        self.anim_conf_back.clicked.connect(lambda: self.root_widget.setCurrentIndex(M_CONTROL_WIDGET_INDEX))
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
        self.unknown_anim_icon.setPixmap(qta.icon("mdi6.alert-circle", color="#FDD835").pixmap(128, 128))
        self.unknown_anim_layout.addWidget(self.unknown_anim_icon)

        self.unknown_anim_label = QLabel("Animation Unknown")
        self.unknown_anim_label.setObjectName("h1")
        self.unknown_anim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unknown_anim_layout.addWidget(self.unknown_anim_label)

        self.unknown_anim_layout.addStretch()

        self.anim_single_color_widget = QWidget()
        self.anim_config_stack.insertWidget(A_SINGLE_COLOR_INDEX, self.anim_single_color_widget)

        self.anim_single_color_layout = QHBoxLayout()
        self.anim_single_color_widget.setLayout(self.anim_single_color_layout)

        self.anim_single_color_palette = palette.PaletteGrid(palette.PALETTES["kevinbot"], size=56)
        self.anim_single_color_palette.selected.connect(
            lambda c: self.publish_and_update_args(args_topic, f"single_color,{{\"color\": "
                                                               f"{list(hex_to_rgb(c.lstrip('#')))}}}")
        )
        self.anim_single_color_layout.addWidget(self.anim_single_color_palette)

        self.anim_single_color_right_layout = QVBoxLayout()
        self.anim_single_color_layout.addLayout(self.anim_single_color_right_layout)

        self.anim_single_color_right_layout.addStretch()

        self.anim_single_color_current_label = QLabel("Current")
        self.anim_single_color_current_label.setObjectName("h2")
        self.anim_single_color_right_layout.addWidget(self.anim_single_color_current_label)

        self.anim_single_color_current = widgets.ColorBlock()
        self.anim_single_color_right_layout.addWidget(self.anim_single_color_current)

        self.anim_single_color_right_layout.addStretch()

        # Rainbow Conf
        self.anim_config_stack.insertWidget(A_RAINBOW_INDEX, self.generate_animation_config_unavailabe())

        # Glitter Rainbow Conf

        self.anim_grainbow_widget = QWidget()
        self.anim_config_stack.insertWidget(A_GLITTER_RAINBOW_INDEX, self.anim_grainbow_widget)

        self.anim_grainbow_layout = QVBoxLayout()
        self.anim_grainbow_widget.setLayout(self.anim_grainbow_layout)

        self.anim_grainbow_layout.addStretch()

        self.anim_grainbow_ratio_label = QLabel("Glitter to Normal Ratio")
        self.anim_grainbow_ratio_label.setObjectName("h3")
        self.anim_grainbow_layout.addWidget(self.anim_grainbow_ratio_label)

        self.anim_grainbow_ratio = QSlider(Qt.Orientation.Horizontal)
        self.anim_grainbow_ratio.setRange(1, 50)
        self.anim_grainbow_ratio.valueChanged.connect(
            lambda: self.publish_and_update_args(
                args_topic, f"glitter_rainbow,{{\"glitter_ratio\": {self.anim_grainbow_ratio.value()/100}}}"
            )
        )
        self.anim_grainbow_ratio.sliderReleased.connect(
            lambda: self.publish_and_update_args(
                args_topic, f"glitter_rainbow,{{\"glitter_ratio\": {self.anim_grainbow_ratio.value() / 100}}}"
            )
        )
        self.anim_grainbow_layout.addWidget(self.anim_grainbow_ratio)

        self.anim_grainbow_layout.addStretch()

        # Colorloop Conf
        self.anim_config_stack.insertWidget(A_COLORLOOP_INDEX, self.generate_animation_config_unavailabe())

        # Magic Conf
        self.anim_config_stack.insertWidget(A_MAGIC_INDEX, self.generate_animation_config_unavailabe())

        # Fire Conf
        self.anim_config_stack.insertWidget(A_FIRE_INDEX, self.generate_animation_config_unavailabe())

        # Colored Lights Conf
        self.anim_config_stack.insertWidget(A_COLORED_LIGHTS_INDEX, self.generate_animation_config_unavailabe())

        # Fade config
        self.anim_fade_widget = QWidget()
        self.anim_config_stack.insertWidget(A_FADE_INDEX, self.anim_fade_widget)

        self.anim_fade_layout = QHBoxLayout()
        self.anim_fade_widget.setLayout(self.anim_fade_layout)

        self.anim_fade_a_layout = QVBoxLayout()
        self.anim_fade_layout.addLayout(self.anim_fade_a_layout)

        self.anim_fade_palette_a = palette.PaletteGrid(palette.PALETTES["kevinbot"], size=56)
        self.anim_fade_palette_a.selected.connect(
            lambda c: self.publish_and_update_args(args_topic, f"fade,{{\"colora\": "
                                                               f"{list(hex_to_rgb(c.lstrip('#')))}}}")
        )
        self.anim_fade_a_layout.addWidget(self.anim_fade_palette_a)

        self.anim_fade_a_bottom_layout = QHBoxLayout()
        self.anim_fade_a_layout.addLayout(self.anim_fade_a_bottom_layout)

        self.anim_fade_a_bottom_layout.addStretch()

        self.anim_fade_current_a_label = QLabel("Current")
        self.anim_fade_current_a_label.setObjectName("h2")
        self.anim_fade_a_bottom_layout.addWidget(self.anim_fade_current_a_label)

        self.anim_fade_current_a = widgets.ColorBlock()
        self.anim_fade_current_a.setFixedHeight(32)
        self.anim_fade_a_bottom_layout.addWidget(self.anim_fade_current_a)

        self.anim_fade_a_bottom_layout.addStretch()

        self.anim_fade_divider = QFrame()
        self.anim_fade_divider.setFrameShape(QFrame.Shape.VLine)
        self.anim_fade_layout.addWidget(self.anim_fade_divider)

        self.anim_fade_b_layout = QVBoxLayout()
        self.anim_fade_layout.addLayout(self.anim_fade_b_layout)

        self.anim_fade_palette_b = palette.PaletteGrid(palette.PALETTES["kevinbot"], size=56)
        self.anim_fade_palette_b.selected.connect(
            lambda c: self.publish_and_update_args(args_topic, f"fade,{{\"colorb\": "
                                                               f"{list(hex_to_rgb(c.lstrip('#')))}}}")
        )
        self.anim_fade_b_layout.addWidget(self.anim_fade_palette_b)

        self.anim_fade_b_bottom_layout = QHBoxLayout()
        self.anim_fade_b_layout.addLayout(self.anim_fade_b_bottom_layout)

        self.anim_fade_b_bottom_layout.addStretch()

        self.anim_fade_current_b_label = QLabel("Current")
        self.anim_fade_current_b_label.setObjectName("h2")
        self.anim_fade_b_bottom_layout.addWidget(self.anim_fade_current_b_label)

        self.anim_fade_current_b = widgets.ColorBlock()
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

        self.anim_flash_palette_a = palette.PaletteGrid(palette.PALETTES["kevinbot"], size=56)
        self.anim_flash_palette_a.selected.connect(
            lambda c: self.publish_and_update_args(args_topic, f"flash,{{\"colora\": "
                                                               f"{list(hex_to_rgb(c.lstrip('#')))}}}")
        )
        self.anim_flash_a_layout.addWidget(self.anim_flash_palette_a)

        self.anim_flash_a_bottom_layout = QHBoxLayout()
        self.anim_flash_a_layout.addLayout(self.anim_flash_a_bottom_layout)

        self.anim_flash_a_bottom_layout.addStretch()

        self.anim_flash_current_a_label = QLabel("Current")
        self.anim_flash_current_a_label.setObjectName("h2")
        self.anim_flash_a_bottom_layout.addWidget(self.anim_flash_current_a_label)

        self.anim_flash_current_a = widgets.ColorBlock()
        self.anim_flash_current_a.setFixedHeight(32)
        self.anim_flash_a_bottom_layout.addWidget(self.anim_flash_current_a)

        self.anim_flash_a_bottom_layout.addStretch()

        self.anim_flash_divider = QFrame()
        self.anim_flash_divider.setFrameShape(QFrame.Shape.VLine)
        self.anim_flash_layout.addWidget(self.anim_flash_divider)

        self.anim_flash_b_layout = QVBoxLayout()
        self.anim_flash_layout.addLayout(self.anim_flash_b_layout)

        self.anim_flash_palette_b = palette.PaletteGrid(palette.PALETTES["kevinbot"], size=56)
        self.anim_flash_palette_b.selected.connect(
            lambda c: self.publish_and_update_args(args_topic, f"flash,{{\"colorb\": "
                                                               f"{list(hex_to_rgb(c.lstrip('#')))}}}")
        )
        self.anim_flash_b_layout.addWidget(self.anim_flash_palette_b)

        self.anim_flash_b_bottom_layout = QHBoxLayout()
        self.anim_flash_b_layout.addLayout(self.anim_flash_b_bottom_layout)

        self.anim_flash_b_bottom_layout.addStretch()

        self.anim_flash_current_b_label = QLabel("Current")
        self.anim_flash_current_b_label.setObjectName("h2")
        self.anim_flash_b_bottom_layout.addWidget(self.anim_flash_current_b_label)

        self.anim_flash_current_b = widgets.ColorBlock()
        self.anim_flash_current_b.setFixedHeight(32)
        self.anim_flash_b_bottom_layout.addWidget(self.anim_flash_current_b)

        self.anim_flash_b_bottom_layout.addStretch()

        self.anim_flash_speed = QSlider()
        self.anim_flash_speed.setRange(3, 50)
        self.anim_flash_speed.valueChanged.connect(
            lambda: self.publish_and_update_args(args_topic, f"flash,{{\"speed\": "
                                                               f"{self.anim_flash_speed.value()}}}")
        )
        self.anim_flash_speed.sliderReleased.connect(
            lambda: self.publish_and_update_args(args_topic, f"flash,{{\"speed\": "
                                                               f"{self.anim_flash_speed.value()}}}")
        )
        self.anim_flash_layout.addWidget(self.anim_flash_speed)

        if app_fullscreen:
            self.showFullScreen()
        else:
            self.show()

    def check_mqtt_connection(self):
        if self.client.state == mqtt.MqttClient.Connected:
            if self.root_widget.currentIndex() not in [M_ABOUT_PAGE_INDEX, M_ANIM_CONF_INDEX]:
                self.root_widget.setCurrentIndex(M_CONTROL_WIDGET_INDEX)
            return
        elif self.client.state == mqtt.MqttClient.Connecting:
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Attempts: {self.connection_attempts}")
            self.root_widget.setCurrentIndex(M_CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1
        elif self.client.state == mqtt.MqttClient.ConnectError:
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Failed: {self.client.result_code}")
            self.root_widget.setCurrentIndex(M_CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1
        else:
            self.client.connectToHost()
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Attempts: {self.connection_attempts}")
            self.root_widget.setCurrentIndex(M_CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1

    def on_client_connect(self):
        self.client.subscribe(state_return_topic)
        self.client.subscribe(brightness_return_topic)
        self.client.subscribe(anim_return_topic)
        self.client.subscribe(data_request_return_topic)
        self.client.publish(data_request_topic, "request_type_full")

    def on_client_message(self, topic: str, payload: str):
        if topic == state_return_topic:
            if payload == "ON":
                self.led_powered = PowerStates.ON
                self.control_power.setIcon(qta.icon("mdi6.power", color="#66BB6A"))
            else:
                self.led_powered = PowerStates.OFF
                self.control_power.setIcon(qta.icon("mdi6.power", color="#F44336"))

        elif topic == brightness_return_topic:
            self.brightness_known = BrightnessStates.KNOWN
            self.brightness_value = int(payload)
            self.control_brightness_warning.setPixmap(
                qta.icon("mdi6.check-circle", color="#66BB6A").pixmap(QSize(24, 24)))

        elif topic == anim_return_topic:
            if payload in list(ANIMATION_LIST.values()):
                animation_name = list(ANIMATION_LIST.keys())[list(ANIMATION_LIST.values()).index(payload)]
                self.animation_sidebar_frame.setEnabled(True)
                self.update_animation_page(payload)
            else:
                animation_name = "Unknown"
            self.current_animation.setText(f"Current Animation: {animation_name}")

        elif topic == data_request_return_topic:
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                # TODO: Handle this!
                return

            if "state" in data:
                if data["state"] == "ON":
                    self.led_powered = PowerStates.ON
                    self.control_power.setIcon(qta.icon("mdi6.power", color="#66BB6A"))
                else:
                    self.led_powered = PowerStates.OFF
                    self.control_power.setIcon(qta.icon("mdi6.power", color="#F44336"))

            if "animation" in data:
                if data["animation"] in list(ANIMATION_LIST.values()):
                    animation_name = list(ANIMATION_LIST.keys())[list(ANIMATION_LIST.values()).index(data["animation"])]
                    self.animation_sidebar_frame.setEnabled(True)
                    self.update_animation_page(data["animation"])
                else:
                    animation_name = "Unknown"
                self.current_animation.setText(f"Current Animation: {animation_name}")

            if "brightness" in data:
                self.control_brightness_slider.setValue(data["brightness"])
                self.brightness_known = BrightnessStates.KNOWN
                self.control_brightness_warning.setPixmap(
                    qta.icon("mdi6.check-circle", color="#66BB6A").pixmap(QSize(24, 24)))

            if "args" in data:
                self.animation_args = dict_to_dataclass(json.loads(data["args"]), animation_data.AnimationArgs)
                self.anim_single_color_current.setRGB(self.animation_args.single_color.color)
                self.anim_fade_current_a.setRGB(self.animation_args.fade.colora)
                self.anim_fade_current_b.setRGB(self.animation_args.fade.colorb)
                self.anim_flash_current_a.setRGB(self.animation_args.flash.colora)
                self.anim_flash_current_b.setRGB(self.animation_args.flash.colorb)
                if not self.anim_grainbow_ratio.isSliderDown():
                    self.anim_grainbow_ratio.blockSignals(True)
                    self.anim_grainbow_ratio.setValue(round(self.animation_args.glitter_rainbow.glitter_ratio * 100))
                    self.anim_grainbow_ratio.blockSignals(False)

                if not self.anim_flash_speed.isSliderDown():
                    self.anim_flash_speed.blockSignals(True)
                    self.anim_flash_speed.setValue(self.animation_args.flash.speed)
                    self.anim_flash_speed.blockSignals(False)

    def toggle_led_power(self):
        if self.led_powered == PowerStates.ON:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(state_topic, "OFF")
        elif self.led_powered == PowerStates.OFF:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(state_topic, "ON")
        else:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(state_topic, "OFF")

    def update_brightness(self):
        self.brightness_known = BrightnessStates.UNKNOWN
        self.control_brightness_warning.setPixmap(qta.icon("mdi6.alert", color="#FDD835").pixmap(QSize(24, 24)))
        self.client.publish(brightness_topic, self.control_brightness_slider.value())

    def set_animation(self, name: str, _) -> None:
        self.animation_sidebar_frame.setEnabled(False)
        self.client.publish(animation_topic, ANIMATION_LIST[name])

    def show_about(self):
        self.root_widget.setCurrentIndex(M_ABOUT_PAGE_INDEX)

    def anim_conf(self):
        self.root_widget.setCurrentIndex(M_ANIM_CONF_INDEX)

    def update_animation_page(self, animation: str) -> None:
        if animation in ANIMATION_CONF_INDEXES.keys():
            self.anim_config_stack.setCurrentIndex(ANIMATION_CONF_INDEXES[animation])
        else:
            self.anim_config_stack.setCurrentIndex(A_UNKNOWN_INDEX)

    def generate_animation_config_unavailabe(self) -> QWidget:
        anim_widget = QWidget()

        anim_layout = QVBoxLayout()
        anim_widget.setLayout(anim_layout)

        anim_layout.addStretch()

        unknown_anim_icon = QLabel()
        unknown_anim_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unknown_anim_icon.setPixmap(qta.icon("mdi6.alert-circle", color="#FDD835").pixmap(128, 128))
        anim_layout.addWidget(unknown_anim_icon)

        anim_label = QLabel("This animation does not have any settings")
        anim_label.setObjectName("h1")
        anim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        anim_layout.addWidget(anim_label)

        anim_layout.addStretch()

        return anim_widget

    def publish_and_update_args(self, topic, data):
        self.client.publish(topic, data)
        self.client.publish(data_request_topic, "request_type_args")


class AnimationWidget(QFrame):
    def __init__(self, title: str = "Animation"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumWidth(160)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.icon = QLabel()

        if title == "Single Color":
            self.icon.setPixmap(qta.icon("mdi6.moon-full", color="#FFEE58").pixmap(72, 72))
        elif title == "Rainbow":
            self.icon.setPixmap(qta.icon("ph.rainbow", color="#FFEE58").pixmap(72, 72))
        elif title == "Colorloop":
            self.icon.setPixmap(qta.icon("mdi6.refresh", color="#FFEE58").pixmap(72, 72))
        elif title == "Fire":
            self.icon.setPixmap(qta.icon("mdi6.fire", color="#FFEE58").pixmap(72, 72))
        elif title == "Magic":
            self.icon.setPixmap(qta.icon("mdi6.magic-staff", color="#FFEE58").pixmap(72, 72))
        elif title == "Colored Lights":
            self.icon.setPixmap(qta.icon("mdi6.string-lights", color="#FFEE58").pixmap(72, 72))
        elif title == "Flash":
            self.icon.setPixmap(qta.icon("mdi6.flash", color="#FFEE58").pixmap(72, 72))
        elif title == "Fade":
            self.icon.setPixmap(qta.icon("mdi6.transition", color="#FFEE58").pixmap(72, 72))
        elif title == "Wipe":
            self.icon.setPixmap(qta.icon("mdi6.chevron-double-right", color="#FFEE58").pixmap(72, 72))
        elif title == "Glitter Rainbow":
            self.icon.setPixmap(qta.icon("mdi6.auto-mode", color="#FFEE58").pixmap(72, 72))
        else:
            self.icon.setPixmap(qta.icon("mdi6.auto-fix", color="#FFEE58").pixmap(72, 72))

        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon)

        self.title = QLabel(title)
        self.title.setObjectName("h3")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if app_custom_theme:
        qta.dark(app)
        with open("style.qss", "r", encoding="utf-8") as qss:
            app.setStyleSheet(qdarktheme.load_stylesheet() + "\n" + qss.read())
        QFontDatabase.addApplicationFont("assets/fonts/Cabin/static/Cabin-Regular.ttf")

    win = MainWindow()
    sys.exit(app.exec())
