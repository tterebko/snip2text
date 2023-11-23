import cv2
import numpy as np
import PIL

from PyQt5 import QtWidgets, QtCore, QtGui
from typing import Optional

import recognition
import snippingtool
import translation


class Snip2TextWindow(QtWidgets.QMainWindow):
	FONT_SIZES = [10, 12, 16, 24, 36, 48]
	MAIN_DEFAULT_FONT_SIZE = 24
	SUBS_DEFAULT_FONT_SIZE = 12
	MENU_FONT_ACTIONS = ['Recognized Text', 'Spelling', 'Translation']
	TEXT_WIDGETS = ['qteRecognizedTextWidget', 'qteSpellingTextWidget', 'qteTranslatedTextWidget']
	SNIP_WIDGET = 'qlSnippedImage'
	SAMPLE_TEXTS = ['你好，世界！', 'Nǐ hǎo, shìjiè!', 'Hello, World!']

	def __init__(self, start_position=(300, 300, 350, 250)):
		super().__init__()

		self.pil_image: Optional[PIL.Image.Image] = None
		self.image: Optional[QtGui.QPixmap] = None
		self.snipping_tool: Optional[snippingtool.SnippingWidget] = None
		self.translate_automatically: bool = True

		self.start_position = start_position

		self.name2widget = dict(zip(self.MENU_FONT_ACTIONS, self.TEXT_WIDGETS))
		self.widget2size = dict(
			zip(self.TEXT_WIDGETS, [self.MAIN_DEFAULT_FONT_SIZE] + [self.SUBS_DEFAULT_FONT_SIZE] * 2))

		self.ui_components()

	def ui_components(self) -> None:
		self.setWindowIcon(QtGui.QIcon('res/logo64.png'))
		toolbar = self.menuBar()

		# Window content
		central_widget = QtWidgets.QWidget(self)
		layout = QtWidgets.QVBoxLayout(central_widget)

		for i, w in enumerate([QtWidgets.QTextEdit(objectName=name) for name in self.TEXT_WIDGETS]):
			self.set_font_size(w, self.widget2size[w.objectName()])
			w.setText(self.SAMPLE_TEXTS[i])
			layout.addWidget(w)

		snipped_image_widget = QtWidgets.QLabel(objectName=self.SNIP_WIDGET)
		snipped_image_widget.setAlignment(QtCore.Qt.AlignCenter)
		layout.addWidget(snipped_image_widget)
		snipped_image_widget.hide()

		self.setCentralWidget(central_widget)
		self.setGeometry(*self.start_position)
		self.setWindowTitle('snip2text')

		# Menu
		toolbar.addAction('&New', self.new_snip)
		toolbar.addAction('&Translate', self.translate)
		settings_action = toolbar.addMenu('&Settings')
		toolbar.addAction('&Exit', self.close)

		# Menu | Settings | Translate to language
		languages_action = settings_action.addMenu('&Language')
		chinese_language = languages_action.addAction('Chinese and English')
		chinese_language.setCheckable(True)
		chinese_language.setChecked(True)
		chinese_language.setEnabled(False)
		settings_action.addSeparator()

		# Menu | Settings | Translate automatically
		auto_translate_action = settings_action.addAction('Immediate &Translation', self.translate_automatically_changed)
		auto_translate_action.setCheckable(True)
		auto_translate_action.setChecked(self.translate_automatically)
		settings_action.addSeparator()

		# Menu | Settings | Fonts
		font_sizes_action = settings_action.addMenu('&Font Sizes')
		for menu_name in self.MENU_FONT_ACTIONS:
			font_action = font_sizes_action.addMenu('&' + menu_name)
			action_group = QtWidgets.QActionGroup(self)
			for size in self.FONT_SIZES:
				action = font_action.addAction(str(size))
				action.triggered.connect(lambda _, n=menu_name, s=size: self.change_font_size(self.name2widget[n], s))
				action_group.addAction(action)
				action.setCheckable(True)
				action.setChecked(self.widget2size[self.name2widget[menu_name]] == size)

		# Menu | Settings | Show Snipped image
		show_snip_action = settings_action.addAction('&Show Snip')
		show_snip_action.triggered.connect(lambda value, s=snipped_image_widget: s.show() if value else s.hide())
		show_snip_action.setCheckable(True)
		show_snip_action.setChecked(False)

		self.show()

	def new_snip(self) -> None:
		self.hide()
		self.snipping_tool = snippingtool.SnippingWidget(self)
		self.snipping_tool.start()

	def recognize(self) -> None:
		text_edit_widget = self.findChild(QtWidgets.QTextEdit, self.TEXT_WIDGETS[0])
		text_edit_widget.setText('In progress...')
		QtWidgets.QApplication.processEvents()

		res = recognition.engine.ocr(img_fp=self.pil_image)
		text_edit_widget.setText(' '.join([r['text'] for r in res]))
		QtWidgets.QApplication.processEvents()

	def translate(self) -> None:
		text = self.findChild(QtWidgets.QTextEdit, self.TEXT_WIDGETS[0]).toPlainText()
		spelling_widget = self.findChild(QtWidgets.QTextEdit, self.TEXT_WIDGETS[1])
		translate_widget = self.findChild(QtWidgets.QTextEdit, self.TEXT_WIDGETS[2])
		spelling_widget.setText('In progress...')
		translate_widget.setText('In progress...')
		QtWidgets.QApplication.processEvents()

		spelling_widget.setText(translation.get_spelling(text))
		translate_widget.setText(translation.get_translation(text))

	def render_image(self) -> None:
		if self.image:
			snipped_image = self.findChild(QtWidgets.QLabel, self.SNIP_WIDGET)
			snipped_image.setFixedHeight(min(self.height() // 4, self.image.height()))

			w, h = snipped_image.width(), snipped_image.height()
			snipped_image.setPixmap(self.image.scaled(w, h, QtCore.Qt.KeepAspectRatio))

	def change_font_size(self, widget_name: str, size: int) -> None:
		self.set_font_size(self.findChild(QtWidgets.QTextEdit, widget_name), size)

	def __call__(self, image: PIL.Image.Image) -> None:
		self.pil_image = image
		self.image = Snip2TextWindow.convert_pil_img_to_qpixmap(image)
		self.render_image()
		if self.snipping_tool:
			self.snipping_tool.stop()
		for name in self.TEXT_WIDGETS:
			self.findChild(QtWidgets.QTextEdit, name).setText('')
		self.show()
		self.update()

		self.recognize()
		if self.translate_automatically:
			self.translate()

	def resizeEvent(self, a0: Optional[QtGui.QResizeEvent]) -> None:
		self.render_image()

	def translate_automatically_changed(self, value: bool) -> None:
		self.translate_automatically = value

	@staticmethod
	def set_font_size(widget: QtWidgets.QWidget, font_size: int) -> None:
		font = QtGui.QFont()
		font.setPointSize(font_size)
		widget.setFont(font)

	@staticmethod
	def convert_pil_img_to_numpy_img(pil_img: PIL.Image.Image):
		return cv2.cvtColor(np.array(pil_img), cv2.COLOR_BGR2RGB)

	@staticmethod
	def convert_pil_img_to_qpixmap(image: PIL.Image.Image) -> QtGui.QPixmap:
		np_img = Snip2TextWindow.convert_pil_img_to_numpy_img(image)
		height, width, channel = np_img.shape
		bytes_per_line = 3 * width
		img = QtGui.QImage(np_img.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888).rgbSwapped()
		return QtGui.QPixmap(img)
