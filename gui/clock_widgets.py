# gui/clock_widgets.py
# ─────────────────────────────────────────────────────────────────────────────
# Reusable animated circular widgets for JARVIS dashboard.
# ─────────────────────────────────────────────────────────────────────────────

import math

from PyQt5.QtCore import Qt, QElapsedTimer, QPointF, QTimer, QRectF
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient,
    QConicalGradient, QLinearGradient
)
from PyQt5.QtWidgets import QWidget


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


class FuturisticDial(QWidget):
    """
    Reusable animated circular dial for stopwatch and countdown surfaces.
    Features:
      - Outer neon glow ring
      - Inner glassmorphism background
      - Tick marks with neon colouring
      - Smooth progress arc
      - Optional ticking hand
      - Pulsing centre dot
      - Centre text and sub-text
    """

    def __init__(self, accent=QColor("#00e5ff"), parent=None):
        super().__init__(parent)
        self.accent = QColor(accent)
        self.progress = 0.0
        self.sweep = 0.0
        self.hand_ratio = 0.0
        self.center_text = "00:00:00"
        self.sub_text = ""
        self.show_hand = True
        self.setMinimumSize(200, 200)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate)
        self._animation_timer.start(16)

    def set_values(self, progress=None, hand_ratio=None,
                   center_text=None, sub_text=None):
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
        self.sweep = (self.sweep + 0.6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        cx = self.width() / 2
        cy = self.height() / 2
        radius = side / 2 - 22

        # ── Outer glow background ────────────────────────────────────────
        glow = QRadialGradient(QPointF(cx, cy), radius + 30)
        glow.setColorAt(0.0, QColor(self.accent.red(), self.accent.green(),
                                     self.accent.blue(), 12))
        glow.setColorAt(0.7, QColor(self.accent.red(), self.accent.green(),
                                     self.accent.blue(), 6))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(cx, cy), radius + 28, radius + 28)

        # ── Dark glass circle fill ───────────────────────────────────────
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(4, 10, 18, 215))
        painter.drawEllipse(QPointF(cx, cy), radius + 6, radius + 6)

        # ── Multiple neon ring layers for glow effect ────────────────────
        for blur, alpha in ((16, 18), (10, 40), (5, 75), (2, 140)):
            pen = QPen(QColor(self.accent.red(), self.accent.green(),
                              self.accent.blue(), alpha), blur)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # ── Inner decorative ring ────────────────────────────────────────
        painter.setPen(QPen(QColor(30, 75, 95, 130), 1))
        painter.drawEllipse(QPointF(cx, cy), radius - 20, radius - 20)

        # ── Tick marks ───────────────────────────────────────────────────
        for idx in range(60):
            angle = math.radians(idx * 6 - 90)
            is_major = idx % 5 == 0
            outer = radius - 3
            inner = radius - (18 if is_major else 10)

            p1 = QPointF(cx + math.cos(angle) * inner,
                         cy + math.sin(angle) * inner)
            p2 = QPointF(cx + math.cos(angle) * outer,
                         cy + math.sin(angle) * outer)

            if is_major:
                painter.setPen(QPen(QColor(150, 230, 255, 210), 2.5))
            else:
                painter.setPen(QPen(QColor(80, 180, 220, 70), 1))
            painter.drawLine(p1, p2)

        # ── Decorative rotating inner lines ──────────────────────────────
        painter.setPen(QPen(QColor(self.accent.red(), self.accent.green(),
                                   self.accent.blue(), 30), 1))
        for angle_deg in range(0, 360, 30):
            angle = math.radians(angle_deg - 90 + self.sweep * 0.04)
            end = QPointF(cx + math.cos(angle) * (radius - 30),
                          cy + math.sin(angle) * (radius - 30))
            painter.drawLine(QPointF(cx, cy), end)

        # ── Progress arc ─────────────────────────────────────────────────
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # Glow behind progress arc
        glow_pen = QPen(QColor(self.accent.red(), self.accent.green(),
                               self.accent.blue(), 50), 12)
        glow_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(glow_pen)
        painter.drawArc(rect, 90 * 16, int(-360 * self.progress * 16))

        # Main progress arc
        progress_pen = QPen(self.accent, 5)
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(rect, 90 * 16, int(-360 * self.progress * 16))

        # ── Hand ─────────────────────────────────────────────────────────
        if self.show_hand:
            angle = math.radians(self.hand_ratio * 360 - 90)
            hand_len = radius - 35
            hand_end = QPointF(cx + math.cos(angle) * hand_len,
                               cy + math.sin(angle) * hand_len)

            # Hand glow
            painter.setPen(QPen(QColor(255, 255, 255, 40), 4))
            painter.drawLine(QPointF(cx, cy), hand_end)
            # Main hand
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(QPointF(cx, cy), hand_end)

            # Centre dot — pulsing
            pulse = 0.6 + 0.4 * math.sin(self.sweep * 0.05)
            painter.setBrush(QColor(self.accent.red(), self.accent.green(),
                                    self.accent.blue(),
                                    int(180 * pulse)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), 6, 6)
            # Tip dot
            painter.setBrush(self.accent)
            painter.drawEllipse(hand_end, 4, 4)

        # ── Centre text ──────────────────────────────────────────────────
        painter.setPen(QColor("#eafaff"))
        text_size = max(14, int(side * 0.072))
        painter.setFont(QFont("Consolas", text_size, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.center_text)

        # ── Sub text ─────────────────────────────────────────────────────
        if self.sub_text:
            painter.setPen(QColor(130, 230, 255, 180))
            sub_size = max(8, int(side * 0.032))
            painter.setFont(QFont("Consolas", sub_size, QFont.Bold))
            painter.drawText(0, int(cy + side * 0.14), self.width(), 28,
                             Qt.AlignCenter, self.sub_text)


class JarvisCoreGlyph(QWidget):
    """Animated JARVIS core orb used by the dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.phase = 0.0
        self.setMinimumSize(160, 140)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        
        # Audio listener initialization if not already done
        from gui import audio_reactive
        try:
            self.audio_stream = audio_reactive.start_audio_listener()
        except Exception:
            pass

    def tick(self):
        self.phase += 0.06
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx = self.width() / 2
        cy = self.height() / 2

        # gets assistant current state
        from gui.gui_state import get_state
        from gui import audio_reactive
        state = get_state()
        volume = audio_reactive.get_volume()

        # Set colors and radius based on state
        if state == "listening":
            accent_color = QColor(0, 255, 120)  # Green
            glow_color = QColor(0, 255, 120, 18)
            inner_glow = QColor(0, 255, 120, 60)
            text_color = QColor("#d6ffeb")
        elif state == "speaking":
            accent_color = QColor(0, 170, 255)  # Cyan
            glow_color = QColor(0, 170, 255, 18)
            inner_glow = QColor(0, 170, 255, 60)
            text_color = QColor("#d6f0ff")
        else:  # idle
            accent_color = QColor(255, 40, 40)   # Red
            glow_color = QColor(255, 30, 60, 18)
            inner_glow = QColor(255, 45, 80, 60)
            text_color = QColor("#ffd6dc")

        radius = min(self.width(), self.height()) * 0.32
        radius += (volume * 50)

        # Outer glow
        glow = QRadialGradient(QPointF(cx, cy), radius + 20)
        glow.setColorAt(0.0, glow_color)
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(cx, cy), radius + 18, radius + 18)

        # Morphing shape
        path = QPainterPath()
        points = []
        wave_mult = 18 if state == "listening" else (16 if state == "speaking" else 14)
        wave_mult += (volume * 60)

        for angle_deg in range(0, 360, 8):
            angle = math.radians(angle_deg)
            wave = (math.sin(angle * 3 + self.phase) * wave_mult
                    + math.cos(angle * 5 - self.phase) * (wave_mult * 0.4))
            r = radius + wave
            points.append(QPointF(cx + math.cos(angle) * r,
                                  cy + math.sin(angle) * r))

        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)
        path.closeSubpath()

        painter.setPen(QPen(accent_color, 2.5))
        painter.setBrush(QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 20))
        painter.drawPath(path)

        # Inner ring
        painter.setPen(QPen(inner_glow, 1))
        painter.setBrush(Qt.NoBrush)
        inner_r = radius * 0.55
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # Label
        painter.setPen(text_color)
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, "J.A.R.V.I.S")


class WorldClockWidget(QWidget):
    """Compact world clock tile showing city name, time, and date."""

    def __init__(self, city="City", time_str="00:00", label="UTC",
                 date_str="01 Jan", parent=None):
        super().__init__(parent)
        self.city = city
        self.time_str = time_str
        self.label = label
        self.date_str = date_str
        self.setMinimumSize(120, 58)
        self.setMaximumHeight(62)

    def set_data(self, city, time_str, label, date_str):
        self.city = city
        self.time_str = time_str
        self.label = label
        self.date_str = date_str
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.setPen(QPen(QColor(0, 229, 255, 35), 1))
        painter.setBrush(QColor(4, 10, 18, 200))
        painter.drawRoundedRect(QRectF(1, 1, self.width() - 2,
                                       self.height() - 2), 8, 8)

        # City name
        painter.setPen(QColor(0, 229, 255, 200))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(8, 16, self.city)

        # Time
        painter.setPen(QColor("#eafaff"))
        painter.setFont(QFont("Consolas", 14, QFont.Bold))
        painter.drawText(8, 38, self.time_str)

        # Label + date
        painter.setPen(QColor(255, 255, 255, 100))
        painter.setFont(QFont("Consolas", 7))
        text_w = painter.fontMetrics().horizontalAdvance(self.time_str)
        painter.drawText(12 + text_w, 38, f" {self.label}")
        painter.drawText(8, 52, self.date_str)
