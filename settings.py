from qtpy.QtCore import QSettings
from loguru import logger


class SettingsManager:
    def __init__(self) -> None:
        self.qsettings = QSettings("meowmeowahr", "NeoPixelAnimatorGUI")
        logger.info(f"Initialized QSettings store at directory {self.qsettings.fileName()}")

    @property
    def mqtt_host(self) -> str:
        value = self.qsettings.value("mqtt/host", "localhost", str)  # type: ignore
        return value if value else "localhost"

    @mqtt_host.setter
    def mqtt_host(self, new_value: str):
        self.qsettings.setValue("mqtt/host", new_value)
        logger.info(f"Set value of mqtt/host to {new_value}")

    def set_mqtt_host(self, new_value: str):
        self.mqtt_host = new_value

    @property
    def mqtt_port(self) -> int:
        return self.qsettings.value("mqtt/port", 1883, int)  # type: ignore

    @mqtt_port.setter
    def mqtt_port(self, new_value: int):
        self.qsettings.setValue("mqtt/port", new_value)
        logger.info(f"Set value of mqtt/port to {new_value}")

    def set_mqtt_port(self, new_value: int):
        self.mqtt_port = new_value

    @property
    def data_request_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/data_request_topic", "MQTTAnimator/data_request", str)  # type: ignore
        return value if value else "MQTTAnimator/data_request"

    @data_request_topic.setter
    def data_request_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/data_request_topic", new_value)
        logger.info(f"Set value of mqtt/topics/data_request_topic to {new_value}")

    def set_data_request_topic(self, new_value: str):
        self.data_request_topic = new_value

    @property
    def return_data_request_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/return_data_request_topic", "MQTTAnimator/rdata_request",
                                     str)  # type: ignore
        return value if value else "MQTTAnimator/rdata_request"

    @return_data_request_topic.setter
    def return_data_request_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_data_request_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_data_request_topic to {new_value}")

    def set_return_data_request_topic(self, new_value: str):
        self.return_data_request_topic = new_value

    @property
    def state_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/state_topic", "MQTTAnimator/state", str)  # type: ignore
        return value if value else "MQTTAnimator/state"

    @state_topic.setter
    def state_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/state_topic", new_value)
        logger.info(f"Set value of mqtt/topics/state_topic to {new_value}")

    def set_state_topic(self, new_value: str):
        self.state_topic = new_value

    @property
    def return_state_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/return_state_topic", "MQTTAnimator/rstate", str)  # type: ignore
        return value if value else "MQTTAnimator/rstate"

    @return_state_topic.setter
    def return_state_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_state_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_state_topic to {new_value}")

    def set_return_state_topic(self, new_value: str):
        self.return_state_topic = new_value

    @property
    def brightness_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/brightness_topic", "MQTTAnimator/brightness", str)  # type: ignore
        return value if value else "MQTTAnimator/brightness"

    @brightness_topic.setter
    def brightness_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/brightness_topic", new_value)
        logger.info(f"Set value of mqtt/topics/brightness_topic to {new_value}")

    def set_brightness_topic(self, new_value: str):
        self.brightness_topic = new_value

    @property
    def return_brightness_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/return_brightness_topic", "MQTTAnimator/rbrightness",
                                     str)  # type: ignore
        return value if value else "MQTTAnimator/rbrightness"

    @return_brightness_topic.setter
    def return_brightness_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_brightness_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_brightness_topic to {new_value}")

    def set_return_brightness_topic(self, new_value: str):
        self.return_brightness_topic = new_value

    @property
    def args_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/args_topic", "MQTTAnimator/args", str)  # type: ignore
        return value if value else "MQTTAnimator/args"

    @args_topic.setter
    def args_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/args_topic", new_value)
        logger.info(f"Set value of mqtt/topics/args_topic to {new_value}")

    def set_args_topic(self, new_value: str):
        self.args_topic = new_value

    @property
    def animation_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/animation_topic", "MQTTAnimator/animation", str)  # type: ignore
        return value if value else "MQTTAnimator/animation"

    @animation_topic.setter
    def animation_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/animation_topic", new_value)
        logger.info(f"Set value of mqtt/topics/animation_topic to {new_value}")

    def set_animation_topic(self, new_value: str):
        self.animation_topic = new_value

    @property
    def return_anim_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/return_anim_topic", "MQTTAnimator/ranimation", str)  # type: ignore
        return value if value else "MQTTAnimator/ranimation"

    @return_anim_topic.setter
    def return_anim_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_anim_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_anim_topic to {new_value}")

    def set_return_anim_topic(self, new_value: str):
        self.return_anim_topic = new_value
