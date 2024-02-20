import random
import sys

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import qdarktheme

import mqtt

BROKER_ADDRESS = "pilight.lan"
BROKER_PORT = 1883
client_id = f'publish-{random.randint(0, 1000)}'

CONNECTION_WIDGET_INDEX = 0
CONTROL_WIDGET_INDEX = 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.client = mqtt.MqttClient()
        self.client.hostname = BROKER_ADDRESS
        self.client.port = BROKER_PORT

        self.connection_attempts = 1

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r", encoding="utf-8") as qss:
        app.setStyleSheet(qdarktheme.load_stylesheet() + "\n" + qss.read())
    QFontDatabase.addApplicationFont("assets/fonts/Cabin/static/Cabin-Regular.ttf")

    win = MainWindow()
    sys.exit(app.exec())
