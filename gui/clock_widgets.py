from datetime import datetime
import math
import sys

from PyQt5.QtCore import Qt, QTimer, QElapsedTimer, QPointF, QRectF
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QPen, QColor, QRadialGradient
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QLabel


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


class FuturisticDial(QWidget):
    """Reusable animated circular dial for stopwatch and countdown surfaces."""

    def __init__(self, accent=QColor("#00e5ff"), parent=None):
        super().__init__(parent)

        self.accent = QColor(accent)

        self.progress = 0.0
        self.sweep = 0.0
        self.hand_ratio = 0.0

        self.center_text = "00:00:00"
        self.sub_text = ""

        self.show_hand = True

        self.setMinimumSize(320, 320)

        self._elapsed = QElapsedTimer()
        self._elapsed.start()

        # ANIMATION TIMER
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate)
        self._animation_timer.start(16)

    def set_values(
        self,
        progress=None,
        hand_ratio=None,
        center_text=None,
        sub_text=None,
    ):
        if progress is not None:
            self.progress = clamp(float(progress))

        if hand_ratio is not None:
            self.hand_ratio = float(hand_ratio) % 1.0

        if center_text is not None:
            self.center_text = center_text

        if sub_text is not None:
            self.sub_text = sub_text

        self.update()

    def _animate(self):
        self.sweep = (self.sweep + 0.75) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())

        cx = self.width() / 2
        cy = self.height() / 2

        radius = side / 2 - 18

        rect = (
            int(cx - radius),
            int(cy - radius),
            int(radius * 2),
            int(radius * 2),
        )

        # BACKGROUND
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(4, 12, 18, 220))
        painter.drawEllipse(QPointF(cx, cy), radius + 8, radius + 8)

        # OUTER GLOW
        for blur, alpha in ((14, 30), (8, 55), (4, 110)):
            pen = QPen(
                QColor(
                    self.accent.red(),
                    self.accent.green(),
                    self.accent.blue(),
                    alpha,
                ),
                blur,
            )
            pen.setCapStyle(Qt.RoundCap)

            painter.setPen(pen)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # INNER CIRCLE
        painter.setPen(QPen(QColor(36, 82, 100, 170), 1))
        painter.drawEllipse(QPointF(cx, cy), radius - 18, radius - 18)

        # TICKS
        for idx in range(60):
            angle = math.radians(idx * 6 - 90)

            outer = radius - 4
            inner = radius - (16 if idx % 5 == 0 else 9)

            p1 = QPointF(
                cx + math.cos(angle) * inner,
                cy + math.sin(angle) * inner,
            )

            p2 = QPointF(
                cx + math.cos(angle) * outer,
                cy + math.sin(angle) * outer,
            )

            painter.setPen(
                QPen(
                    QColor(
                        155,
                        230,
                        255,
                        190 if idx % 5 == 0 else 80,
                    ),
                    2 if idx % 5 == 0 else 1,
                )
            )

            painter.drawLine(p1, p2)

        # SWEEP LINES
        painter.setPen(
            QPen(
                QColor(
                    self.accent.red(),
                    self.accent.green(),
                    self.accent.blue(),
                    75,
                ),
                1,
            )
        )

        for angle_deg in range(0, 360, 30):
            angle = math.radians(angle_deg - 90 + self.sweep * 0.05)

            end = QPointF(
                cx + math.cos(angle) * (radius - 28),
                cy + math.sin(angle) * (radius - 28),
            )

            painter.drawLine(QPointF(cx, cy), end)

        # PROGRESS ARC
        progress_pen = QPen(self.accent, 6)
        progress_pen.setCapStyle(Qt.RoundCap)

        painter.setPen(progress_pen)

        painter.drawArc(
            *rect,
            90 * 16,
            int(-360 * self.progress * 16),
        )

        # CLOCK HAND
        if self.show_hand:
            angle = math.radians(self.hand_ratio * 360 - 90)

            hand_end = QPointF(
                cx + math.cos(angle) * (radius - 35),
                cy + math.sin(angle) * (radius - 35),
            )

            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(QPointF(cx, cy), hand_end)

            painter.setBrush(self.accent)
            painter.setPen(Qt.NoPen)

            painter.drawEllipse(QPointF(cx, cy), 5, 5)
            painter.drawEllipse(hand_end, 4, 4)

        # MAIN TIME TEXT
        painter.setPen(QColor("#eafaff"))

        painter.setFont(
            QFont(
                "Consolas",
                max(16, int(side * 0.075)),
                QFont.Bold,
            )
        )

        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            self.center_text,
        )

        # SUB TEXT
        if self.sub_text:
            painter.setPen(QColor(130, 230, 255, 180))

            painter.setFont(
                QFont(
                    "Consolas",
                    max(8, int(side * 0.035)),
                    QFont.Bold,
                )
            )

            painter.drawText(
                0,
                int(cy + side * 0.13),
                self.width(),
                28,
                Qt.AlignCenter,
                self.sub_text,
            )





# -------------------------------------------------
# JARVIS CORE GLYPH (ANIMATED HUD ORB)
# -------------------------------------------------


