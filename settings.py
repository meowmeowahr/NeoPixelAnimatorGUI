from enum import Enum

from qtpy.QtCore import QSettings
from loguru import logger


class CursorSetting(Enum):
    DEFAULT = 0
    NONE = 1
    BLOB = 2

class SettingsManager:
    def __init__(self) -> None:
        self.qsettings = QSettings("meowmeowahr", "NeoPixelAnimatorGUI")
        logger.info(f"Initialized QSettings store at directory {self.qsettings.fileName()}")

    @property
    def mqtt_host(self) -> str:
        value = self.qsettings.value("mqtt/host", "localhost", str)  # type: ignore
        return value if value else "localhost" # type: ignore

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
        return value if value else "MQTTAnimator/data_request" # type: ignore

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
        return value if value else "MQTTAnimator/rdata_request" # type: ignore

    @return_data_request_topic.setter
    def return_data_request_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_data_request_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_data_request_topic to {new_value}")

    def set_return_data_request_topic(self, new_value: str):
        self.return_data_request_topic = new_value

    @property
    def state_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/state_topic", "MQTTAnimator/state", str)  # type: ignore
        return value if value else "MQTTAnimator/state" # type: ignore

    @state_topic.setter
    def state_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/state_topic", new_value)
        logger.info(f"Set value of mqtt/topics/state_topic to {new_value}")

    def set_state_topic(self, new_value: str):
        self.state_topic = new_value

    @property
    def return_state_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/return_state_topic", "MQTTAnimator/rstate", str)  # type: ignore
        return value if value else "MQTTAnimator/rstate" # type: ignore

    @return_state_topic.setter
    def return_state_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_state_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_state_topic to {new_value}")

    def set_return_state_topic(self, new_value: str):
        self.return_state_topic = new_value

    @property
    def brightness_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/brightness_topic", "MQTTAnimator/brightness", str)  # type: ignore
        return value if value else "MQTTAnimator/brightness" # type: ignore

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
        return value if value else "MQTTAnimator/rbrightness" # type: ignore

    @return_brightness_topic.setter
    def return_brightness_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_brightness_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_brightness_topic to {new_value}")

    def set_return_brightness_topic(self, new_value: str):
        self.return_brightness_topic = new_value

    @property
    def args_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/args_topic", "MQTTAnimator/args", str)  # type: ignore
        return value if value else "MQTTAnimator/args" # type: ignore

    @args_topic.setter
    def args_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/args_topic", new_value)
        logger.info(f"Set value of mqtt/topics/args_topic to {new_value}")

    def set_args_topic(self, new_value: str):
        self.args_topic = new_value

    @property
    def animation_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/animation_topic", "MQTTAnimator/animation", str)  # type: ignore
        return value if value else "MQTTAnimator/animation" # type: ignore

    @animation_topic.setter
    def animation_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/animation_topic", new_value)
        logger.info(f"Set value of mqtt/topics/animation_topic to {new_value}")

    def set_animation_topic(self, new_value: str):
        self.animation_topic = new_value

    @property
    def return_anim_topic(self) -> str:
        value = self.qsettings.value("mqtt/topics/return_anim_topic", "MQTTAnimator/ranimation", str)  # type: ignore
        return value if value else "MQTTAnimator/ranimation" # type: ignore

    @return_anim_topic.setter
    def return_anim_topic(self, new_value: str):
        self.qsettings.setValue("mqtt/topics/return_anim_topic", new_value)
        logger.info(f"Set value of mqtt/topics/return_anim_topic to {new_value}")

    def set_return_anim_topic(self, new_value: str):
        self.return_anim_topic = new_value

    @property
    def cursor_style(self) -> CursorSetting:
        value = self.qsettings.value("app/cursor", CursorSetting.DEFAULT.value, int)  # type: ignore
        return CursorSetting(value) if value else CursorSetting.DEFAULT # type: ignore

    @cursor_style.setter
    def cursor_style(self, new_value: CursorSetting):
        self.qsettings.setValue("app/cursor", new_value.value)
        logger.info(f"Set value of app/cursor to {new_value}")

    def set_cursor_style(self, new_value: CursorSetting):
        self.cursor_style = new_value

    @property
    def app_title(self) -> str:
        value = self.qsettings.value("app/title", "NeoPixel Animator", str)  # type: ignore
        return value if value else "NeoPixel Animator" # type: ignore

    @app_title.setter
    def app_title(self, new_value: str):
        self.qsettings.setValue("app/title", new_value)
        logger.info(f"Set value of app/title to {new_value}")

    def set_app_title(self, new_value: str):
        self.app_title = new_value

    @property
    def custom_theming(self) -> bool:
        value = self.qsettings.value("app/custom_theming", True, bool)  # type: ignore
        return value # type: ignore

    @custom_theming.setter
    def custom_theming(self, new_value: bool):
        self.qsettings.setValue("app/custom_theming", new_value)
        logger.info(f"Set value of app/custom_theming to {new_value}")

    def set_custom_theming(self, new_value: bool):
        self.custom_theming = new_value

    @property
    def dark_mode(self) -> bool:
        value = self.qsettings.value("app/dark_mode", True, bool)  # type: ignore
        return value # type: ignore

    @dark_mode.setter
    def dark_mode(self, new_value: bool):
        self.qsettings.setValue("app/dark_mode", new_value)
        logger.info(f"Set value of app/dark_mode to {new_value}")

    def set_dark_mode(self, new_value: bool):
        self.dark_mode = new_value

    @property
    def fullscreen(self) -> bool:
        value = self.qsettings.value("app/fullscreen", False, bool)  # type: ignore
        return value # type: ignore

    @fullscreen.setter
    def fullscreen(self, new_value: bool):
        self.qsettings.setValue("app/fullscreen", new_value)
        logger.info(f"Set value of app/fullscreen to {new_value}")

    def set_fullscreen(self, new_value: bool):
        self.fullscreen = new_value