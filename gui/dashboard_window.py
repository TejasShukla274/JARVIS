# gui/dashboard_window.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Productivity Dashboard — Shell window with sidebar navigation
# and stacked tab views.
# ─────────────────────────────────────────────────────────────────────────────

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget, QSystemTrayIcon, QStyle, QMenu, QAction, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from scheduler.background_scheduler import get_scheduler
from gui.dashboard_tab import DashboardTab
from gui.calendar_tab import CalendarTab
from gui.tasks_tab import TasksTab
from gui.reminders_tab import RemindersTab
from gui.alarms_tab import AlarmsTab
from gui.stopwatch_timer_tab import StopwatchTimerTab
from gui.alarm_popup import AlarmPopup
from gui import styles

from utils.audio_player import play_notification_beep


class DashboardWindow(QMainWindow):
    """
    Unified Productivity Dashboard — sidebar navigation, stacked views,
    system tray, and background scheduler integration.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS PRODUCTIVITY COCKPIT")
        self.resize(1200, 780)
        self.setStyleSheet(
            f"background-color: {styles.BG_DEEPEST}; color: white;"
        )
        self.center_on_screen()
        self.setup_ui()
        self.setup_system_tray()

        # Scheduler connection
        self.scheduler = get_scheduler()
        self.scheduler.alarm_triggered.connect(self.on_alarm_fired)
        self.scheduler.reminder_triggered.connect(self.on_reminder_fired)
        self.scheduler.timer_completed.connect(self.on_timer_fired)
        self.active_popups = []

        if not self.scheduler.isRunning():
            self.scheduler.start()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    # ── UI setup ─────────────────────────────────────────────────────────

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main = QHBoxLayout(central)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(10)

        # ═══════════════════════════════════════════════════════════════
        # SIDEBAR
        # ═══════════════════════════════════════════════════════════════
        sidebar = QWidget()
        sidebar.setStyleSheet(styles.SIDEBAR_STYLE)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(14, 18, 14, 18)
        sb.setSpacing(8)

        lbl_name = QLabel("J.A.R.V.I.S")
        lbl_name.setFont(QFont("Consolas", 18, QFont.Bold))
        lbl_name.setStyleSheet(
            f"color: {styles.CYAN}; letter-spacing: 3px; border: none; "
            "background: transparent;"
        )
        lbl_name.setAlignment(Qt.AlignCenter)
        sb.addWidget(lbl_name)

        lbl_sub = QLabel("PRODUCTIVITY SUITE")
        lbl_sub.setFont(QFont("Consolas", 7, QFont.Bold))
        lbl_sub.setStyleSheet(styles.SUBHEADER_LABEL)
        lbl_sub.setAlignment(Qt.AlignCenter)
        sb.addWidget(lbl_sub)
        sb.addSpacing(12)

        # Navigation buttons
        self.nav_buttons = []
        self._active_tab_index = 0

        nav_tabs = [
            ("⊞  DASHBOARD",      0, styles.GREEN),
            ("📅  CALENDAR",       1, styles.CYAN),
            ("📋  TASKS",          2, styles.AMBER),
            ("🔔  REMINDERS",      3, styles.GREEN),
            ("⏰  ALARMS",         4, styles.RED),
            ("⏱  CHRONO & TIMERS", 5, styles.CYAN),
        ]

        for label, idx, color in nav_tabs:
            btn = QPushButton(label)
            btn.setFont(QFont("Consolas", 9, QFont.Bold))
            btn.clicked.connect(
                lambda checked, i=idx: self.switch_tab(i)
            )
            sb.addWidget(btn)
            self.nav_buttons.append((btn, color))

        sb.addStretch()

        btn_hide = QPushButton("✕  MINIMIZE HUD")
        btn_hide.setFont(QFont("Consolas", 9, QFont.Bold))
        btn_hide.setStyleSheet(styles.button_style(styles.RED))
        btn_hide.clicked.connect(self.hide)
        sb.addWidget(btn_hide)

        main.addWidget(sidebar, stretch=1)

        # ═══════════════════════════════════════════════════════════════
        # STACKED VIEWS
        # ═══════════════════════════════════════════════════════════════
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")

        self.tab_dashboard = DashboardTab()
        self.tab_calendar = CalendarTab()
        self.tab_tasks = TasksTab()
        self.tab_reminders = RemindersTab()
        self.tab_alarms = AlarmsTab()
        self.tab_stopwatch = StopwatchTimerTab()

        self.stack.addWidget(self.tab_dashboard)   # 0
        self.stack.addWidget(self.tab_calendar)     # 1
        self.stack.addWidget(self.tab_tasks)        # 2
        self.stack.addWidget(self.tab_reminders)    # 3
        self.stack.addWidget(self.tab_alarms)       # 4
        self.stack.addWidget(self.tab_stopwatch)    # 5

        main.addWidget(self.stack, stretch=5)

        # Set initial tab
        self.switch_tab(0)

    # ── Tab switching ────────────────────────────────────────────────────

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        self._active_tab_index = index

        # Refresh tab data on activation
        if index == 0:
            self.tab_dashboard.refresh_upcoming_and_stats(force=True)
        elif index == 1:
            self.tab_calendar.render_calendar()
        elif index == 2:
            self.tab_tasks.refresh_tasks()
        elif index == 3:
            self.tab_reminders.refresh_reminders_list()
        elif index == 4:
            self.tab_alarms.refresh_alarms_list()
        elif index == 5:
            self.tab_stopwatch.refresh_timer_queue()

        # Update sidebar button highlights — FIXED: clean style replacement
        for idx, (btn, color) in enumerate(self.nav_buttons):
            btn.setStyleSheet(
                styles.nav_button_style(color, active=(idx == index))
            )

    # ── System tray ──────────────────────────────────────────────────────

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(
            self.style().standardIcon(QStyle.SP_ComputerIcon)
        )

        show_action = QAction("Open JARVIS Cockpit", self)
        show_action.triggered.connect(self.showNormal)

        exit_action = QAction("Shutdown Productivity", self)
        exit_action.triggered.connect(self.quit_app)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()

    def quit_app(self):
        self.scheduler.stop()
        sys.exit(0)

    # ── Alarm / Reminder / Timer handlers ────────────────────────────────

    def on_alarm_fired(self, alarm_dict):
        popup = AlarmPopup(
            title="Alarm Ringing",
            label=alarm_dict["label"] or "Wake up call",
            is_reminder=False,
            custom_sound=alarm_dict.get("custom_sound"),
            volume=alarm_dict.get("volume") or 85,
        )
        self.show_popup(popup)
        self.switch_tab(4)

    def on_reminder_fired(self, reminder_dict):
        popup = AlarmPopup(
            title="Reminder Alert",
            label=reminder_dict["text"],
            is_reminder=True,
            volume=65,
        )
        self.show_popup(popup)
        self.switch_tab(3)

    def on_timer_fired(self, timer_dict):
        popup = AlarmPopup(
            title="Timer Completed",
            label=timer_dict["label"] or "Countdown finished",
            is_reminder=True,
            volume=70,
        )
        self.show_popup(popup)
        self.switch_tab(5)

    def show_popup(self, popup):
        self.active_popups.append(popup)
        popup.destroyed.connect(
            lambda _=None, ref=popup: self.remove_popup(ref)
        )
        popup.show()
        popup.raise_()
        popup.activateWindow()

    def remove_popup(self, popup):
        if popup in self.active_popups:
            self.active_popups.remove(popup)

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_app()


# ── Global singleton ─────────────────────────────────────────────────────
_global_window = None


def get_dashboard_window():
    global _global_window
    if _global_window is None:
        _global_window = DashboardWindow()
    return _global_window


def launch_dashboard():
    """Standalone test runner."""
    app = QApplication(sys.argv)
    win = get_dashboard_window()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch_dashboard()
