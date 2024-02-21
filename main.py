import enum
import json
import random
import sys

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import qdarktheme
import qtawesome as qta

import mqtt

BROKER_ADDRESS = "pilight.lan"
BROKER_PORT = 1883
client_id = f'publish-{random.randint(0, 1000)}'

DR_TOPIC = "MQTTAnimator/data_request"
RDR_TOPIC = "MQTTAnimator/rdata_request"
STATE_TOPIC = "MQTTAnimator/state"
RSTATE_TOPIC = "MQTTAnimator/rstate"
BRIGHT_TOPIC = "MQTTAnimator/brightness"
RBRIGHT_TOPIC = "MQTTAnimator/rbrightness"

CONNECTION_WIDGET_INDEX = 0
CONTROL_WIDGET_INDEX = 1


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
        self.client.hostname = BROKER_ADDRESS
        self.client.port = BROKER_PORT

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

        self.control_title = QLabel("NeoPixel Animator")
        self.control_title.setObjectName("h2")
        self.control_top_bar.addWidget(self.control_title)

        self.control_top_bar.addStretch()

        self.control_power = QPushButton()
        self.control_power.setFlat(True)
        self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
        self.control_power.setIconSize(QSize(48, 48))
        self.control_power.clicked.connect(self.toggle_led_power)
        self.control_top_bar.addWidget(self.control_power)

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

        self.control_animatior_scroll = QScrollArea()
        self.control_animatior_scroll.setWidgetResizable(True)
        self.control_layout.addWidget(self.control_animatior_scroll)

        self.control_animator_widget = QWidget()
        self.control_animatior_scroll.setWidget(self.control_animator_widget)

        self.control_animator_layout = QGridLayout()
        self.control_animator_widget.setLayout(self.control_animator_layout)

        self.test = AnimationWidget()
        self.control_animator_layout.addWidget(self.test, 0, 0)

        self.show()

    def check_mqtt_connection(self):
        if self.client.state == mqtt.MqttClient.Connected:
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
        self.client.subscribe(RSTATE_TOPIC)
        self.client.subscribe(RBRIGHT_TOPIC)
        self.client.subscribe(RDR_TOPIC)
        self.client.publish(DR_TOPIC, "request_type_full")

    def on_client_message(self, topic: str, payload: str):
        if topic == RSTATE_TOPIC:
            if payload == "ON":
                self.led_powered = PowerStates.ON
                self.control_power.setIcon(qta.icon("mdi6.power", color="#66BB6A"))
            else:
                self.led_powered = PowerStates.OFF
                self.control_power.setIcon(qta.icon("mdi6.power", color="#F44336"))
        if topic == RBRIGHT_TOPIC:
            self.brightness_known = BrightnessStates.KNOWN
            self.brightness_value = int(payload)
            self.control_brightness_warning.setPixmap(
                qta.icon("mdi6.check-circle", color="#66BB6A").pixmap(QSize(24, 24)))

        elif topic == RDR_TOPIC:
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

            if "brightness" in data:
                self.control_brightness_slider.setValue(data["brightness"])
                self.brightness_known = BrightnessStates.KNOWN
                self.control_brightness_warning.setPixmap(qta.icon("mdi6.check-circle", color="#66BB6A").pixmap(QSize(24, 24)))

    def toggle_led_power(self):
        if self.led_powered == PowerStates.ON:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(STATE_TOPIC, "OFF")
        elif self.led_powered == PowerStates.OFF:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(STATE_TOPIC, "ON")

    def update_brightness(self):
        self.brightness_known = BrightnessStates.UNKNOWN
        self.control_brightness_warning.setPixmap(qta.icon("mdi6.alert", color="#FDD835").pixmap(QSize(24, 24)))
        self.client.publish(BRIGHT_TOPIC, self.control_brightness_slider.value())


class AnimationWidget(QFrame):
    def __init__(self, title: str = "Animation"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.icon = QLabel()
        self.icon.setPixmap(qta.icon("mdi6.auto-fix",color="#FFEE58").pixmap(128, 128))
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon)

        self.title = QLabel(title)
        self.title.setObjectName("h3")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r", encoding="utf-8") as qss:
        app.setStyleSheet(qdarktheme.load_stylesheet() + "\n" + qss.read())
    QFontDatabase.addApplicationFont("assets/fonts/Cabin/static/Cabin-Regular.ttf")

    win = MainWindow()
    sys.exit(app.exec())
