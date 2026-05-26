# gui/alarm_popup.py

import sys
import threading
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QFont, QPainter, QLinearGradient
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty

from utils.audio_player import play_futuristic_alarm_async, speak_alert


class AlarmPopup(QWidget):
    """
    Futuristic semi-transparent alert screen with pulsing glow animations,
    snooze options, and vocal announcements.
    """
    def __init__(self, title="Alarm Alert", label="Time to wake up!", is_reminder=False):
        super().__init__()
        self.title = title
        self.label = label
        self.is_reminder = is_reminder
        
        # Windows system configuration
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(450, 250)
        
        # Center of screen
        self.center_on_screen()
        
        # Audio / alert stopping trigger
        self.stop_event = threading.Event()
        self.alarm_thread = None
        
        # Flash Animation variables
        self._glow_intensity = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_pulse)
        self.timer.start(30)  # ~30fps pulse
        self.pulse_dir = 1
        
        self.setup_ui()
        self.trigger_alert()

    def center_on_screen(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    @pyqtProperty(int)
    def glow_intensity(self):
        return self._glow_intensity

    @glow_intensity.setter
    def glow_intensity(self, value):
        self._glow_intensity = value
        self.update()

    def update_pulse(self):
        self._glow_intensity += 5 * self.pulse_dir
        if self._glow_intensity >= 150:
            self.pulse_dir = -1
        elif self._glow_intensity <= 30:
            self.pulse_dir = 1
        self.update()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Glow Effect border
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(0, 170, 255, 180) if self.is_reminder else QColor(255, 40, 40, 180))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        # Header Title
        title_lbl = QLabel(self.title.upper())
        title_lbl.setFont(QFont("Consolas", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #00e5ff; letter-spacing: 2px;")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        # Message Label
        msg_lbl = QLabel(self.label)
        msg_lbl.setFont(QFont("Consolas", 14))
        msg_lbl.setStyleSheet("color: white;")
        msg_lbl.setAlignment(Qt.AlignCenter)
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        if not self.is_reminder:
            snooze_btn = QPushButton("SNOOZE")
            snooze_btn.setFont(QFont("Consolas", 11, QFont.Bold))
            snooze_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #00ffaa;
                    border: 1px solid #00ffaa;
                    border-radius: 8px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 255, 170, 0.2);
                    border: 2px solid #00ffaa;
                }
            """)
            snooze_btn.clicked.connect(self.snooze_action)
            btn_layout.addWidget(snooze_btn)

        stop_btn = QPushButton("DISMISS" if self.is_reminder else "STOP")
        stop_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {'#00ffaa' if self.is_reminder else '#ff3333'};
                border: 1px solid {'#00ffaa' if self.is_reminder else '#ff3333'};
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: rgba({ '0, 255, 170' if self.is_reminder else '255, 51, 51' }, 0.2);
                border: 2px solid {'#00ffaa' if self.is_reminder else '#ff3333'};
            }}
        """)
        stop_btn.clicked.connect(self.stop_action)
        btn_layout.addWidget(stop_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def trigger_alert(self):
        # 1. Start alarm loop audio
        self.alarm_thread = play_futuristic_alarm_async(
            duration_sec=30,
            stop_event=self.stop_event
        )
        
        # 2. Run Voice Announcement asynchronously
        announce_text = f"Sir, your alert for {self.label} is active."
        if not self.is_reminder:
            announce_text = f"Sir, your alarm labeled {self.label} is ringing."
            
        threading.Thread(
            target=lambda: speak_alert(announce_text),
            daemon=True
        ).start()

    def snooze_action(self):
        self.cleanup()
        # Add snooze logic (reschedules alarm +5 mins)
        from database.db_manager import add_alarm
        import datetime
        snooze_time = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%H:%M")
        add_alarm(time=snooze_time, label=f"Snoozed: {self.label}", repeat_days="[]", is_active=1)
        self.close()

    def stop_action(self):
        self.cleanup()
        self.close()

    def cleanup(self):
        self.stop_event.set()
        self.timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Cyber-punk semi-transparent glass background with red/blue pulsing gradient border
        glow_color = QColor(0, 170, 255, self._glow_intensity) if self.is_reminder else QColor(255, 40, 40, self._glow_intensity)
        
        painter.setBrush(QColor(10, 10, 15, 235))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        
        # Pulsing neon border lines
        painter.setBrush(Qt.NoBrush)
        painter.setPen(glow_color)
        painter.drawRoundedRect(self.rect(), 12, 12)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = AlarmPopup("ALARM TRIGGERED", "Sir, time to start engineering", is_reminder=False)
    win.show()
    sys.exit(app.exec_())
