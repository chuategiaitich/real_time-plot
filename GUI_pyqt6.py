# import sys
# import re
# import serial
# import threading
# from time import time
# from collections import defaultdict
# from PyQt6.QtCore import pyqtSignal, QObject, QTimer, Qt
# from PyQt6.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox,
#     QLabel, QScrollArea, QFrame
# )
# import pyqtgraph as pg


# class SerialReader(QObject):
#     new_data = pyqtSignal(str, float)  # label, value

#     def __init__(self, port="COM3", baudrate=115200):
#         super().__init__()
#         self.serial = serial.Serial(port, baudrate, timeout=1)
#         self.pattern = re.compile(r">(\w+):\s*(-?\d+\.?\d*)")
#         self.running = True

#     def read_loop(self):
#         while self.running:
#             try:
#                 line = self.serial.readline().decode("utf-8").strip()
#                 matches = self.pattern.findall(line)
#                 for label, value in matches:
#                     self.new_data.emit(label, float(value))
#             except Exception as e:
#                 print(f"Serial error: {e}")

#     def stop(self):
#         self.running = False
#         self.serial.close()


# class SerialPlotter(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Realtime Serial Plotter")
#         self.resize(800, 600)

#         self.layout = QVBoxLayout(self)
#         self.plotWidget = pg.PlotWidget()
#         self.plotWidget.showGrid(x=True, y=True)
#         self.layout.addWidget(self.plotWidget)

#         # Khu vực chứa checkboxes
#         self.checkboxFrame = QFrame()
#         self.checkboxLayout = QVBoxLayout(self.checkboxFrame)
#         self.checkboxScroll = QScrollArea()
#         self.checkboxScroll.setWidget(self.checkboxFrame)
#         self.checkboxScroll.setWidgetResizable(True)
#         self.layout.addWidget(QLabel("Toggle Plot Lines"))
#         self.layout.addWidget(self.checkboxScroll)

#         # Plot data và UI maps
#         self.data_buffers = defaultdict(lambda: {"x": [], "y": []})
#         self.curves = {}
#         self.checkboxes = {}

#         # Serial reader
#         self.reader = SerialReader()
#         self.reader.new_data.connect(self.handle_new_data)

#         # Thread cho serial
#         self.thread = threading.Thread(target=self.reader.read_loop)
#         self.thread.start()

#         # Timer update graph
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_plot)
#         self.timer.start(50)

#     def handle_new_data(self, label, value):
#         t = time()
#         buffer = self.data_buffers[label]
#         buffer["x"].append(t)
#         buffer["y"].append(value)
#         if len(buffer["x"]) > 1000:
#             buffer["x"] = buffer["x"][-1000:]
#             buffer["y"] = buffer["y"][-1000:]

#         if label not in self.curves:
#             self.add_curve(label)

#     def add_curve(self, label):
#         color = pg.intColor(len(self.curves))
#         self.curves[label] = self.plotWidget.plot([], [], pen=color, name=label)
#         checkbox = QCheckBox(label)
#         checkbox.setChecked(True)
#         checkbox.stateChanged.connect(lambda: self.toggle_curve(label))
#         self.checkboxes[label] = checkbox
#         self.checkboxLayout.addWidget(checkbox)

#     def toggle_curve(self, label):
#         visible = self.checkboxes[label].isChecked()
#         self.curves[label].setVisible(visible)

#     def update_plot(self):
#         for label, buffer in self.data_buffers.items():
#             if label in self.curves and self.checkboxes[label].isChecked():
#                 self.curves[label].setData(buffer["x"], buffer["y"])

#     def closeEvent(self, event):
#         self.reader.stop()
#         self.thread.join()
#         event.accept()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     win = SerialPlotter()
#     win.show()
#     sys.exit(app.exec())

import sys
import re
import serial
import serial.tools.list_ports
import threading
from time import time
from collections import defaultdict
from PyQt6.QtCore import pyqtSignal, QObject, QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox,
    QLabel, QScrollArea, QFrame, QComboBox, QGroupBox, QMessageBox
)
import pyqtgraph as pg


class SerialReader(QObject):
    new_data = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        self.serial = None
        self.running = False
        self.pattern = re.compile(r">(\w+):\s*(-?\d+\.?\d*)")

    def start(self, port, baudrate, parity, databits, stopbits):
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=parity,
                bytesize=databits,
                stopbits=stopbits,
                timeout=1
            )
            self.running = True
            threading.Thread(target=self.read_loop, daemon=True).start()
        except Exception as e:
            QMessageBox.critical(None, "Serial Error", f"Could not open serial port:\n{e}")

    def read_loop(self):
        while self.running and self.serial and self.serial.is_open:
            try:
                line = self.serial.readline().decode("utf-8").strip()
                matches = self.pattern.findall(line)
                for label, value in matches:
                    self.new_data.emit(label, float(value))
            except Exception:
                pass

    def stop(self):
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()


class SerialPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Realtime Serial Plotter")
        self.resize(1000, 600)

        main_layout = QVBoxLayout(self)
        self.plotWidget = pg.PlotWidget()
        self.plotWidget.showGrid(x=True, y=True)
        main_layout.addWidget(self.plotWidget)

        # Khu vực config và toggle
        config_toggle_layout = QHBoxLayout()
        main_layout.addLayout(config_toggle_layout)

        # --- Serial Config ---
        self.serialGroup = QGroupBox("Serial Config")
        config_layout = QVBoxLayout(self.serialGroup)
        self.portBox = QComboBox()
        self.baudBox = QComboBox()
        self.parityBox = QComboBox()
        self.databitsBox = QComboBox()
        self.stopbitsBox = QComboBox()

        self.refreshButton = QPushButton("Refresh Ports")
        self.connectButton = QPushButton("Connect")
        self.disconnectButton = QPushButton("Disconnect")

        config_layout.addWidget(QLabel("Port:"))
        config_layout.addWidget(self.portBox)
        config_layout.addWidget(self.refreshButton)
        config_layout.addWidget(QLabel("Baudrate:"))
        config_layout.addWidget(self.baudBox)
        config_layout.addWidget(QLabel("Parity:"))
        config_layout.addWidget(self.parityBox)
        config_layout.addWidget(QLabel("Data Bits:"))
        config_layout.addWidget(self.databitsBox)
        config_layout.addWidget(QLabel("Stop Bits:"))
        config_layout.addWidget(self.stopbitsBox)
        config_layout.addWidget(self.connectButton)
        config_layout.addWidget(self.disconnectButton)

        config_toggle_layout.addWidget(self.serialGroup)

        # --- Plot Toggles ---
        self.checkboxFrame = QFrame()
        self.checkboxLayout = QVBoxLayout(self.checkboxFrame)
        self.checkboxScroll = QScrollArea()
        self.checkboxScroll.setWidget(self.checkboxFrame)
        self.checkboxScroll.setWidgetResizable(True)

        checkbox_container = QVBoxLayout()
        checkbox_container.addWidget(QLabel("Toggle Plot Lines"))
        checkbox_container.addWidget(self.checkboxScroll)

        checkbox_widget = QWidget()
        checkbox_widget.setLayout(checkbox_container)
        config_toggle_layout.addWidget(checkbox_widget)

        # Plot data
        self.data_buffers = defaultdict(lambda: {"x": [], "y": []})
        self.curves = {}
        self.checkboxes = {}

        # Serial reader
        self.reader = SerialReader()
        self.reader.new_data.connect(self.handle_new_data)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

        # UI setup
        self.setup_ui()

    def setup_ui(self):
        self.refresh_ports()
        self.baudBox.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baudBox.setCurrentText("115200")

        self.parityBox.addItems(["None", "Even", "Odd"])
        self.databitsBox.addItems(["5", "6", "7", "8"])
        self.databitsBox.setCurrentText("8")
        self.stopbitsBox.addItems(["1", "1.5", "2"])

        self.refreshButton.clicked.connect(self.refresh_ports)
        self.connectButton.clicked.connect(self.connect_serial)
        self.disconnectButton.clicked.connect(self.disconnect_serial)

    def refresh_ports(self):
        self.portBox.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.portBox.addItems(ports)

    def connect_serial(self):
        port = self.portBox.currentText()
        baudrate = int(self.baudBox.currentText())
        parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD}
        parity = parity_map[self.parityBox.currentText()]
        databits = int(self.databitsBox.currentText())
        stopbits_map = {"1": serial.STOPBITS_ONE, "1.5": serial.STOPBITS_ONE_POINT_FIVE, "2": serial.STOPBITS_TWO}
        stopbits = stopbits_map[self.stopbitsBox.currentText()]

        self.reader.start(port, baudrate, parity, databits, stopbits)

    def disconnect_serial(self):
        self.reader.stop()

    def handle_new_data(self, label, value):
        t = time()
        buffer = self.data_buffers[label]
        buffer["x"].append(t)
        buffer["y"].append(value)
        if len(buffer["x"]) > 1000:
            buffer["x"] = buffer["x"][-1000:]
            buffer["y"] = buffer["y"][-1000:]

        if label not in self.curves:
            self.add_curve(label)

    def add_curve(self, label):
        color = pg.intColor(len(self.curves))
        self.curves[label] = self.plotWidget.plot([], [], pen=color, name=label)
        checkbox = QCheckBox(label)
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(lambda: self.toggle_curve(label))
        self.checkboxes[label] = checkbox
        self.checkboxLayout.addWidget(checkbox)

    def toggle_curve(self, label):
        visible = self.checkboxes[label].isChecked()
        self.curves[label].setVisible(visible)

    def update_plot(self):
        for label, buffer in self.data_buffers.items():
            if label in self.curves and self.checkboxes[label].isChecked():
                self.curves[label].setData(buffer["x"], buffer["y"])

    def closeEvent(self, event):
        self.reader.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SerialPlotter()
    win.show()
    sys.exit(app.exec())
