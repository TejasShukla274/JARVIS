# gui/stopwatch_timer_tab.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Stopwatch & Timer — Unified view with FuturisticDial animations.
# ─────────────────────────────────────────────────────────────────────────────

import uuid

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QScrollArea, QFrame, QLineEdit
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QElapsedTimer

from scheduler.background_scheduler import get_scheduler
from utils.audio_player import play_notification_beep
from gui.clock_widgets import FuturisticDial
from gui import styles


def _fmt_ms(total_ms):
    total_ms = max(0, int(total_ms))
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    seconds = (total_ms % 60000) // 1000
    centiseconds = (total_ms % 1000) // 10
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _fmt_seconds(seconds):
    seconds = max(0, int(round(seconds)))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class StopwatchTimerTab(QWidget):
    """Unified Stopwatch + Timer panel with futuristic animated dials."""

    def __init__(self):
        super().__init__()
        self.scheduler = get_scheduler()
        self.sw_running = False
        self.sw_base_ms = 0
        self.sw_elapsed = QElapsedTimer()
        self.sw_laps = []
        self.timer_cards = {}

        self.setup_ui()

        # 60fps render loop for smooth animations
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.render_live_state)
        self.frame_timer.start(16)

        # Scheduler tick for timer queue refresh
        self.scheduler.second_tick.connect(self.refresh_timer_queue)

    # ── UI ───────────────────────────────────────────────────────────────

    def setup_ui(self):
        main = QHBoxLayout(self)
        main.setSpacing(14)
        main.setContentsMargins(8, 8, 8, 8)

        # ═══════════════════════════════════════════════════════════════
        # LEFT: STOPWATCH
        # ═══════════════════════════════════════════════════════════════
        stopwatch_panel = QFrame()
        stopwatch_panel.setStyleSheet(styles.GLASS_PANEL)
        sw = QVBoxLayout(stopwatch_panel)
        sw.setContentsMargins(18, 16, 18, 16)
        sw.setSpacing(10)

        sw_title = QLabel("STOPWATCH")
        sw_title.setFont(QFont("Consolas", 12, QFont.Bold))
        sw_title.setStyleSheet(styles.SECTION_LABEL)
        sw.addWidget(sw_title)

        self.sw_dial = FuturisticDial(QColor(styles.GREEN))
        self.sw_dial.show_hand = True
        sw.addWidget(self.sw_dial, stretch=3)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.btn_sw_lap = QPushButton("Lap")
        self.btn_sw_lap.setStyleSheet(styles.button_style(styles.CYAN))
        self.btn_sw_lap.clicked.connect(self.record_lap)
        self.btn_sw_lap.setEnabled(False)

        self.btn_sw_reset = QPushButton("Reset")
        self.btn_sw_reset.setStyleSheet(styles.button_style(styles.RED))
        self.btn_sw_reset.clicked.connect(self.reset_stopwatch)

        self.btn_sw_start = QPushButton("Start")
        self.btn_sw_start.setStyleSheet(styles.button_style(styles.GREEN))
        self.btn_sw_start.clicked.connect(self.toggle_stopwatch)

        controls.addWidget(self.btn_sw_lap)
        controls.addWidget(self.btn_sw_reset)
        controls.addStretch()
        controls.addWidget(self.btn_sw_start)
        sw.addLayout(controls)

        self.laps_table = QTableWidget(0, 3)
        self.laps_table.setHorizontalHeaderLabels(["Lap", "Split", "Delta"])
        self.laps_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.laps_table.setStyleSheet(styles.TABLE_STYLE)
        sw.addWidget(self.laps_table, stretch=2)
        main.addWidget(stopwatch_panel, stretch=1)

        # ═══════════════════════════════════════════════════════════════
        # RIGHT: TIMERS
        # ═══════════════════════════════════════════════════════════════
        timer_panel = QFrame()
        timer_panel.setStyleSheet(styles.GLASS_PANEL)
        tm = QVBoxLayout(timer_panel)
        tm.setContentsMargins(18, 16, 18, 16)
        tm.setSpacing(10)

        tm_title = QLabel("TIMERS")
        tm_title.setFont(QFont("Consolas", 12, QFont.Bold))
        tm_title.setStyleSheet(styles.HEADER_LABEL)
        tm.addWidget(tm_title)

        self.timer_dial = FuturisticDial(QColor(styles.CYAN))
        self.timer_dial.show_hand = False
        tm.addWidget(self.timer_dial, stretch=3)

        # Create timer row
        create_row = QHBoxLayout()
        create_row.setSpacing(6)

        self.timer_label = QLineEdit()
        self.timer_label.setPlaceholderText("Label")
        self.timer_label.setText("Timer")
        self.timer_label.setStyleSheet(styles.INPUT_STYLE)

        self.spin_h = QSpinBox()
        self.spin_h.setRange(0, 23)
        self.spin_h.setSuffix(" h")
        self.spin_m = QSpinBox()
        self.spin_m.setRange(0, 59)
        self.spin_m.setSuffix(" m")
        self.spin_m.setValue(5)
        self.spin_s = QSpinBox()
        self.spin_s.setRange(0, 59)
        self.spin_s.setSuffix(" s")

        for spin in (self.spin_h, self.spin_m, self.spin_s):
            spin.setStyleSheet(styles.INPUT_STYLE)

        create_row.addWidget(self.timer_label, stretch=2)
        create_row.addWidget(self.spin_h)
        create_row.addWidget(self.spin_m)
        create_row.addWidget(self.spin_s)
        tm.addLayout(create_row)

        # Action row
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        self.btn_timer_start = QPushButton("Start Timer")
        self.btn_timer_start.setStyleSheet(styles.button_style(styles.GREEN))
        self.btn_timer_start.clicked.connect(self.deploy_custom_timer)
        action_row.addWidget(self.btn_timer_start)

        for label, seconds in (
            ("1 min", 60), ("5 min", 300),
            ("10 min", 600), ("25 min", 1500)
        ):
            btn = QPushButton(label)
            btn.setStyleSheet(styles.button_style(styles.CYAN))
            btn.clicked.connect(
                lambda checked, s=seconds: self.deploy_preset_timer(s)
            )
            action_row.addWidget(btn)
        tm.addLayout(action_row)

        # Active timers queue
        queue_title = QLabel("ACTIVE COUNTDOWNS")
        queue_title.setFont(QFont("Consolas", 9, QFont.Bold))
        queue_title.setStyleSheet(styles.DIM_LABEL)
        tm.addWidget(queue_title)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setStyleSheet(styles.SCROLL_STYLE)
        self.queue_widget = QWidget()
        self.queue_widget.setStyleSheet("background: transparent;")
        self.queue_layout = QVBoxLayout(self.queue_widget)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(8)
        self.queue_scroll.setWidget(self.queue_widget)
        tm.addWidget(self.queue_scroll, stretch=2)

        main.addWidget(timer_panel, stretch=1)
        self.refresh_timer_queue()
        self.render_live_state()

    # ── Stopwatch helpers ────────────────────────────────────────────────

    def current_stopwatch_ms(self):
        if self.sw_running and self.sw_elapsed.isValid():
            return self.sw_base_ms + self.sw_elapsed.elapsed()
        return self.sw_base_ms

    # ── Stopwatch controls ───────────────────────────────────────────────

    def toggle_stopwatch(self):
        if self.sw_running:
            self.pause_stopwatch()
        else:
            self.start_stopwatch()

    def start_stopwatch(self):
        if self.sw_running:
            return
        self.sw_elapsed.restart()
        self.sw_running = True
        self.btn_sw_start.setText("Pause")
        self.btn_sw_start.setStyleSheet(styles.button_style(styles.CYAN))
        self.btn_sw_lap.setEnabled(True)

    def pause_stopwatch(self):
        if not self.sw_running:
            return
        self.sw_base_ms = self.current_stopwatch_ms()
        self.sw_running = False
        self.btn_sw_start.setText("Resume")
        self.btn_sw_start.setStyleSheet(styles.button_style(styles.GREEN))
        self.btn_sw_lap.setEnabled(False)

    def reset_stopwatch(self):
        self.sw_running = False
        self.sw_base_ms = 0
        self.sw_laps = []
        self.laps_table.setRowCount(0)
        self.btn_sw_start.setText("Start")
        self.btn_sw_start.setStyleSheet(styles.button_style(styles.GREEN))
        self.btn_sw_lap.setEnabled(False)
        self.render_live_state()

    def record_lap(self):
        elapsed = self.current_stopwatch_ms()
        previous = self.sw_laps[-1] if self.sw_laps else 0
        self.sw_laps.append(elapsed)
        row = self.laps_table.rowCount()
        self.laps_table.insertRow(row)
        values = [
            f"{row + 1}", _fmt_ms(elapsed), _fmt_ms(elapsed - previous)
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            self.laps_table.setItem(row, col, item)
        self.laps_table.scrollToBottom()
        play_notification_beep()

    # ── Timer controls ───────────────────────────────────────────────────

    def deploy_preset_timer(self, total_seconds):
        self.start_countdown_timer(
            total_seconds, f"Timer ({_fmt_seconds(total_seconds)})"
        )

    def deploy_custom_timer(self):
        total = (self.spin_h.value() * 3600
                 + self.spin_m.value() * 60
                 + self.spin_s.value())
        if total <= 0:
            return
        label = self.timer_label.text().strip() or "Timer"
        self.start_countdown_timer(total, label)

    def start_countdown_timer(self, total_seconds, label="Timer"):
        timer_id = str(uuid.uuid4())
        self.scheduler.start_timer(timer_id, total_seconds, label)
        play_notification_beep()
        self.refresh_timer_queue()

    def refresh_timer_queue(self):
        """Rebuild timer queue cards from scheduler state."""
        for i in reversed(range(self.queue_layout.count())):
            widget = self.queue_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        timers = self.scheduler.get_active_timers()
        if not timers:
            empty = QLabel("No active timers.")
            empty.setFont(QFont("Consolas", 10))
            empty.setStyleSheet(styles.DIM_LABEL)
            self.queue_layout.addWidget(empty)
            self.timer_cards = {}
            return

        self.timer_cards = {}
        for timer in timers:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(2, 8, 14, 210);
                    border: 1px solid {styles.CYAN_GLOW};
                    border-radius: 8px;
                }}
            """)
            row = QHBoxLayout(card)
            row.setContentsMargins(10, 8, 10, 8)

            info = QLabel()
            info.setFont(QFont("Consolas", 10, QFont.Bold))
            info.setStyleSheet(styles.BODY_LABEL)
            row.addWidget(info, stretch=1)

            is_running = timer.get("status") == "running"

            pause = QPushButton("Pause" if is_running else "Resume")
            pause.setStyleSheet(styles.button_style(styles.CYAN, radius=6))
            pause.clicked.connect(
                lambda checked, tid=timer["id"]: self.toggle_timer_pause(tid)
            )

            reset = QPushButton("Reset")
            reset.setStyleSheet(styles.button_style(styles.AMBER, radius=6))
            reset.clicked.connect(
                lambda checked, tid=timer["id"]: self.reset_timer(tid)
            )

            cancel = QPushButton("X")
            cancel.setStyleSheet(styles.button_style(styles.RED, radius=6))
            cancel.clicked.connect(
                lambda checked, tid=timer["id"]: self.cancel_timer(tid)
            )

            row.addWidget(pause)
            row.addWidget(reset)
            row.addWidget(cancel)

            self.queue_layout.addWidget(card)
            self.timer_cards[timer["id"]] = (info, pause)

        self.update_timer_cards(timers)

    def update_timer_cards(self, timers):
        for timer in timers:
            widgets = self.timer_cards.get(timer["id"])
            if not widgets:
                continue
            info, pause = widgets
            left = timer.get(
                "remaining_seconds", timer.get("seconds_left", 0)
            )
            total = max(1, timer.get("total", 1))
            percent = int((left / total) * 100)
            status = timer.get("status", "running").upper()
            info.setText(
                f"{timer.get('label', 'Timer')}   "
                f"{_fmt_seconds(left)}   {percent}%   {status}"
            )
            pause.setText(
                "Pause" if timer.get("status") == "running" else "Resume"
            )

    def toggle_timer_pause(self, timer_id):
        timers = self.scheduler.get_active_timers()
        target = next((t for t in timers if t["id"] == timer_id), None)
        if not target:
            return
        if target.get("status") == "running":
            self.scheduler.pause_timer(timer_id)
        else:
            self.scheduler.resume_timer(timer_id)
        self.refresh_timer_queue()

    def reset_timer(self, timer_id):
        self.scheduler.reset_timer(timer_id)
        self.refresh_timer_queue()

    def cancel_timer(self, timer_id):
        self.scheduler.stop_timer(timer_id)
        self.refresh_timer_queue()

    # ── Live render (60fps) ──────────────────────────────────────────────

    def render_live_state(self):
        """Called ~60fps for smooth dial animations."""
        elapsed = self.current_stopwatch_ms()
        self.sw_dial.set_values(
            progress=(elapsed % 60000) / 60000.0,
            hand_ratio=(elapsed % 60000) / 60000.0,
            center_text=_fmt_ms(elapsed),
            sub_text="RUNNING" if self.sw_running else "READY"
        )

        timers = self.scheduler.get_active_timers()
        self.update_timer_cards(timers)
        if timers:
            primary = timers[0]
            left = primary.get(
                "remaining_seconds", primary.get("seconds_left", 0)
            )
            total = max(1, primary.get("total", 1))
            self.timer_dial.set_values(
                progress=left / float(total),
                center_text=_fmt_seconds(left),
                sub_text=primary.get("label", "Timer").upper()
            )
        else:
            self.timer_dial.set_values(
                progress=0, center_text="00:00:00", sub_text="READY"
            )
