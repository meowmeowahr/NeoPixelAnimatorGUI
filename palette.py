import functools

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import pyqtSignal as Signal

PALETTES = {
    # bokeh paired 12
    'paired12': ['#000000', '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00',
                 '#cab2d6', '#6a3d9a', '#ffff99', '#b15928', '#ffffff'],
    # d3 category 10
    'category10': ['#000000', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                   '#bcbd22', '#17becf', '#ffffff'],
    # 17 undertones https://lospec.com/palette-list/17undertones
    '17undertones': ['#000000', '#141923', '#414168', '#3a7fa7', '#35e3e3', '#8fd970', '#5ebb49', '#458352', '#dcd37b',
                     '#fffee5', '#ffd035', '#cc9245', '#a15c3e', '#a42f3b', '#f45b7a', '#c24998', '#81588d', '#bcb0c2',
                     '#ffffff'],
    # Kevinbot v3
    'kevinbot': [
        "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
        "#FF9900", "#9900FF", "#00FF99", "#990000", "#009900", "#000099",
        "#FFCC00", "#CC00FF", "#00FFCC", "#CC0000", "#00CC00", "#0000CC",
        "#FF6600", "#6600FF", "#00FF66", "#660000", "#006600", "#000066",
        "#FF3300", "#3300FF", "#00FF33", "#330000", "#003300", "#000033",
        "#FF6666", "#6666FF", "#66FF66", "#666666", "#FFCC99"
    ]
}


class _PaletteButton(QtWidgets.QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(42, 42))
        self.color = color
        self.setStyleSheet(
            "padding: 0px; background-color: "
            "qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 {0}, stop: 1 {0});".format(
                color))


class _PaletteBase(QtWidgets.QWidget):
    selected = Signal(object)

    def _emit_color(self, color):
        self.selected.emit(color)


class _PaletteLinearBase(_PaletteBase):
    # noinspection PyUnresolvedReferences
    def __init__(self, colors, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(colors, str):
            if colors in PALETTES:
                colors = PALETTES[colors]

        palette = self.layoutvh()

        for c in colors:
            b = _PaletteButton(c)
            b.pressed.connect(
                functools.partial(self._emit_color, c)
            )
            palette.addWidget(b)

        self.setLayout(palette)


class PaletteHorizontal(_PaletteLinearBase):
    layoutvh = QtWidgets.QHBoxLayout


class PaletteVertical(_PaletteLinearBase):
    layoutvh = QtWidgets.QVBoxLayout


class PaletteGrid(_PaletteBase):

    def __init__(self, colors, n_columns=7, size=42, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(colors, str):
            if colors in PALETTES:
                colors = PALETTES[colors]

        palette = QtWidgets.QGridLayout()
        row, col = 0, 0

        for c in colors:
            b = _PaletteButton(c)
            b.setFixedSize(size, size)
            b.pressed.connect(
                functools.partial(self._emit_color, c)
            )
            palette.addWidget(b, row, col)
            col += 1
            if col == n_columns:
                col = 0
                row += 1

        self.setLayout(palette)
