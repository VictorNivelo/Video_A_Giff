import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QFileDialog,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSlider,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QAction,
    QMenu,
    QDialog,
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon, QFont

DEFAULT_VIDEO_FOLDER = os.path.join(os.path.expanduser("~"), "Videos")
DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Ajustes")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        input_folder_layout = QHBoxLayout()
        self.input_folder_edit = QLineEdit(
            self.settings.value("input_folder", DEFAULT_VIDEO_FOLDER)
        )
        input_folder_btn = QPushButton("Carpeta de Origen", self)
        input_folder_btn.clicked.connect(self.select_input_folder)
        input_folder_layout.addWidget(QLabel("Carpeta de origen:"))
        input_folder_layout.addWidget(self.input_folder_edit)
        input_folder_layout.addWidget(input_folder_btn)
        layout.addLayout(input_folder_layout)
        output_folder_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit(
            self.settings.value("output_folder", DEFAULT_DOWNLOAD_FOLDER)
        )
        output_folder_btn = QPushButton("Carpeta de Destino", self)
        output_folder_btn.clicked.connect(self.select_output_folder)
        output_folder_layout.addWidget(QLabel("Carpeta de destino:"))
        output_folder_layout.addWidget(self.output_folder_edit)
        output_folder_layout.addWidget(output_folder_btn)
        layout.addLayout(output_folder_layout)
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar", self)
        cancel_btn = QPushButton("Cancelar", self)
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Origen", self.input_folder_edit.text()
        )
        if folder:
            self.input_folder_edit.setText(folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Destino", self.output_folder_edit.text()
        )
        if folder:
            self.output_folder_edit.setText(folder)


class VideoToGifConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.settings = QSettings("VideoToGif", "Converter")
        self.config_file = "Configuraciones/Ajustes.json"
        self.dark_mode = self.settings.value("dark_mode", True, type=bool)
        if not self.settings.contains("input_folder"):
            self.settings.setValue("input_folder", DEFAULT_VIDEO_FOLDER)
        if not self.settings.contains("output_folder"):
            self.settings.setValue("output_folder", DEFAULT_DOWNLOAD_FOLDER)
        self.load_settings()
        self.initUI()
        self.apply_theme()

    def initUI(self):
        self.setWindowTitle("Conversor Profesional de Video a GIF")
        self.setMinimumSize(600, 500)
        menubar = self.menuBar()
        theme_menu = menubar.addMenu("Tema")
        settings_menu = menubar.addMenu("Ajustes")
        self.dark_action = QAction("Modo Oscuro", self, checkable=True)
        self.light_action = QAction("Modo Claro", self, checkable=True)
        settings_action = QAction("Configurar carpetas", self)
        theme_menu.addAction(self.dark_action)
        theme_menu.addAction(self.light_action)
        settings_menu.addAction(settings_action)
        self.dark_action.triggered.connect(lambda: self.change_theme(True))
        self.light_action.triggered.connect(lambda: self.change_theme(False))
        settings_action.triggered.connect(self.show_settings_dialog)
        if self.dark_mode:
            self.dark_action.setChecked(True)
        else:
            self.light_action.setChecked(True)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        self.select_btn = QPushButton("Seleccionar Video", self)
        self.select_btn.clicked.connect(self.select_video)
        layout.addWidget(self.select_btn)
        self.file_label = QLabel("Ningún archivo seleccionado", self)
        layout.addWidget(self.file_label)
        options_layout = QVBoxLayout()
        fps_layout = QHBoxLayout()
        fps_label = QLabel("FPS:", self)
        self.fps_spin = QSpinBox(self)
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(self.fps)
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_spin)
        options_layout.addLayout(fps_layout)
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Calidad:", self)
        self.quality_slider = QSlider(Qt.Horizontal, self)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(self.quality)
        self.quality_value = QLabel(str(self.quality), self)
        self.quality_slider.valueChanged.connect(
            lambda: self.quality_value.setText(str(self.quality_slider.value()))
        )
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value)
        options_layout.addLayout(quality_layout)
        size_layout = QHBoxLayout()
        size_label = QLabel("Tamaño:", self)
        self.size_combo = QComboBox(self)
        self.size_combo.addItems(["Original", "720p", "480p", "360p"])
        self.size_combo.setCurrentText(self.size)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        options_layout.addLayout(size_layout)
        layout.addLayout(options_layout)
        self.convert_btn = QPushButton("Convertir a GIF", self)
        self.convert_btn.clicked.connect(self.convert_to_gif)
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)
        self.status_label = QLabel("", self)
        layout.addWidget(self.status_label)

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.settings.setValue("input_folder", dialog.input_folder_edit.text())
            self.settings.setValue("output_folder", dialog.output_folder_edit.text())
            self.save_settings()

    def load_settings(self):
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
                self.fps = config.get("fps", 15)
                self.quality = config.get("quality", 95)
                self.size = config.get("size", "Original")
        except:
            self.fps = int(self.settings.value("fps", 15))
            self.quality = int(self.settings.value("quality", 95))
            self.size = self.settings.value("size", "Original")

    def save_settings(self):
        config = {
            "fps": self.fps_spin.value(),
            "quality": self.quality_slider.value(),
            "size": self.size_combo.currentText(),
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f)
        self.settings.setValue("fps", config["fps"])
        self.settings.setValue("quality", config["quality"])
        self.settings.setValue("size", config["size"])

    def change_theme(self, dark_mode):
        self.dark_mode = dark_mode
        self.dark_action.setChecked(dark_mode)
        self.light_action.setChecked(not dark_mode)
        self.settings.setValue("dark_mode", dark_mode)
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(
                """
               QMainWindow, QWidget { background-color: #1e1e2e; color: #cdd6f4; }
               QPushButton {
                   background-color: #89b4fa;
                   color: #1e1e2e;
                   border: none;
                   padding: 10px;
                   border-radius: 4px;
                   font-size: 14px;
                   font-weight: bold;
                   margin: 5px;
               }
               QPushButton:hover { background-color: #b4befe; }
               QPushButton:disabled { background-color: #6c7086; color: #11111b; }
               QLabel { font-size: 14px; margin: 5px; color: #cdd6f4; }
               QSpinBox, QComboBox, QLineEdit {
                   padding: 8px;
                   border: 2px solid #89b4fa;
                   border-radius: 4px;
                   background-color: #313244;
                   color: #cdd6f4;
                   margin: 5px;
                   selection-background-color: #89b4fa;
               }
               QSlider::groove:horizontal {
                   border: 1px solid #89b4fa;
                   height: 8px;
                   background: #313244;
                   margin: 2px 0;
                   border-radius: 4px;
               }
               QSlider::handle:horizontal {
                   background: #89b4fa;
                   border: 1px solid #89b4fa;
                   width: 18px;
                   margin: -2px 0;
                   border-radius: 9px;
               }
               QMenuBar {
                   background-color: #1e1e2e;
                   color: #cdd6f4;
               }
               QMenuBar::item:selected { background-color: #313244; }
               QMenu {
                   background-color: #1e1e2e;
                   color: #cdd6f4;
               }
               QMenu::item:selected { background-color: #313244; }
           """
            )
        else:
            self.setStyleSheet(
                """
               QMainWindow, QWidget { background-color: #ffffff; color: #333333; }
               QPushButton {
                   background-color: #2196F3;
                   color: white;
                   border: none;
                   padding: 10px;
                   border-radius: 4px;
                   font-size: 14px;
                   font-weight: bold;
                   margin: 5px;
               }
               QPushButton:hover { background-color: #1976D2; }
               QPushButton:disabled { background-color: #BDBDBD; }
               QLabel { font-size: 14px; margin: 5px; color: #333333; }
               QSpinBox, QComboBox, QLineEdit {
                   padding: 8px;
                   border: 2px solid #2196F3;
                   border-radius: 4px;
                   background-color: white;
                   color: #333333;
                   margin: 5px;
                   selection-background-color: #2196F3;
               }
               QSlider::groove:horizontal {
                   border: 1px solid #2196F3;
                   height: 8px;
                   background: #E3F2FD;
                   margin: 2px 0;
                   border-radius: 4px;
               }
               QSlider::handle:horizontal {
                   background: #2196F3;
                   border: 1px solid #2196F3;
                   width: 18px;
                   margin: -2px 0;
                   border-radius: 9px;
               }
               QMenuBar {
                   background-color: #ffffff;
                   color: #333333;
               }
               QMenuBar::item:selected { background-color: #E3F2FD; }
               QMenu {
                   background-color: #ffffff;
                   color: #333333;
               }
               QMenu::item:selected { background-color: #E3F2FD; }
           """
            )

    def select_video(self):
        input_folder = self.settings.value("input_folder", "")
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Video",
            input_folder,
            "Video Files (*.mp4 *.avi *.mov *.wmv)",
        )
        if file_name:
            self.video_path = file_name
            self.file_label.setText(
                f"Archivo seleccionado: {os.path.basename(file_name)}"
            )
            self.convert_btn.setEnabled(True)

    def convert_to_gif(self):
        if not self.video_path:
            QMessageBox.warning(self, "Error", "Por favor seleccione un video primero.")
            return
        output_folder = self.settings.value("output_folder", "")
        if not output_folder:
            QMessageBox.warning(
                self, "Error", "Por favor configure la carpeta de destino en Ajustes."
            )
            return
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"No se pudo crear la carpeta de destino: {str(e)}"
                )
                return
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        output_path = os.path.join(output_folder, f"{base_name}.gif")
        try:
            self.status_label.setText("Convirtiendo...")
            QApplication.processEvents()
            from moviepy.editor import VideoFileClip

            clip = VideoFileClip(self.video_path)
            fps = self.fps_spin.value()
            size_option = self.size_combo.currentText()
            if size_option != "Original":
                height = int(size_option.replace("p", ""))
                clip = clip.resize(height=height)
            clip.write_gif(
                output_path,
                fps=fps,
                program="ffmpeg",
                opt="OptimizePlus",
                fuzz=self.quality_slider.value(),
            )
            self.status_label.setText("¡Conversión completada!")
            clip.close()
            self.save_settings()
            QMessageBox.information(self, "Éxito", f"GIF guardado como: {output_path}")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error durante la conversión: {str(e)}"
            )
            self.status_label.setText(f"Error: {str(e)}")


def main():
    app = QApplication(sys.argv)
    ex = VideoToGifConverter()
    ex.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
