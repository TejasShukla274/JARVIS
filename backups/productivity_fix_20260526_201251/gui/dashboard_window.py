# gui/dashboard_window.py

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QSystemTrayIcon, QStyle, QMenu, QAction
)
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtCore import Qt

from scheduler.background_scheduler import get_scheduler
from gui.dashboard_tab import DashboardTab
from gui.calendar_tab import CalendarTab
from gui.tasks_tab import TasksTab
from gui.reminders_tab import RemindersTab
from gui.alarms_tab import AlarmsTab
from gui.stopwatch_timer_tab import StopwatchTimerTab
from gui.alarm_popup import AlarmPopup

from utils.audio_player import play_notification_beep


class DashboardWindow(QMainWindow):
    """
    Unified Main Dashboard Window. Contains the navigation sidebar,
    stacked views for alarms, stopwatch, timers, reminders, tasks, and calendar.
    Hooks signals from background QThread scheduler safely.
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("JARVIS PRODUCTIVITY COCKPIT")
        self.resize(1100, 750)
        self.setStyleSheet("background-color: #050508; color: white;")
        
        # Center of screen
        self.center_on_screen()
        
        # Create core widgets
        self.setup_ui()
        self.setup_system_tray()
        
        # Connect Background Scheduler signals
        self.scheduler = get_scheduler()
        self.scheduler.alarm_triggered.connect(self.on_alarm_fired)
        self.scheduler.reminder_triggered.connect(self.on_reminder_fired)
        self.scheduler.timer_completed.connect(self.on_timer_fired)
        self.active_popups = []
        
        # Start background thread scheduler if not running
        if not self.scheduler.isRunning():
            self.scheduler.start()

    def center_on_screen(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # =====================================================================
        # SIDEBAR NAVIGATION PANEL
        # =====================================================================
        sidebar = QWidget()
        sidebar.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 15, 230);
                border: 1px solid rgba(0, 170, 255, 30);
                border-radius: 12px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(10)

        # Header HUD
        lbl_hud = QLabel("J.A.R.V.I.S")
        lbl_hud.setFont(QFont("Consolas", 18, QFont.Bold))
        lbl_hud.setStyleSheet("color: #00e5ff; letter-spacing: 2px; border: none; background: transparent;")
        lbl_hud.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_hud)

        lbl_sub = QLabel("PRODUCTIVITY SUITE")
        lbl_sub.setFont(QFont("Consolas", 8))
        lbl_sub.setStyleSheet("color: rgba(255, 255, 255, 100); letter-spacing: 1px; border: none; background: transparent;")
        lbl_sub.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_sub)
        sidebar_layout.addSpacing(15)

        # Nav Buttons list
        self.nav_buttons = []
        nav_tabs = [
            ("DASHBOARD COCKPIT", 0, "#00ffaa"),
            ("INTEGRATED CALENDAR", 1, "#00aaff"),
            ("KANBAN & TASKS", 2, "#ffaa00"),
            ("REMINDERS CORE", 3, "#00ffaa"),
            ("ALARM SCHEDULES", 4, "#ff3333"),
            ("CHRONOS & TIMERS", 5, "#00aaff")
        ]

        for label, idx, color in nav_tabs:
            btn = QPushButton(label)
            btn.setFont(QFont("Consolas", 9, QFont.Bold))
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: white;
                    background-color: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 6px;
                    padding: 12px 10px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid {color}90;
                    color: {color};
                }}
            """)
            # Workaround for loop value retention using default argument
            btn.clicked.connect(lambda checked, i=idx: self.switch_tab(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()
        
        # Power down button
        btn_hide = QPushButton("MINIMIZE HUD")
        btn_hide.setFont(QFont("Consolas", 9, QFont.Bold))
        btn_hide.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 50, 50, 20);
                color: #ff3333;
                border: 1px solid #ff3333;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 50);
            }
        """)
        btn_hide.clicked.connect(self.hide)
        sidebar_layout.addWidget(btn_hide)

        main_layout.addWidget(sidebar, stretch=1)

        # =====================================================================
        # CENTRAL STACKED VIEWS CONTAINER
        # =====================================================================
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
        
        # Instantiate Tab views
        self.tab_dashboard = DashboardTab()
        self.tab_calendar = CalendarTab()
        self.tab_tasks = TasksTab()
        self.tab_reminders = RemindersTab()
        self.tab_alarms = AlarmsTab()
        self.tab_stopwatch = StopwatchTimerTab()

        self.stack.addWidget(self.tab_dashboard)  # Index 0
        self.stack.addWidget(self.tab_calendar)   # Index 1
        self.stack.addWidget(self.tab_tasks)      # Index 2
        self.stack.addWidget(self.tab_reminders)  # Index 3
        self.stack.addWidget(self.tab_alarms)     # Index 4
        self.stack.addWidget(self.tab_stopwatch)  # Index 5

        main_layout.addWidget(self.stack, stretch=4)

        # Initial active styling
        self.switch_tab(0)

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        
        # Refresh contents on tab switches
        if index == 0:
            self.tab_dashboard.refresh_upcoming_and_stats()
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

        # Update button highlights
        for idx, btn in enumerate(self.nav_buttons):
            if idx == index:
                btn.setStyleSheet(btn.styleSheet() + "\nbackground-color: rgba(0, 170, 255, 20); color: #00e5ff; border: 1px solid #00e5ff;")
            else:
                # Reset standard styles
                btn.setStyleSheet(btn.styleSheet().split("\nbackground-color")[0])

    def setup_system_tray(self):
        """
        Creates background tray icon, enabling background persistence.
        """
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use standard windows system icon if file not found
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # Action menus
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
        
        # Double click to restore window
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()

    def quit_app(self):
        self.scheduler.stop()
        sys.exit(0)

    # =====================================================================
    # ALARM & REMINDER BACKGROUND TRIGGER HANDLERS
    # =====================================================================
    def on_alarm_fired(self, alarm_dict):
        """
        Thread-safe callback slot fired by background QThread. Opens visual overlays.
        """
        popup = AlarmPopup(
            title="Alarm Ringing",
            label=alarm_dict['label'] or "Wake up call",
            is_reminder=False
        )
        self.show_popup(popup)
        
        # Switch to alarms tab automatically to refresh state
        self.switch_tab(4)

    def on_reminder_fired(self, reminder_dict):
        """
        Thread-safe callback slot for reminders.
        """
        popup = AlarmPopup(
            title="Reminder Alert",
            label=reminder_dict['text'],
            is_reminder=True
        )
        self.show_popup(popup)
        
        # Switch to reminders tab to refresh list
        self.switch_tab(3)

    def on_timer_fired(self, timer_dict):
        """
        Thread-safe callback slot for countdown timer completions.
        """
        popup = AlarmPopup(
            title="Timer Completed",
            label=timer_dict['label'] or "Countdown timer finished",
            is_reminder=True
        )
        self.show_popup(popup)
        
        # Switch to stopwatch/timer tab to refresh queue
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
        """
        Minimize to system tray instead of exiting when close button clicked.
        """
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_app()


# Global Singleton Window Reference
_global_window = None

def get_dashboard_window():
    global _global_window
    if _global_window is None:
        _global_window = DashboardWindow()
    return _global_window


def launch_dashboard():
    """
    Standalone runner utility to test or initialize the Productivity UI.
    """
    app = QApplication(sys.argv)
    win = get_dashboard_window()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    launch_dashboard()
