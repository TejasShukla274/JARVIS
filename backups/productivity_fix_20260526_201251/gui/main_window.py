# gui/main_window.py

import sys
import math

from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPen,
    QFont,
    QPainterPath
)

from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal

from gui.gui_state import get_state
from gui import audio_reactive
from gui.reminder_panel import ReminderPanel
from scheduler.reminder_scheduler import ReminderScheduler
from voice.voice_output import speak


class ReminderBridge(QObject):

    reminder_due = pyqtSignal(dict)


class MorphingOrb(QWidget):

    def __init__(self):

        super().__init__()

        # window settings
        self.setWindowTitle("J.A.R.V.I.S")

        self.setGeometry(500, 150, 900, 700)

        self.setStyleSheet("background-color: black;")

        # orb animation variables
        self.phase = 0

        self.current_color = (255, 40, 40)

        self.reactive_radius = 120

        # start microphone listener
        self.audio_stream = audio_reactive.start_audio_listener()

        # animation timer
        self.timer = QTimer()

        self.timer.timeout.connect(self.update_animation)

        self.timer.start(16)



    def update_animation(self):

        # gets assistant current state
        state = get_state()

        # gets live microphone volume
        volume = audio_reactive.get_volume()

        # orb pulse
        self.reactive_radius = 120 + (volume * 100)

        # different colors for different states

        # LISTENING
        if state == "listening":

            self.current_color = (0, 255, 120)

        # SPEAKING
        elif state == "speaking":

            self.current_color = (0, 170, 255)

        # IDLE
        else:

            self.current_color = (255, 40, 40)

        # animation movement
        self.phase += 0.08

        self.update()



    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        # center of orb
        center_x = self.width() // 2
        center_y = self.height() // 2

        radius = self.reactive_radius

        # color unpacking
        r, g, b = self.current_color

        # glowing pen
        pen = QPen(QColor(r, g, b), 4)

        painter.setPen(pen)

        # transparent fill
        painter.setBrush(QColor(r, g, b, 50))

        # create morphing path
        path = QPainterPath()

        points = []

        # generates fluid changing shape
        for angle in range(0, 360, 8):

            rad = math.radians(angle)

            wave = math.sin(rad * 4 + self.phase) * 18

            dynamic_radius = radius + wave

            x = center_x + dynamic_radius * math.cos(rad)

            y = center_y + dynamic_radius * math.sin(rad)

            points.append((x, y))

        # start path
        first_x, first_y = points[0]

        path.moveTo(first_x, first_y)

        # connect all points
        for x, y in points[1:]:

            path.lineTo(x, y)

        path.closeSubpath()

        # draw orb
        painter.drawPath(path)

        # center text
        painter.setPen(QColor(255, 255, 255))

        painter.setFont(QFont("Consolas", 22, QFont.Bold))

        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "J.A.R.V.I.S"
        )


class JarvisWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("J.A.R.V.I.S")

        self.setGeometry(500, 150, 700, 700)

        self.setStyleSheet("background-color: black;")

        self.orb = MorphingOrb()

        self.orb.setParent(self)

        # ✅ FIX: make orb fill full window so center is correct
        self.reminder_panel = ReminderPanel()
        self.reminder_panel.setParent(self)

        self.reminder_bridge = ReminderBridge()
        self.reminder_bridge.reminder_due.connect(
            self.show_reminder_notification
        )

        self.reminder_scheduler = ReminderScheduler(
            self.reminder_bridge.reminder_due.emit
        )
        self.reminder_scheduler.start()

        self.layout_children()

    def resizeEvent(self, event):

        # ✅ keeps orb centered on resize
        self.layout_children()

        super().resizeEvent(event)

    def layout_children(self):

        panel_width = 280
        orb_width = max(300, self.width() - panel_width)

        self.orb.setGeometry(0, 0, orb_width, self.height())
        self.reminder_panel.setGeometry(
            orb_width,
            20,
            panel_width - 20,
            max(260, self.height() - 40)
        )

    def show_reminder_notification(self, reminder):

        message = reminder["message"] or reminder["title"]

        self.reminder_panel.refresh()

        QMessageBox.information(
            self,
            "JARVIS Reminder",
            message
        )

        speak(f"Reminder. {message}")

    def closeEvent(self, event):

        self.reminder_scheduler.stop()

        super().closeEvent(event)



def launch_gui():

    app = QApplication(sys.argv)

    window = JarvisWindow()

    window.show()

    sys.exit(app.exec_())
