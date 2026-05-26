# gui/stopwatch_timer_tab.py

import math
import uuid
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QScrollArea
)
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from scheduler.background_scheduler import get_scheduler
from utils.audio_player import play_notification_beep


class CircularTimerAnimation(QWidget):
    """
    Renders a glowing, futuristic circular progress ring representing seconds or timer ratios.
    """
    def __init__(self, color=QColor(0, 170, 255)):
        super().__init__()
        self.color = color
        self.angle_offset = 0.0
        self.setMinimumSize(120, 120)

    def set_progress(self, ratio):
        # Ratio should be 0.0 to 1.0
        self.angle_offset = float(ratio) * 360.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(self.width(), self.height()) // 2 - 10
        
        # 1. Base dark glowing trace circle
        pen_trace = QPen(QColor(self.color.red(), self.color.green(), self.color.blue(), 30), 4)
        painter.setPen(pen_trace)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # 2. Glowing progress arc
        pen_glow = QPen(self.color, 4)
        painter.setPen(pen_glow)
        
        # In PyQt, angle is in 1/16th of a degree
        start_angle = 90 * 16  # start at 12 o'clock
        span_angle = int(-self.angle_offset * 16)
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            start_angle, span_angle
        )


class StopwatchTimerTab(QWidget):
    """
    Unified view containing the futuristic Stopwatch and Timer subsystems.
    """
    def __init__(self):
        super().__init__()
        self.setup_stopwatch_state()
        self.setup_ui()
        
        # Stopwatch ticking timer (10ms intervals for millisecond precision)
        self.sw_timer = QTimer()
        self.sw_timer.timeout.connect(self.tick_stopwatch)
        
        # Scheduler hooks
        self.scheduler = get_scheduler()
        self.scheduler.second_tick.connect(self.refresh_timer_queue)
        
    def setup_stopwatch_state(self):
        self.sw_running = False
        self.sw_time_ms = 0
        self.sw_laps = []

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(25)
        
        # =====================================================================
        # LEFT PANEL: STOPWATCH
        # =====================================================================
        sw_panel = QWidget()
        sw_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        sw_layout = QVBoxLayout(sw_panel)
        sw_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        sw_title = QLabel("CHRONOMETER SYSTEM")
        sw_title.setFont(QFont("Consolas", 11, QFont.Bold))
        sw_title.setStyleSheet("color: #00ffaa; letter-spacing: 1px; border: none;")
        sw_layout.addWidget(sw_title, alignment=Qt.AlignTop)

        # Reactive Ring + Digital readout layout
        sw_hud_layout = QHBoxLayout()
        self.sw_anim = CircularTimerAnimation(QColor(0, 255, 170))
        sw_hud_layout.addWidget(self.sw_anim)

        self.sw_display = QLabel("00:00:00.00")
        self.sw_display.setFont(QFont("Consolas", 28, QFont.Bold))
        self.sw_display.setStyleSheet("color: white; border: none;")
        sw_hud_layout.addWidget(self.sw_display, stretch=1)
        sw_layout.addLayout(sw_hud_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_sw_start = QPushButton("START")
        self.btn_sw_start.setFont(QFont("Consolas", 10, QFont.Bold))
        self.btn_sw_start.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 170, 20);
                color: #00ffaa;
                border: 1px solid #00ffaa;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 170, 50);
            }
        """)
        self.btn_sw_start.clicked.connect(self.toggle_stopwatch)
        btn_layout.addWidget(self.btn_sw_start)

        self.btn_sw_lap = QPushButton("LAP")
        self.btn_sw_lap.setFont(QFont("Consolas", 10, QFont.Bold))
        self.btn_sw_lap.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 170, 255, 20);
                color: #00aaff;
                border: 1px solid #00aaff;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 170, 255, 50);
            }
        """)
        self.btn_sw_lap.clicked.connect(self.record_lap)
        self.btn_sw_lap.setEnabled(False)
        btn_layout.addWidget(self.btn_sw_lap)

        self.btn_sw_reset = QPushButton("RESET")
        self.btn_sw_reset.setFont(QFont("Consolas", 10, QFont.Bold))
        self.btn_sw_reset.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 50, 50, 20);
                color: #ff3232;
                border: 1px solid #ff3232;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 50);
            }
        """)
        self.btn_sw_reset.clicked.connect(self.reset_stopwatch)
        btn_layout.addWidget(self.btn_sw_reset)
        sw_layout.addLayout(btn_layout)

        # Laps Table
        self.laps_table = QTableWidget(0, 2)
        self.laps_table.setHorizontalHeaderLabels(["Lap", "Split Time"])
        self.laps_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.laps_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(10, 10, 15, 120);
                border: 1px solid rgba(0, 170, 255, 20);
                color: white;
                gridline-color: rgba(0, 170, 255, 10);
            }
            QHeaderView::section {
                background-color: rgba(15, 15, 25, 255);
                color: #00e5ff;
                font-family: Consolas;
                border: 1px solid rgba(0, 170, 255, 20);
            }
        """)
        sw_layout.addWidget(self.laps_table)
        main_layout.addWidget(sw_panel, stretch=1)

        # =====================================================================
        # RIGHT PANEL: TIMER & MULTI-TIMERS
        # =====================================================================
        timer_panel = QWidget()
        timer_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        timer_layout = QVBoxLayout(timer_panel)
        timer_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        t_title = QLabel("COUNTDOWN SYSTEM")
        t_title.setFont(QFont("Consolas", 11, QFont.Bold))
        t_title.setStyleSheet("color: #00aaff; letter-spacing: 1px; border: none;")
        timer_layout.addWidget(t_title, alignment=Qt.AlignTop)

        # Selectors layout
        sel_layout = QHBoxLayout()
        sel_layout.setSpacing(10)
        
        self.spin_h = QSpinBox()
        self.spin_h.setRange(0, 23)
        self.spin_h.setSuffix("h")
        self.spin_h.setFont(QFont("Consolas", 11))
        self.spin_h.setStyleSheet("color: white; background-color: #0a0a0f; padding: 4px; border-radius: 4px;")
        
        self.spin_m = QSpinBox()
        self.spin_m.setRange(0, 59)
        self.spin_m.setSuffix("m")
        self.spin_m.setValue(10)  # Default 10 mins
        self.spin_m.setFont(QFont("Consolas", 11))
        self.spin_m.setStyleSheet("color: white; background-color: #0a0a0f; padding: 4px; border-radius: 4px;")

        self.spin_s = QSpinBox()
        self.spin_s.setRange(0, 59)
        self.spin_s.setSuffix("s")
        self.spin_s.setFont(QFont("Consolas", 11))
        self.spin_s.setStyleSheet("color: white; background-color: #0a0a0f; padding: 4px; border-radius: 4px;")

        sel_layout.addWidget(self.spin_h)
        sel_layout.addWidget(self.spin_m)
        sel_layout.addWidget(self.spin_s)
        timer_layout.addLayout(sel_layout)

        # Launch Timer button
        btn_start_t = QPushButton("DEPLOY TIMER")
        btn_start_t.setFont(QFont("Consolas", 10, QFont.Bold))
        btn_start_t.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 170, 255, 30);
                color: #00aaff;
                border: 1px solid #00aaff;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 170, 255, 60);
            }
        """)
        btn_start_t.clicked.connect(self.deploy_custom_timer)
        timer_layout.addWidget(btn_start_t)

        # Presets Buttons
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(5)
        
        presets = [("5 Min", 300), ("10 Min", 600), ("25 Min", 1500), ("1 Hour", 3600)]
        for label, sec in presets:
            btn = QPushButton(label)
            btn.setFont(QFont("Consolas", 9))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 170, 255, 30);
                    border: 1px solid #00aaff;
                }
            """)
            # Workaround for capturing loop variable properly inside lambda
            btn.clicked.connect(lambda checked, s=sec: self.deploy_preset_timer(s))
            presets_layout.addWidget(btn)
        timer_layout.addLayout(presets_layout)

        # Active Timers Queue Scroll Area
        timer_layout.addWidget(QLabel("ACTIVE QUEUE:"), alignment=Qt.AlignTop)
        
        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setStyleSheet("border: none; background: transparent;")
        
        self.queue_widget = QWidget()
        self.queue_widget.setStyleSheet("background: transparent;")
        self.queue_layout = QVBoxLayout(self.queue_widget)
        self.queue_layout.setSpacing(8)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        
        self.queue_scroll.setWidget(self.queue_widget)
        timer_layout.addWidget(self.queue_scroll)

        main_layout.addWidget(timer_panel, stretch=1)
        self.setLayout(main_layout)

    # =====================================================================
    # STOPWATCH CONTROLS
    # =====================================================================
    def toggle_stopwatch(self):
        if self.sw_running:
            self.pause_stopwatch()
        else:
            self.start_stopwatch()

    def start_stopwatch(self):
        if self.sw_running:
            return

        self.sw_timer.start(10)
        self.btn_sw_start.setText("PAUSE")
        self.btn_sw_start.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 170, 255, 20);
                color: #00aaff;
                border: 1px solid #00aaff;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 170, 255, 50);
            }
        """)
        self.btn_sw_lap.setEnabled(True)
        self.sw_running = True

    def pause_stopwatch(self):
        if not self.sw_running:
            return

        self.sw_timer.stop()
        self.btn_sw_start.setText("RESUME")
        self.btn_sw_start.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 170, 20);
                color: #00ffaa;
                border: 1px solid #00ffaa;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 170, 50);
            }
        """)
        self.btn_sw_lap.setEnabled(False)
        self.sw_running = False

    def tick_stopwatch(self):
        self.sw_time_ms += 10
        
        # Update display values
        total_sec = self.sw_time_ms // 1000
        ms = (self.sw_time_ms % 1000) // 10
        minutes = total_sec // 60
        sec = total_sec % 60
        hours = minutes // 60
        minutes = minutes % 60
        
        self.sw_display.setText(f"{hours:02d}:{minutes:02d}:{sec:02d}.{ms:02d}")
        
        # Circle progress ratio of active seconds
        self.sw_anim.set_progress((self.sw_time_ms % 60000) / 60000.0)

    def record_lap(self):
        lap_time_str = self.sw_display.text()
        lap_num = len(self.sw_laps) + 1
        self.sw_laps.append(lap_time_str)
        
        # Update UI Table
        row_pos = self.laps_table.rowCount()
        self.laps_table.insertRow(row_pos)
        self.laps_table.setItem(row_pos, 0, QTableWidgetItem(f"Lap {lap_num}"))
        self.laps_table.setItem(row_pos, 1, QTableWidgetItem(lap_time_str))
        self.laps_table.scrollToBottom()

    def reset_stopwatch(self):
        self.sw_timer.stop()
        self.setup_stopwatch_state()
        self.sw_display.setText("00:00:00.00")
        self.sw_anim.set_progress(0)
        self.btn_sw_start.setText("START")
        self.btn_sw_start.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 170, 20);
                color: #00ffaa;
                border: 1px solid #00ffaa;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 170, 50);
            }
        """)
        self.btn_sw_lap.setEnabled(False)
        self.laps_table.setRowCount(0)

    # =====================================================================
    # TIMER CONTROLS
    # =====================================================================
    def deploy_preset_timer(self, total_seconds):
        self.start_countdown_timer(total_seconds)

    def deploy_custom_timer(self):
        hrs = self.spin_h.value()
        mins = self.spin_m.value()
        secs = self.spin_s.value()
        
        total_seconds = (hrs * 3600) + (mins * 60) + secs
        if total_seconds > 0:
            self.start_countdown_timer(total_seconds)

    def start_countdown_timer(self, total_seconds):
        timer_id = str(uuid.uuid4())
        label = f"Timer ({total_seconds // 60}m)"
        self.scheduler.start_timer(timer_id, total_seconds, label)
        play_notification_beep()
        self.refresh_timer_queue()

    def refresh_timer_queue(self):
        """
        Dynamically builds list cards of active countdown items.
        Called once every second synchronized with system clock ticks.
        """
        # Clear existing layout children
        for i in reversed(range(self.queue_layout.count())):
            widget = self.queue_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Repopulate
        active_list = self.scheduler.active_timers
        if not active_list:
            lbl = QLabel("No active countdown runs.")
            lbl.setFont(QFont("Consolas", 10))
            lbl.setStyleSheet("color: rgba(255,255,255, 100); border: none;")
            self.queue_layout.addWidget(lbl)
            return

        for timer in active_list:
            card = QWidget()
            card.setStyleSheet("""
                QWidget {
                    background-color: rgba(10, 10, 15, 200);
                    border: 1px solid rgba(0, 170, 255, 30);
                    border-radius: 8px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            
            # Glowing indicator
            indicator = CircularTimerAnimation(QColor(0, 170, 255))
            ratio = timer['seconds_left'] / float(timer['total'])
            indicator.set_progress(ratio)
            indicator.setMaximumSize(30, 30)
            card_layout.addWidget(indicator)

            # Timer details
            time_left_sec = timer['seconds_left']
            h = time_left_sec // 3600
            m = (time_left_sec % 3600) // 60
            s = time_left_sec % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"

            lbl_time = QLabel(f"{timer['label']}: {time_str}")
            lbl_time.setFont(QFont("Consolas", 10, QFont.Bold))
            lbl_time.setStyleSheet("color: white; border: none; background: transparent;")
            card_layout.addWidget(lbl_time, stretch=1)

            # Cancel button
            btn_del = QPushButton("✕")
            btn_del.setFont(QFont("Consolas", 10, QFont.Bold))
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 50, 50, 20);
                    color: #ff5252;
                    border: 1px solid #ff5252;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 50, 50, 60);
                }
            """)
            btn_del.clicked.connect(lambda checked, tid=timer['id']: self.cancel_timer(tid))
            card_layout.addWidget(btn_del)
            
            self.queue_layout.addWidget(card)

    def cancel_timer(self, timer_id):
        self.scheduler.stop_timer(timer_id)
        self.refresh_timer_queue()
