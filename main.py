import enum
import functools
import json
import random
import sys
import traceback
import logging

import yaml

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import qdarktheme
import qtawesome as qta

import mqtt

__version__ = "0.1.0"

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

ANIMATION_LIST = {"Single Color": "SingleColor",
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
                  "Random Color": "RandomColor"}

CONNECTION_WIDGET_INDEX = 0
CONTROL_WIDGET_INDEX = 1
ABOUT_PAGE_INDEX = 2


class PowerStates(enum.Enum):
    OFF = 0
    ON = 1
    UNKNOWN = 2


class BrightnessStates(enum.Enum):
    KNOWN = 0
    UNKNOWN = 1


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

        self.setWindowTitle("NeoPixel Animator Client")
        self.setWindowIcon(QIcon("assets/icons/icon-128.svg"))

        self.root_widget = QStackedWidget()
        self.setCentralWidget(self.root_widget)

        self.connection_widget = QWidget()
        self.root_widget.insertWidget(CONNECTION_WIDGET_INDEX, self.connection_widget)

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
        self.root_widget.insertWidget(CONTROL_WIDGET_INDEX, self.control_widget)

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
        self.control_power.setIconSize(QSize(48, 48))
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
        self.animation_settings.setIconSize(QSize(36, 36))
        self.animation_settings.setFixedWidth(self.animation_settings.minimumSizeHint().height())
        self.animation_settings.setFlat(True)
        self.animation_sidebar_layout.addWidget(self.animation_settings)

        # About
        self.about_widget = QWidget()
        self.root_widget.insertWidget(ABOUT_PAGE_INDEX, self.about_widget)

        self.about_layout = QVBoxLayout()
        self.about_widget.setLayout(self.about_layout)

        self.about_top_bar = QHBoxLayout()
        self.about_layout.addLayout(self.about_top_bar)

        self.about_back = QPushButton()
        self.about_back.setFlat(True)
        self.about_back.setIcon(qta.icon("mdi6.arrow-left-box", color="#9EA7AA"))
        self.about_back.setIconSize(QSize(48, 48))
        self.about_back.clicked.connect(lambda: self.root_widget.setCurrentIndex(CONTROL_WIDGET_INDEX))
        self.about_top_bar.addWidget(self.about_back)

        self.about_top_bar.addStretch()

        self.about_side_by_side = QHBoxLayout()
        self.about_layout.addLayout(self.about_side_by_side)

        self.about_icon = QLabel()
        self.about_icon.setPixmap(QPixmap("assets/icons/icon-512.svg"))
        self.about_icon.setScaledContents(True)
        self.about_icon.setFixedSize(QSize(240, 240))
        self.about_side_by_side.addWidget(self.about_icon)

        self.about_right_layout = QVBoxLayout()
        self.about_side_by_side.addLayout(self.about_right_layout)

        self.about_right_layout.addStretch()

        self.about_title = QLabel("NeoPixel Animation Client")
        self.about_title.setObjectName("h0")
        self.about_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.about_right_layout.addWidget(self.about_title)

        self.about_version = QLabel(__version__)
        self.about_version.setObjectName("h1")
        self.about_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.about_right_layout.addWidget(self.about_version)

        self.about_right_layout.addStretch()

        if app_fullscreen:
            self.showFullScreen()
        else:
            self.show()

    def check_mqtt_connection(self):
        if self.client.state == mqtt.MqttClient.Connected:
            if self.root_widget.currentIndex() != ABOUT_PAGE_INDEX:
                self.root_widget.setCurrentIndex(CONTROL_WIDGET_INDEX)
            return
        elif self.client.state == mqtt.MqttClient.Connecting:
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Attempts: {self.connection_attempts}")
            self.root_widget.setCurrentIndex(CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1
        elif self.client.state == mqtt.MqttClient.ConnectError:
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Failed: {self.client.result_code}")
            self.root_widget.setCurrentIndex(CONNECTION_WIDGET_INDEX)
            self.connection_attempts += 1
        else:
            self.client.connectToHost()
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Attempts: {self.connection_attempts}")
            self.root_widget.setCurrentIndex(CONNECTION_WIDGET_INDEX)
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
                else:
                    animation_name = "Unknown"
                self.current_animation.setText(f"Current Animation: {animation_name}")

            if "brightness" in data:
                self.control_brightness_slider.setValue(data["brightness"])
                self.brightness_known = BrightnessStates.KNOWN
                self.control_brightness_warning.setPixmap(
                    qta.icon("mdi6.check-circle", color="#66BB6A").pixmap(QSize(24, 24)))

    def toggle_led_power(self):
        if self.led_powered == PowerStates.ON:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(state_topic, "OFF")
        elif self.led_powered == PowerStates.OFF:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(state_topic, "ON")

    def update_brightness(self):
        self.brightness_known = BrightnessStates.UNKNOWN
        self.control_brightness_warning.setPixmap(qta.icon("mdi6.alert", color="#FDD835").pixmap(QSize(24, 24)))
        self.client.publish(brightness_topic, self.control_brightness_slider.value())

    def set_animation(self, name: str, _) -> None:
        self.animation_sidebar_frame.setEnabled(False)
        self.client.publish(animation_topic, ANIMATION_LIST[name])

    def show_about(self):
        self.root_widget.setCurrentIndex(ABOUT_PAGE_INDEX)


class AnimationWidget(QFrame):
    def __init__(self, title: str = "Animation"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumWidth(160)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.icon = QLabel()
        self.icon.setPixmap(qta.icon("mdi6.auto-fix", color="#FFEE58").pixmap(72, 72))
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon)

        self.title = QLabel(title)
        self.title.setObjectName("h3")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qta.dark(app)

    with open("style.qss", "r", encoding="utf-8") as qss:
        app.setStyleSheet(qdarktheme.load_stylesheet() + "\n" + qss.read())
    QFontDatabase.addApplicationFont("assets/fonts/Cabin/static/Cabin-Regular.ttf")

    win = MainWindow()
    sys.exit(app.exec())
