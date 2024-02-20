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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.client = mqtt.MqttClient()
        self.client.hostname = BROKER_ADDRESS
        self.client.port = BROKER_PORT

        self.connection_attempts = 0

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

        self.show()

    def check_mqtt_connection(self):
        self.connection_attempts += 1
        if self.client.state == mqtt.MqttClient.Connected:
            self.connection_timer.stop()
        elif self.client.state == mqtt.MqttClient.Connecting:
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Attempts: {self.connection_attempts}")
        elif self.client.state == mqtt.MqttClient.ConnectError:
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Failed: {self.client.result_code}")
        else:
            self.client.connectToHost()
            self.connection_timer.start()
            self.connection_attempts_label.setText(f"Connection Attempts: {self.connection_attempts}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r", encoding="utf-8") as qss:
        app.setStyleSheet(qdarktheme.load_stylesheet() + "\n" + qss.read())
    QFontDatabase.addApplicationFont("assets/fonts/Cabin/static/Cabin-Regular.ttf")

    win = MainWindow()
    sys.exit(app.exec())
