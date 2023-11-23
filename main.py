import PyQt5
import sys

import snippingwindow


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    screens = app.screens()
    window = snippingwindow.Snip2TextWindow()
    sys.exit(app.exec_())

