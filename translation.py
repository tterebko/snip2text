import argostranslate.package
import argostranslate.translate
import pinyin

from_code = 'zh'
to_code = 'en'

# Download and install Argos Translate package
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(filter(lambda x: x.from_code == from_code and x.to_code == to_code, available_packages))
argostranslate.package.install_from_path(package_to_install.download())


def get_spelling(text: str) -> str:
	return pinyin.get(text, delimiter=' ')


def get_translation(text: str) -> str:
	return argostranslate.translate.translate(text, from_code, to_code)

