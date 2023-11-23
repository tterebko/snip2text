import mss
import tkinter as tk

from PIL import ImageGrab, Image
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt


class SnippingWidget(QtWidgets.QWidget):
    def __init__(self, callback):
        super(SnippingWidget, self).__init__()

        self.callback = callback
        self.is_snipping = False
        self.is_multiple_screens = False

        self.setWindowTitle('snip2text')
        self.setWindowIcon(QtGui.QIcon('res/logo64.png'))
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        root = tk.Tk()
        g = self.get_geometry(root)
        self.setGeometry(*g)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.abs_begin = QtCore.QPoint()
        self.abs_end = QtCore.QPoint()

    def get_geometry(self, tkinter: tk.Tk):
        screens = QtGui.QGuiApplication.screens()

        if len(screens) == 1:
            return 0, 0, tkinter.winfo_screenwidth(), tkinter.winfo_screenheight()

        self.is_multiple_screens = True
        x_min = y_min = +100_000
        x_max = y_max = -100_000
        for s in screens:
            g = s.geometry()
            x_min = min(x_min, g.x())
            y_min = min(y_min, g.y())
            x_max = max(x_max, g.x() + g.width())
            y_max = max(y_max, g.y() + g.height())
        return x_min, y_min, x_max - x_min, y_max - y_min

    def start(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.is_snipping = True
        self.setWindowOpacity(0.3)
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.show()

    def stop(self):
        self.close()

    def paintEvent(self, event):
        if self.is_snipping:
            brush_color = (128, 128, 255, 100)
            lw = 3
            opacity = 0.3
        else:
            # reset points, so the rectangle won't show up again.
            self.begin = QtCore.QPoint()
            self.end = QtCore.QPoint()
            brush_color = (0, 0, 0, 0)
            lw = 0
            opacity = 0

        self.setWindowOpacity(opacity)
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), lw))
        qp.setBrush(QtGui.QColor(*brush_color))
        rect = QtCore.QRectF(self.begin, self.end)
        qp.drawRect(rect)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.abs_begin = QtGui.QCursor.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        p1, p2 = self.abs_begin, QtGui.QCursor.pos()
        self.is_snipping = False

        QtWidgets.QApplication.restoreOverrideCursor()
        self.repaint()
        QtWidgets.QApplication.processEvents()

        bbox = (min(p1.x(), p2.x()), min(p1.y(), p2.y()), max(p1.x(), p2.x()), max(p1.y(), p2.y()))
        if self.is_multiple_screens:
            with mss.mss() as sct:
                sct_img = sct.grab(bbox)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        else:
            img = ImageGrab.grab(bbox=bbox)
        QtWidgets.QApplication.processEvents()
        self.callback(img)
