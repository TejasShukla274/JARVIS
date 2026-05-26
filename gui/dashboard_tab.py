# gui/dashboard_tab.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Productivity Dashboard — Main Overview Tab
# Futuristic HUD with live clock, world clocks, JARVIS core,
# focus timer, analytics, and upcoming agenda.
# ─────────────────────────────────────────────────────────────────────────────

import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QRadialGradient
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF

from database.db_manager import (
    get_alarms, get_reminders, get_tasks, get_events, add_timer_log
)
from utils.audio_player import play_notification_beep, speak_alert
from utils.time_service import (
    now_local, now_naive, format_clock, format_date, get_world_clocks
)
from gui.clock_widgets import FuturisticDial, JarvisCoreGlyph, WorldClockWidget
from gui import styles


class GlassPanel(QFrame):
    """Glassmorphism panel with neon border glow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(styles.GLASS_PANEL)


class StatCard(QFrame):
    """Small analytics stat card with count and label."""

    def __init__(self, label_text, color, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(2, 8, 14, 200);
                border: 1px solid {styles.CYAN_FAINT};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        self.value_label = QLabel("0")
        self.value_label.setFont(QFont("Consolas", 22, QFont.Bold))
        self.value_label.setStyleSheet(
            f"color: {color}; border: none; background: transparent;"
        )
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        caption = QLabel(label_text)
        caption.setFont(QFont("Consolas", 7, QFont.Bold))
        caption.setStyleSheet(styles.DIM_LABEL)
        caption.setAlignment(Qt.AlignCenter)
        layout.addWidget(caption)

    def set_value(self, val):
        self.value_label.setText(str(val))


class DashboardTab(QWidget):
    """
    Main overview tab — the JARVIS productivity cockpit.
    """

    def __init__(self):
        super().__init__()
        self.pomodoro_state = "idle"
        self.pomodoro_seconds_left = 25 * 60
        self.pomodoro_total_seconds = 25 * 60
        self.completed_sessions = 0
        self.world_clock_widgets = []

        self.setup_ui()

        # Connect scheduler tick
        from scheduler.background_scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.second_tick.connect(self.on_system_tick)

        # Local high-frequency clock update
        self.local_tick = QTimer(self)
        self.local_tick.timeout.connect(self.update_clock)
        self.local_tick.start(1000)

        # Initial render
        self.update_clock()
        self.update_world_clocks()
        self.refresh_upcoming_and_stats()
        self.update_focus_dial()

    # ── UI Construction ──────────────────────────────────────────────────

    def setup_ui(self):
        root = QGridLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(10)

        # ═══════════════════════════════════════════════════════════════
        # ROW 0, COL 0-1 : LOCAL CLOCK + DATE
        # ═══════════════════════════════════════════════════════════════
        clock_panel = GlassPanel()
        clock_layout = QVBoxLayout(clock_panel)
        clock_layout.setContentsMargins(20, 14, 20, 14)
        clock_layout.setSpacing(4)

        clock_header = QLabel("SYSTEM TIME")
        clock_header.setFont(QFont("Consolas", 8, QFont.Bold))
        clock_header.setStyleSheet(styles.HEADER_LABEL)
        clock_layout.addWidget(clock_header)

        self.lbl_clock = QLabel("00:00:00 PM")
        self.lbl_clock.setFont(QFont("Consolas", 38, QFont.Bold))
        self.lbl_clock.setStyleSheet(
            f"color: {styles.WHITE}; border: none; background: transparent;"
        )
        clock_layout.addWidget(self.lbl_clock)

        self.lbl_date = QLabel("Loading...")
        self.lbl_date.setFont(QFont("Consolas", 10, QFont.Bold))
        self.lbl_date.setStyleSheet(styles.HEADER_LABEL)
        clock_layout.addWidget(self.lbl_date)

        root.addWidget(clock_panel, 0, 0, 1, 2)

        # ═══════════════════════════════════════════════════════════════
        # ROW 0, COL 2 : JARVIS CORE ORB
        # ═══════════════════════════════════════════════════════════════
        core_panel = GlassPanel()
        core_layout = QVBoxLayout(core_panel)
        core_layout.setContentsMargins(8, 8, 8, 8)
        core_layout.addWidget(JarvisCoreGlyph(), stretch=1)
        root.addWidget(core_panel, 0, 2, 1, 1)

        # ═══════════════════════════════════════════════════════════════
        # ROW 0, COL 3 : WORLD CLOCKS
        # ═══════════════════════════════════════════════════════════════
        world_panel = GlassPanel()
        world_layout = QVBoxLayout(world_panel)
        world_layout.setContentsMargins(12, 10, 12, 10)
        world_layout.setSpacing(4)

        world_header = QLabel("WORLD CLOCK")
        world_header.setFont(QFont("Consolas", 9, QFont.Bold))
        world_header.setStyleSheet(styles.HEADER_LABEL)
        world_layout.addWidget(world_header)

        # Create 6 world clock tiles in a 3x2 grid
        wc_grid = QGridLayout()
        wc_grid.setSpacing(5)
        self.world_clock_widgets = []

        clocks_data = get_world_clocks()
        for i, data in enumerate(clocks_data):
            wc = WorldClockWidget(
                city=data["city"], time_str=data["time_str"],
                label=data["label"], date_str=data["date_str"]
            )
            row_i = i // 2
            col_i = i % 2
            wc_grid.addWidget(wc, row_i, col_i)
            self.world_clock_widgets.append(wc)

        world_layout.addLayout(wc_grid)
        root.addWidget(world_panel, 0, 3, 2, 1)

        # ═══════════════════════════════════════════════════════════════
        # ROW 1, COL 0 : FOCUS TIMER (POMODORO) with dial
        # ═══════════════════════════════════════════════════════════════
        focus_panel = GlassPanel()
        focus_layout = QVBoxLayout(focus_panel)
        focus_layout.setContentsMargins(14, 12, 14, 12)
        focus_layout.setSpacing(6)

        focus_title = QLabel("FOCUS TIMER")
        focus_title.setFont(QFont("Consolas", 10, QFont.Bold))
        focus_title.setStyleSheet(styles.SECTION_LABEL)
        focus_layout.addWidget(focus_title)

        self.focus_dial = FuturisticDial(QColor(styles.GREEN))
        self.focus_dial.show_hand = False
        self.focus_dial.setMinimumSize(180, 180)
        focus_layout.addWidget(self.focus_dial, stretch=1)

        focus_buttons = QHBoxLayout()
        focus_buttons.setSpacing(8)

        self.btn_pomo_control = QPushButton("Start")
        self.btn_pomo_control.setStyleSheet(styles.button_style(styles.GREEN))
        self.btn_pomo_control.clicked.connect(self.toggle_pomodoro)

        self.btn_pomo_reset = QPushButton("Reset")
        self.btn_pomo_reset.setStyleSheet(styles.button_style(styles.RED))
        self.btn_pomo_reset.clicked.connect(self.reset_pomodoro)

        focus_buttons.addWidget(self.btn_pomo_control)
        focus_buttons.addWidget(self.btn_pomo_reset)
        focus_layout.addLayout(focus_buttons)

        self.lbl_sessions = QLabel("Sessions: 0")
        self.lbl_sessions.setFont(QFont("Consolas", 8))
        self.lbl_sessions.setStyleSheet(styles.DIM_LABEL)
        self.lbl_sessions.setAlignment(Qt.AlignCenter)
        focus_layout.addWidget(self.lbl_sessions)

        root.addWidget(focus_panel, 1, 0, 2, 1)

        # ═══════════════════════════════════════════════════════════════
        # ROW 1, COL 1-2 : ANALYTICS GRID
        # ═══════════════════════════════════════════════════════════════
        stats_panel = GlassPanel()
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(14, 12, 14, 12)
        stats_layout.setSpacing(8)

        stats_header = QLabel("MISSION ANALYTICS")
        stats_header.setFont(QFont("Consolas", 10, QFont.Bold))
        stats_header.setStyleSheet(styles.HEADER_LABEL)
        stats_layout.addWidget(stats_header)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)

        self.stat_tasks = StatCard("TASKS", styles.AMBER)
        self.stat_reminders = StatCard("REMINDERS", styles.GREEN)
        self.stat_events = StatCard("EVENTS", styles.CYAN)
        self.stat_alarms = StatCard("ALARMS", styles.RED)

        stats_grid.addWidget(self.stat_tasks, 0, 0)
        stats_grid.addWidget(self.stat_reminders, 0, 1)
        stats_grid.addWidget(self.stat_events, 1, 0)
        stats_grid.addWidget(self.stat_alarms, 1, 1)
        stats_layout.addLayout(stats_grid)

        root.addWidget(stats_panel, 1, 1, 1, 2)

        # ═══════════════════════════════════════════════════════════════
        # ROW 2, COL 1-3 : UPCOMING AGENDA
        # ═══════════════════════════════════════════════════════════════
        agenda_panel = GlassPanel()
        agenda_layout = QVBoxLayout(agenda_panel)
        agenda_layout.setContentsMargins(14, 12, 14, 12)
        agenda_layout.setSpacing(6)

        agenda_header = QLabel("UPCOMING PRIORITY ACTIONS")
        agenda_header.setFont(QFont("Consolas", 10, QFont.Bold))
        agenda_header.setStyleSheet(styles.SECTION_LABEL)
        agenda_layout.addWidget(agenda_header)

        self.lbl_upcoming = QLabel("Loading agenda protocols...")
        self.lbl_upcoming.setFont(QFont("Consolas", 10))
        self.lbl_upcoming.setStyleSheet(styles.BODY_LABEL)
        self.lbl_upcoming.setWordWrap(True)
        self.lbl_upcoming.setAlignment(Qt.AlignTop)
        agenda_layout.addWidget(self.lbl_upcoming, stretch=1)

        root.addWidget(agenda_panel, 2, 1, 1, 3)

        # ── Grid stretch ─────────────────────────────────────────────────
        root.setColumnStretch(0, 2)
        root.setColumnStretch(1, 2)
        root.setColumnStretch(2, 2)
        root.setColumnStretch(3, 3)
        root.setRowStretch(0, 2)
        root.setRowStretch(1, 2)
        root.setRowStretch(2, 3)

    # ── Clock updates ────────────────────────────────────────────────────

    def update_clock(self):
        self.lbl_clock.setText(format_clock())
        self.lbl_date.setText(format_date().upper())

    def update_world_clocks(self):
        clocks = get_world_clocks()
        for i, data in enumerate(clocks):
            if i < len(self.world_clock_widgets):
                self.world_clock_widgets[i].set_data(
                    data["city"], data["time_str"],
                    data["label"], data["date_str"]
                )

    # ── Pomodoro controls ────────────────────────────────────────────────

    def toggle_pomodoro(self):
        if self.pomodoro_state == "idle":
            self.pomodoro_state = "focus"
            self.pomodoro_seconds_left = self.pomodoro_total_seconds
            self.btn_pomo_control.setText("Pause")
            self.btn_pomo_control.setStyleSheet(
                styles.button_style(styles.CYAN)
            )
            play_notification_beep()
        elif self.pomodoro_state == "paused":
            self.pomodoro_state = "focus"
            self.btn_pomo_control.setText("Pause")
            self.btn_pomo_control.setStyleSheet(
                styles.button_style(styles.CYAN)
            )
            play_notification_beep()
        else:
            self.pomodoro_state = "paused"
            self.btn_pomo_control.setText("Resume")
            self.btn_pomo_control.setStyleSheet(
                styles.button_style(styles.GREEN)
            )
            play_notification_beep()
        self.update_focus_dial()

    def reset_pomodoro(self):
        self.pomodoro_state = "idle"
        self.pomodoro_seconds_left = 25 * 60
        self.pomodoro_total_seconds = 25 * 60
        self.btn_pomo_control.setText("Start")
        self.btn_pomo_control.setStyleSheet(
            styles.button_style(styles.GREEN)
        )
        self.update_focus_dial()

    def pomodoro_tick(self):
        if self.pomodoro_state != "focus":
            return
        self.pomodoro_seconds_left -= 1
        if self.pomodoro_seconds_left <= 0:
            self.completed_sessions += 1
            self.lbl_sessions.setText(
                f"Sessions: {self.completed_sessions}"
            )
            add_timer_log(
                self.pomodoro_total_seconds,
                now_naive().isoformat(timespec="seconds"),
                "Pomodoro Focus"
            )
            speak_alert("Focus timer completed, Sir.")
            self.pomodoro_state = "idle"
            self.pomodoro_seconds_left = 25 * 60
            self.pomodoro_total_seconds = 25 * 60
            self.btn_pomo_control.setText("Start")
            self.btn_pomo_control.setStyleSheet(
                styles.button_style(styles.GREEN)
            )
        self.update_focus_dial()

    def update_focus_dial(self):
        total = max(1, self.pomodoro_total_seconds)
        ratio = self.pomodoro_seconds_left / float(total)
        mins = self.pomodoro_seconds_left // 60
        secs = self.pomodoro_seconds_left % 60
        state_text = "READY"
        if self.pomodoro_state == "focus":
            state_text = "FOCUSING"
        elif self.pomodoro_state == "paused":
            state_text = "PAUSED"
        self.focus_dial.set_values(
            progress=ratio,
            center_text=f"{mins:02d}:{secs:02d}",
            sub_text=state_text
        )

    # ── System tick handler ──────────────────────────────────────────────

    def on_system_tick(self):
        self.pomodoro_tick()
        self.update_world_clocks()
        self.refresh_upcoming_and_stats()

    # ── Stats & Agenda ───────────────────────────────────────────────────

    _refresh_counter = 0

    def refresh_upcoming_and_stats(self, force=False):
        """Refresh analytics and upcoming agenda from database."""
        # Throttle to every 5 seconds (called every tick) unless forced
        if not force:
            DashboardTab._refresh_counter += 1
            if DashboardTab._refresh_counter % 5 != 0:
                return

        tasks = get_tasks()
        reminders = get_reminders(include_completed=False)
        events = get_events()
        alarms = [a for a in get_alarms() if a.get("is_active")]

        self.stat_tasks.set_value(
            len([t for t in tasks if t["status"].lower() != "done"])
        )
        self.stat_reminders.set_value(len(reminders))
        self.stat_events.set_value(len(events))
        self.stat_alarms.set_value(len(alarms))

        now = now_naive()
        lines = []

        # Next reminder
        future_rem = [
            r for r in reminders
            if datetime.datetime.fromisoformat(r["datetime"]) > now
        ]
        if future_rem:
            r = future_rem[0]
            dt = datetime.datetime.fromisoformat(r["datetime"])
            diff = dt - now
            mins_left = int(diff.total_seconds() // 60)
            h, m = divmod(mins_left, 60)
            lines.append(
                f"⏰  Next reminder: {r['text']} (in {h}h {m}m)"
            )
        else:
            lines.append("⏰  Next reminder: None scheduled")

        # Next event
        future_ev = [
            e for e in events
            if datetime.datetime.fromisoformat(e["start_time"]) > now
        ]
        if future_ev:
            e = future_ev[0]
            dt = datetime.datetime.fromisoformat(e["start_time"])
            lines.append(
                f"📅  Next event: {e['title']} on "
                f"{dt.strftime('%d %b, %I:%M %p')}"
            )
        else:
            lines.append("📅  Next event: None scheduled")

        # Overdue tasks
        overdue = []
        for t in tasks:
            if t["status"].lower() != "done" and t["due_date"]:
                due = datetime.datetime.strptime(
                    t["due_date"], "%Y-%m-%d"
                ).date()
                if due < now.date():
                    overdue.append(t["title"])

        if overdue:
            lines.append(f"⚠️  Overdue tasks: {len(overdue)}")
            for title in overdue[:3]:
                lines.append(f"    • {title}")
        else:
            lines.append("✅  No overdue tasks")

        lines.append(f"🎯  Focus sessions today: {self.completed_sessions}")

        self.lbl_upcoming.setText("\n".join(lines))
