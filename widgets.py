from qtpy.QtWidgets import QFrame


def rgb_to_hex(rgb):
    return '%02x%02x%02x' % tuple(rgb)


class ColorBlock(QFrame):
    """
    A simple widget ot show a single color
    """

    def __init__(self) -> None:
        super(ColorBlock, self).__init__()

        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumWidth(64)
        self.setMinimumHeight(64)

        self.setMaximumSize(128, 128)

    def setColor(self, color: str) -> None:
        """
        Sets the color of the widget
        """
        self.setStyleSheet(f"background-color: {color};")

    def setRGB(self, rgb):
        """
        Sets the color of the widget in (r, g, b)
        """
        color_str = rgb_to_hex(rgb)
        self.setStyleSheet(f"background-color: #{color_str};")