class JarvisCoreGlyph(QWidget):
    """
    Animated HUD Core Orb for JARVIS.
    Responds dynamically to voice assistant states (idle, listening, speaking)
    and microphone audio volume level.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0.0
        self.setMinimumSize(140, 140)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)  # ~30 fps

    def _animate(self):
        self.angle = (self.angle + 2.5) % 360.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        size = min(w, h)
        radius = size / 2.0 - 10.0

        if radius <= 0:
            return

        try:
            from gui.gui_state import get_state
            state = get_state()
        except Exception:
            state = "idle"

        try:
            from gui.audio_reactive import get_volume
            vol = get_volume()
        except Exception:
            vol = 0.0

        if state == "listening":
            base_color = QColor("#00ffaa")
        elif state == "speaking":
            base_color = QColor("#00e5ff")
        else:
            base_color = QColor("#ff4b6e")

        grad = QRadialGradient(cx, cy, radius)
        c_glow = QColor(base_color)
        c_glow.setAlpha(int(30 + 40 * vol))
        c_dark = QColor(2, 8, 14, 220)
        grad.setColorAt(0.0, c_glow)
        grad.setColorAt(0.7, QColor(base_color.red(), base_color.green(), base_color.blue(), 10))
        grad.setColorAt(1.0, c_dark)

        painter.setPen(Qt.NoPen)
        painter.setBrush(grad)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        pulse = math.sin(math.radians(self.angle * 2)) * 3.0 + (vol * 8.0)

        pen_outer = QPen(base_color, 2)
        painter.setPen(pen_outer)
        rect_outer = QRectF(cx - radius + 4, cy - radius + 4, (radius - 4) * 2, (radius - 4) * 2)
        painter.drawArc(rect_outer, int((self.angle) * 16), int(120 * 16))
        painter.drawArc(rect_outer, int((self.angle + 180) * 16), int(120 * 16))

        inner_r = radius * 0.6 + pulse
        if inner_r > 0:
            c_inner = QColor(base_color)
            c_inner.setAlpha(180)
            pen_inner = QPen(c_inner, 1.5, Qt.DashLine)
            painter.setPen(pen_inner)
            painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        core_r = radius * 0.35 + (vol * 5.0)
        if core_r > 0:
            core_grad = QRadialGradient(cx, cy, core_r)
            core_grad.setColorAt(0.0, QColor("#ffffff"))
            core_grad.setColorAt(0.5, base_color)
            c_transparent = QColor(base_color)
            c_transparent.setAlpha(0)
            core_grad.setColorAt(1.0, c_transparent)

            painter.setPen(Qt.NoPen)
            painter.setBrush(core_grad)
            painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Consolas", max(7, int(size * 0.055)), QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, "JARVIS\nCORE")


# -------------------------------------------------
# WORLD CLOCK WIDGET
# -------------------------------------------------


class WorldClockWidget(QFrame):
    """
    Compact World Clock Tile for the HUD Dashboard.
    Displays city name, time, timezone label, and short date.
    """

    def __init__(self, city="", time_str="", label="", date_str="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(4, 10, 18, 200);
                border: 1px solid rgba(0, 229, 255, 30);
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(4)

        self.city_label = QLabel(city)
        self.city_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.city_label.setStyleSheet("color: #00e5ff; border: none; background: transparent;")

        self.tz_label = QLabel(label)
        self.tz_label.setFont(QFont("Consolas", 7, QFont.Bold))
        self.tz_label.setStyleSheet("color: rgba(255, 255, 255, 120); border: none; background: transparent;")
        self.tz_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        top_layout.addWidget(self.city_label, stretch=1)
        top_layout.addWidget(self.tz_label)
        layout.addLayout(top_layout)

        self.time_label = QLabel(time_str)
        self.time_label.setFont(QFont("Consolas", 13, QFont.Bold))
        self.time_label.setStyleSheet("color: #eafaff; border: none; background: transparent;")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        self.date_label = QLabel(date_str)
        self.date_label.setFont(QFont("Consolas", 7))
        self.date_label.setStyleSheet("color: rgba(255, 255, 255, 150); border: none; background: transparent;")
        self.date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.date_label)

    def set_data(self, city, time_str, label, date_str):
        self.city_label.setText(city)
        self.time_label.setText(time_str)
        self.tz_label.setText(label)
        self.date_label.setText(date_str)


# -------------------------------------------------
# REAL CLOCK WINDOW
# -------------------------------------------------


class ClockWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("JARVIS CLOCK")

        self.setStyleSheet("""
            QWidget {
                background-color: #02060b;
            }
        """)

        self.resize(500, 500)

        layout = QVBoxLayout(self)

        self.clock_dial = FuturisticDial()

        layout.addWidget(self.clock_dial)

        # REAL CLOCK TIMER
        self.clock_timer = QTimer(self)

        # UPDATE EVERY SECOND
        self.clock_timer.timeout.connect(self.update_clock)

        self.clock_timer.start(1000)

        # INITIAL UPDATE
        self.update_clock()

    def update_clock(self):

        # REAL LOCAL SYSTEM TIME
        now = datetime.now()

        # DIGITAL CLOCK
        current_time = now.strftime("%H:%M:%S")

        # ANALOG HAND
        seconds = now.second + now.microsecond / 1_000_000

        hand_ratio = seconds / 60.0

        # PROGRESS
        progress = seconds / 60.0

        # UPDATE DIAL
        self.clock_dial.set_values(
            progress=progress,
            hand_ratio=hand_ratio,
            center_text=current_time,
            sub_text=now.strftime("%A, %d %B %Y"),
        )


# -------------------------------------------------
# MAIN
# -------------------------------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = ClockWindow()

    window.show()

    sys.exit(app.exec_())