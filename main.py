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

CONNECTION_WIDGET_INDEX = 0
CONTROL_WIDGET_INDEX = 1


class PowerStates(enum.Enum):
    OFF = 0
    ON = 1
    UNKNOWN = 2


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

        self.setWindowTitle("NeoPixel Animator Client")

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

        self.control_layout = QHBoxLayout()
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

    def toggle_led_power(self):
        if self.led_powered == PowerStates.ON:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(STATE_TOPIC, "OFF")
        elif self.led_powered == PowerStates.OFF:
            self.led_powered = PowerStates.UNKNOWN
            self.control_power.setIcon(qta.icon("mdi6.power", color="#9EA7AA"))
            self.client.publish(STATE_TOPIC, "ON")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r", encoding="utf-8") as qss:
        app.setStyleSheet(qdarktheme.load_stylesheet() + "\n" + qss.read())
    QFontDatabase.addApplicationFont("assets/fonts/Cabin/static/Cabin-Regular.ttf")

    win = MainWindow()
    sys.exit(app.exec())
