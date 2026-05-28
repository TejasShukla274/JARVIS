# gui/weather_widgets.py
# ─────────────────────────────────────────────────────────────────────────────
# Custom vector-drawn animated neon weather widgets for JARVIS cockpit.
# ─────────────────────────────────────────────────────────────────────────────

import math
import time
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QRadialGradient
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF

from gui import styles
from services.weather_service import get_cached_weather, fetch_and_cache_weather, is_weather_cache_expired

# ── ✏️  CHANGE THIS to any city you want ─────────────────────────────────────
WEATHER_CITY = "Ayodhya"
# ─────────────────────────────────────────────────────────────────────────────


class NeonWeatherIcon(QWidget):
    """
    Futuristic HUD vector-drawn animated neon weather icon.
    Draws custom micro-animations without external image/gif dependencies:
      - clear_day: Rotating glowing sun
      - clear_night: Crescent moon with pulsing stars
      - clouds: Slow-pulsing cloud shapes
      - rain: Clouds + animated falling drops
      - thunderstorm: Dark clouds + flickering lightning bolts
      - snow: Clouds + drifting rotating snowflakes
      - mist: Ripple-shifting horizontal mist lines
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.category = "clouds"  # Default
        self.animation_step = 0.0
        self.setMinimumSize(60, 60)
        self.setMaximumSize(80, 80)
        
        # High efficiency paint timer (33ms = 30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def set_category(self, category):
        category = category.lower()
        if category in ["clear_day", "clear_night", "clouds", "rain", "thunderstorm", "snow", "mist"]:
            self.category = category
        else:
            self.category = "clouds"
        self.update()

    def tick(self):
        self.animation_step += 0.05
        if self.animation_step > 1000.0:
            self.animation_step = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        size = min(w, h) * 0.7
        r = size / 2

        if self.category == "clear_day":
            self.draw_clear_day(painter, cx, cy, r)
        elif self.category == "clear_night":
            self.draw_clear_night(painter, cx, cy, r)
        elif self.category == "clouds":
            self.draw_clouds(painter, cx, cy, r)
        elif self.category == "rain":
            self.draw_rain(painter, cx, cy, r)
        elif self.category == "thunderstorm":
            self.draw_thunderstorm(painter, cx, cy, r)
        elif self.category == "snow":
            self.draw_snow(painter, cx, cy, r)
        elif self.category == "mist":
            self.draw_mist(painter, cx, cy, r)

    # ── Sun animation (clear_day) ────────────────────────────────────────────
    def draw_clear_day(self, painter, cx, cy, r):
        # Draw soft radial core glow
        glow = QRadialGradient(QPointF(cx, cy), r * 1.5)
        glow.setColorAt(0.0, QColor(255, 170, 0, 45))
        glow.setColorAt(0.6, QColor(255, 170, 0, 10))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(cx, cy), r * 1.4, r * 1.4)

        # Sun core
        painter.setBrush(QColor(styles.BG_DEEPEST))
        painter.setPen(QPen(QColor(styles.AMBER), 2.5))
        painter.drawEllipse(QPointF(cx, cy), r * 0.6, r * 0.6)

        # Rotating Rays
        ray_pen = QPen(QColor(styles.AMBER), 2.0)
        ray_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(ray_pen)
        
        num_rays = 8
        rot = self.animation_step * 0.4
        for i in range(num_rays):
            angle = math.radians(i * (360 / num_rays) + rot * 10)
            inner_dist = r * 0.75
            outer_dist = r * 1.05
            p1 = QPointF(cx + math.cos(angle) * inner_dist, cy + math.sin(angle) * inner_dist)
            p2 = QPointF(cx + math.cos(angle) * outer_dist, cy + math.sin(angle) * outer_dist)
            painter.drawLine(p1, p2)

    # ── Crescent Moon animation (clear_night) ─────────────────────────────────
    def draw_clear_night(self, painter, cx, cy, r):
        # Pulsing stars in background
        star_pulse = 0.5 + 0.5 * math.sin(self.animation_step * 2)
        star_color = QColor(0, 229, 255, int(80 + 100 * star_pulse))
        painter.setPen(QPen(star_color, 1.5))
        
        # Draw little points/crosses for stars
        stars = [
            QPointF(cx - r * 0.8, cy - r * 0.8),
            QPointF(cx + r * 0.7, cy - r * 0.6),
            QPointF(cx - r * 0.6, cy + r * 0.7)
        ]
        for star in stars:
            painter.drawLine(QPointF(star.x() - 2, star.y()), QPointF(star.x() + 2, star.y()))
            painter.drawLine(QPointF(star.x(), star.y() - 2), QPointF(star.x(), star.y() + 2))

        # Crescent moon path
        path = QPainterPath()
        # Outer arc
        rect_outer = QRectF(cx - r * 0.7, cy - r * 0.7, r * 1.4, r * 1.4)
        path.arcTo(rect_outer, 120, 220)
        # Inner arc
        rect_inner = QRectF(cx - r * 0.45, cy - r * 0.6, r * 1.2, r * 1.2)
        path.arcTo(rect_inner, 340, -220)
        path.closeSubpath()

        # Moon glow
        glow = QRadialGradient(QPointF(cx - 2, cy - 2), r * 1.3)
        glow.setColorAt(0.0, QColor(0, 229, 255, 30))
        glow.setColorAt(0.8, QColor(0, 229, 255, 5))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Main crescent
        painter.setPen(QPen(QColor(styles.CYAN), 2.5))
        painter.setBrush(QColor(styles.BG_DEEPEST))
        painter.drawPath(path)

    # ── Clouds painting (clouds) ──────────────────────────────────────────────
    def draw_clouds_base(self, painter, cx, cy, r, offset_y=0, pulse_scalar=1.0):
        # Draw background cloud
        pulse = 1.0 + 0.05 * math.sin(self.animation_step + pulse_scalar)
        
        # Cloud coordinate definitions
        c_x = cx + r * 0.2
        c_y = cy - r * 0.15 + offset_y
        
        # Draw overlapping neon circles & base rounded rectangle
        painter.setPen(QPen(QColor(0, 229, 255, 60), 1.5))
        painter.setBrush(QColor(4, 12, 22, 130))
        
        # Left circle
        painter.drawEllipse(QPointF(cx - r * 0.45 * pulse, c_y + r * 0.15), r * 0.4, r * 0.4)
        # Main center circle
        painter.drawEllipse(QPointF(c_x - r * 0.3 * pulse, c_y - r * 0.1), r * 0.55, r * 0.55)
        # Right circle
        painter.drawEllipse(QPointF(c_x + r * 0.35 * pulse, c_y + r * 0.1), r * 0.45, r * 0.45)
        
        # Cloud base bounding rect
        base_rect = QRectF(cx - r * 0.7 * pulse, c_y + r * 0.1, r * 1.55 * pulse, r * 0.45)
        painter.drawRoundedRect(base_rect, 10, 10)

    def draw_clouds(self, painter, cx, cy, r):
        self.draw_clouds_base(painter, cx, cy, r, offset_y=0, pulse_scalar=1.0)
        # Foreground main outline
        pulse = 1.0 + 0.03 * math.sin(self.animation_step * 1.2)
        painter.setPen(QPen(QColor(styles.CYAN), 2.5))
        painter.setBrush(Qt.NoBrush)
        
        # Draw highlights of cloud silhouette
        painter.drawArc(QRectF(cx - r * 0.85 * pulse, cy - r * 0.1, r * 0.8 * pulse, r * 0.8 * pulse), 40 * 16, 150 * 16)
        painter.drawArc(QRectF(cx - r * 0.3 * pulse, cy - r * 0.45, r * 1.1 * pulse, r * 1.1 * pulse), 10 * 16, 160 * 16)
        painter.drawArc(QRectF(cx + r * 0.45 * pulse, cy - r * 0.15, r * 0.8 * pulse, r * 0.8 * pulse), -30 * 16, 140 * 16)
        painter.drawLine(QPointF(cx - r * 0.5 * pulse, cy + r * 0.5), QPointF(cx + r * 0.85 * pulse, cy + r * 0.5))

    # ── Rain animation (rain) ────────────────────────────────────────────────
    def draw_rain(self, painter, cx, cy, r):
        # Draw background cloud first (slightly higher up)
        self.draw_clouds_base(painter, cx, cy - r * 0.1, r, offset_y=-r * 0.15)
        self.draw_clouds(painter, cx, cy - r * 0.1, r)

        # Animated raindrops
        painter.setPen(QPen(QColor(styles.CYAN), 2.0))
        painter.setBrush(Qt.NoBrush)
        
        # 3 lanes of raindrops sliding downwards
        lanes = [-0.4, 0.0, 0.4]
        for idx, lane in enumerate(lanes):
            # Speed differences
            offset = (self.animation_step * 8 + idx * 12) % (r * 0.8)
            drop_x = cx + lane * r
            drop_y = cy + r * 0.2 + offset
            
            # Draw slanted droplet line
            if drop_y < cy + r * 1.1:
                painter.drawLine(QPointF(drop_x, drop_y), QPointF(drop_x - 3, drop_y + 8))

    # ── Thunderstorm animation (thunderstorm) ─────────────────────────────────
    def draw_thunderstorm(self, painter, cx, cy, r):
        # Cloud layer
        self.draw_clouds_base(painter, cx, cy - r * 0.1, r, offset_y=-r * 0.15)
        self.draw_clouds(painter, cx, cy - r * 0.1, r)

        # Lightning flicker logic (rapid flashes)
        flicker = int(self.animation_step * 10) % 20
        if flicker in [1, 2, 4]:
            # Glow on background
            glow = QRadialGradient(QPointF(cx, cy + r * 0.4), r * 1.3)
            glow.setColorAt(0.0, QColor(255, 170, 0, 70))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(cx, cy + r * 0.4), r * 1.2, r * 1.2)

            # Lightning bolt path
            path = QPainterPath()
            path.moveTo(cx - r * 0.15, cy + r * 0.25)
            path.lineTo(cx - r * 0.35, cy + r * 0.55)
            path.lineTo(cx, cy + r * 0.5)
            path.lineTo(cx - r * 0.2, cy + r * 0.95)
            
            painter.setPen(QPen(QColor(styles.AMBER), 3.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

    # ── Snow animation (snow) ────────────────────────────────────────────────
    def draw_snow(self, painter, cx, cy, r):
        self.draw_clouds_base(painter, cx, cy - r * 0.1, r, offset_y=-r * 0.15)
        self.draw_clouds(painter, cx, cy - r * 0.1, r)

        # Drifting snow particles
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        lanes = [(-0.45, 0.0), (0.05, 0.3), (0.45, 0.6)]
        for idx, (lane_x, phase) in enumerate(lanes):
            drift_y = cy + r * 0.2 + ((self.animation_step * 2.5 + idx * 8) % (r * 0.75))
            drift_x = cx + lane_x * r + math.sin(self.animation_step * 1.5 + phase) * 5
            
            if drift_y < cy + r * 1.0:
                # Draw asterisk snow particle
                painter.drawLine(QPointF(drift_x - 3, drift_y), QPointF(drift_x + 3, drift_y))
                painter.drawLine(QPointF(drift_x, drift_y - 3), QPointF(drift_x, drift_y + 3))

    # ── Mist/Fog animation (mist) ────────────────────────────────────────────
    def draw_mist(self, painter, cx, cy, r):
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(styles.CYAN), 2.0))
        
        # 3 parallel wavy lines shifting left/right
        lines_y = [-r * 0.4, 0, r * 0.4]
        for idx, offset_y in enumerate(lines_y):
            path = QPainterPath()
            phase_shift = self.animation_step * 2 + idx * 4
            
            # Start path
            first_x = cx - r * 1.1
            first_y = cy + offset_y + math.sin(phase_shift) * 3
            path.moveTo(first_x, first_y)
            
            # Draw rippling sine wave
            segments = 12
            for i in range(1, segments + 1):
                px = cx - r * 1.1 + (r * 2.2 / segments) * i
                angle = phase_shift + (i / segments) * math.pi * 3
                py = cy + offset_y + math.sin(angle) * 3
                path.lineTo(px, py)
                
            # Pulsing alpha
            alpha = int(120 + 80 * math.sin(self.animation_step * 0.8 + idx))
            painter.setPen(QPen(QColor(0, 229, 255, alpha), 2.0))
            painter.drawPath(path)


class CompactWeatherWidget(QFrame):
    """
    HUD Weather Panel. Includes the Delhi animated weather icon,
    the live temperature read, and current condition.
    Self-updates asynchronously in the background.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(12)

        # 1. Custom animated icon
        self.icon_widget = NeonWeatherIcon()
        layout.addWidget(self.icon_widget)

        # 2. Text layout
        txt_layout = QVBoxLayout()
        txt_layout.setContentsMargins(0, 0, 0, 0)
        txt_layout.setSpacing(1)

        self.lbl_city_cond = QLabel("DELHI / CONNECTING...")
        self.lbl_city_cond.setFont(QFont(styles.FONT_FAMILY, 8, QFont.Bold))
        self.lbl_city_cond.setStyleSheet(styles.HEADER_LABEL)
        txt_layout.addWidget(self.lbl_city_cond)

        self.lbl_temp = QLabel("--°C")
        self.lbl_temp.setFont(QFont(styles.FONT_FAMILY, 24, QFont.Bold))
        self.lbl_temp.setStyleSheet(f"color: {styles.WHITE}; background: transparent; border: none;")
        txt_layout.addWidget(self.lbl_temp)

        self.lbl_humidity_feels = QLabel("H: --% | FEELS: --°C")
        self.lbl_humidity_feels.setFont(QFont(styles.FONT_FAMILY, 8))
        self.lbl_humidity_feels.setStyleSheet(styles.DIM_LABEL)
        txt_layout.addWidget(self.lbl_humidity_feels)

        layout.addLayout(txt_layout)

        # Timer to trigger caching fetch safely
        self.fetch_timer = QTimer(self)
        self.fetch_timer.timeout.connect(self.run_background_fetch)
        self.fetch_timer.start(1000 * 60 * 3)  # Checks cache every 3 minutes

        # Load immediate cached state
        self.load_cache_and_render()

    def load_cache_and_render(self):
        """Loads immediately from cached JSON if present."""
        data = get_cached_weather()
        if data:
            self.lbl_temp.setText(f"{data['temperature']}°C")
            self.lbl_city_cond.setText(f"{data['city'].upper()} / {data['condition'].upper()}")
            self.lbl_humidity_feels.setText(f"HUMIDITY: {data['humidity']}% | FEELS: {data['feels_like']}°C")
            self.icon_widget.set_category(data["icon"])
        else:
            self.lbl_city_cond.setText(f"{WEATHER_CITY.upper()} / FETCHING...")
            self.icon_widget.set_category("clouds")
            # Trigger background fetch immediately on startup
            self.run_background_fetch(force=True)

    def run_background_fetch(self, force=False):
        """Fires background thread to update caching to ensure zero dashboard start lag."""
        if force or is_weather_cache_expired():
            # Run asynchronously
            import threading
            t = threading.Thread(target=self._async_fetch_job, daemon=True)
            t.start()

    def _async_fetch_job(self):
        """Runs on a background thread to prevent GUI lockups."""
        try:
            fetch_and_cache_weather(WEATHER_CITY)
            # Safely invoke GUI update from the background thread via a QTimer shot
            QTimer.singleShot(0, self.load_cache_and_render)
        except Exception as e:
            print("Background weather fetch error:", e)
