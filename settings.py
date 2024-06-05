"""
QSettings Loader for NeoPixelAnimatorGUI
"""

from qtpy.QtCore import QSettings

from loguru import logger

class SettingsManager:
    def __init__(self) -> None:
        self.qsettings = QSettings("meowmeowahr", "NeoPixelAnimatorGUI")
        logger.info(f"Initialized QSettings store at directory {self.qsettings.fileName()}")

    @property
    def mqtt_host(self) -> str:
        return self.qsettings.value("mqtt/host", "localhost", str) # type: ignore
    
    @mqtt_host.setter
    def mqtt_host(self, new_value: str):
        self.qsettings.setValue("mqtt/host", new_value)
        logger.info(f"Set value of mqtt/host to {new_value}")

    def set_mqtt_host(self, new_value: str):
        self.mqtt_host = new_value

    @property
    def mqtt_port(self) -> int:
        return self.qsettings.value("mqtt/host", 1883, int) # type: ignore
    
    @mqtt_port.setter
    def mqtt_port(self, new_value: int):
        self.qsettings.setValue("mqtt/port", new_value)
        logger.info(f"Set value of mqtt/port to {new_value}")

    def set_mqtt_port(self, new_value: int):
        self.mqtt_port = new_value

    @property
    def data_request_topic(self) -> str:
        return self.qsettings.value("mqtt/topics/data_request_topic", "MQTTAnimator/data_request", str) # type: ignore
    
    @data_request_topic.setter
    def data_request_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/data_request_topic", new_value)
        logger.info(f"Set value of mqtt/topics/data_request_topic to {new_value}")

    def set_data_request_topic(self, new_value: str):
        self.data_request_topic = new_value

    @property
    def return_data_request_topic(self) -> str:
        return self.qsettings.value("mqtt/topics/return_data_request_topic", "MQTTAnimator/rdata_request", str) # type: ignore
    
    @return_data_request_topic.setter
    def return_data_request_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_data_request_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_data_request_topic to {new_value}")

    def set_return_data_request_topic(self, new_value: str):
        self.return_data_request_topic = new_value

    @property
    def state_topic(self) -> str:
        return self.qsettings.value("mqtt/topics/state_topic", "MQTTAnimator/state", str) # type: ignore

    @state_topic.setter
    def state_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/state_topic", new_value)
        logger.info(f"Set value of mqtt/topics/state_topic to {new_value}")

    def set_state_topic(self, new_value: str):
        self.state_topic = new_value

