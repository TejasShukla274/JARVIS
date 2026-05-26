# gui/dashboard_tab.py

import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QTimer

from database.db_manager import get_alarms, get_reminders, get_tasks, get_events, add_timer_log
from utils.audio_player import play_notification_beep, speak_alert


class DashboardTab(QWidget):
    """
    Overview Tab for the Productivity System.
    Houses the local Focus Session (Pomodoro), overall system stats, and upcoming schedule lists.
    """
    def __init__(self):
        super().__init__()
        self.pomodoro_state = "idle"  # idle, focus, short_break, long_break
        self.pomodoro_seconds_left = 25 * 60
        self.pomodoro_total_seconds = 25 * 60
        self.completed_sessions = 0
        
        self.setup_ui()
        
        # Connect Pomodoro tick to 1-second system clock timer
        from scheduler.background_scheduler import get_scheduler
        get_scheduler().second_tick.connect(self.pomodoro_tick)
        get_scheduler().second_tick.connect(self.refresh_upcoming_and_stats)

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # =====================================================================
        # LEFT PANEL: POMODORO FOCUS COCKPIT
        # =====================================================================
        focus_panel = QWidget()
        focus_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        focus_layout = QVBoxLayout(focus_panel)
        focus_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("FOCUS COCKPIT (POMODORO)")
        title.setFont(QFont("Consolas", 11, QFont.Bold))
        title.setStyleSheet("color: #00ffaa; letter-spacing: 1px; border: none;")
        focus_layout.addWidget(title)

        # Time readout
        self.lbl_pomo_time = QLabel("25:00")
        self.lbl_pomo_time.setFont(QFont("Consolas", 42, QFont.Bold))
        self.lbl_pomo_time.setStyleSheet("color: white; border: none; background: transparent;")
        self.lbl_pomo_time.setAlignment(Qt.AlignCenter)
        focus_layout.addWidget(self.lbl_pomo_time)

        # State Indicator Label
        self.lbl_pomo_state = QLabel("READY FOR DEPLOYMENT")
        self.lbl_pomo_state.setFont(QFont("Consolas", 10, QFont.Bold))
        self.lbl_pomo_state.setStyleSheet("color: #00aaff; border: none; background: transparent;")
        self.lbl_pomo_state.setAlignment(Qt.AlignCenter)
        focus_layout.addWidget(self.lbl_pomo_state)

        # Progress bar
        self.pomo_progress = QProgressBar()
        self.pomo_progress.setValue(100)
        self.pomo_progress.setTextVisible(False)
        self.pomo_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(0, 170, 255, 30);
                border-radius: 4px;
                background-color: rgba(10, 10, 15, 255);
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #00ffaa;
            }
        """)
        focus_layout.addWidget(self.pomo_progress)

        # Control actions
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_pomo_control = QPushButton("START FOCUS")
        self.btn_pomo_control.setFont(QFont("Consolas", 10, QFont.Bold))
        self.btn_pomo_control.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 170, 20);
                color: #00ffaa;
                border: 1px solid #00ffaa;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 170, 50);
            }
        """)
        self.btn_pomo_control.clicked.connect(self.toggle_pomodoro)
        btn_layout.addWidget(self.btn_pomo_control)

        self.btn_pomo_reset = QPushButton("RESET")
        self.btn_pomo_reset.setFont(QFont("Consolas", 10, QFont.Bold))
        self.btn_pomo_reset.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 50, 50, 20);
                color: #ff3232;
                border: 1px solid #ff3232;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 50);
            }
        """)
        self.btn_pomo_reset.clicked.connect(self.reset_pomodoro)
        btn_layout.addWidget(self.btn_pomo_reset)
        
        focus_layout.addLayout(btn_layout)

        # Focus stats summary
        self.lbl_sessions = QLabel("Completed Focus Runs: 0")
        self.lbl_sessions.setFont(QFont("Consolas", 9))
        self.lbl_sessions.setStyleSheet("color: rgba(255,255,255, 150); border: none;")
        self.lbl_sessions.setAlignment(Qt.AlignCenter)
        focus_layout.addWidget(self.lbl_sessions)

        main_layout.addWidget(focus_panel, stretch=1)

        # =====================================================================
        # RIGHT PANEL: QUICK STATS GRID & UPCOMING AGENDA PANEL
        # =====================================================================
        right_panel = QWidget()
        right_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)

        right_layout.addWidget(QLabel("PRODUCTIVITY ANALYTICS MATRIX:"), alignment=Qt.AlignTop)
        
        # Grid stats card
        stats_frame = QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        stats_grid = QHBoxLayout(stats_frame)
        stats_grid.setContentsMargins(0, 5, 0, 5)
        stats_grid.setSpacing(10)
        
        self.card_tasks = self.create_analytics_pill("TASKS DUE", "0", "#ffaa00")
        self.card_reminders = self.create_analytics_pill("REMINDERS", "0", "#00ffaa")
        self.card_events = self.create_analytics_pill("EVENTS", "0", "#00aaff")

        stats_grid.addWidget(self.card_tasks)
        stats_grid.addWidget(self.card_reminders)
        stats_grid.addWidget(self.card_events)
        right_layout.addWidget(stats_frame)

        # Agenda summary
        right_layout.addWidget(QLabel("UPCOMING PRIORITY ACTIONS:"), alignment=Qt.AlignTop)
        self.lbl_upcoming = QLabel("Loading agenda protocols...")
        self.lbl_upcoming.setFont(QFont("Consolas", 10))
        self.lbl_upcoming.setStyleSheet("color: white; border: none; background: transparent;")
        self.lbl_upcoming.setWordWrap(True)
        self.lbl_upcoming.setAlignment(Qt.AlignTop)
        right_layout.addWidget(self.lbl_upcoming, stretch=1)

        main_layout.addWidget(right_panel, stretch=1)
        self.setLayout(main_layout)
        
        self.refresh_upcoming_and_stats()

    def create_analytics_pill(self, label, count, color):
        pill = QFrame()
        pill.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 15, 200);
                border: 1px solid rgba(0, 170, 255, 20);
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(pill)
        layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_num = QLabel(count)
        lbl_num.setFont(QFont("Consolas", 18, QFont.Bold))
        lbl_num.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        lbl_num.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_num)

        lbl_tag = QLabel(label)
        lbl_tag.setFont(QFont("Consolas", 8))
        lbl_tag.setStyleSheet("color: rgba(255,255,255, 120); border: none; background: transparent;")
        lbl_tag.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_tag)
        
        # Save count indicator widget reference
        pill.setProperty("count_lbl", lbl_num)
        return pill

    def toggle_pomodoro(self):
        if self.pomodoro_state == "idle":
            # Start focus run
            self.pomodoro_state = "focus"
            self.pomodoro_seconds_left = 25 * 60
            self.pomodoro_total_seconds = 25 * 60
            self.lbl_pomo_state.setText("FOCUS SESSION IN PROGRESS")
            self.lbl_pomo_state.setStyleSheet("color: #ff3e3e; border: none;")
            self.btn_pomo_control.setText("PAUSE FOCUS")
            self.btn_pomo_control.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 170, 255, 20);
                    color: #00aaff;
                    border: 1px solid #00aaff;
                    border-radius: 6px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 170, 255, 50);
                }
            """)
            play_notification_beep()
            
        elif self.pomodoro_state in ("focus", "short_break", "long_break"):
            # Pause focus run
            self.pomodoro_state = "paused"
            self.lbl_pomo_state.setText("SESSION SUSPENDED")
            self.lbl_pomo_state.setStyleSheet("color: #ffaa00; border: none;")
            self.btn_pomo_control.setText("RESUME FOCUS")
            self.btn_pomo_control.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 255, 170, 20);
                    color: #00ffaa;
                    border: 1px solid #00ffaa;
                    border-radius: 6px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 255, 170, 50);
                }
            """)
            play_notification_beep()
            
        elif self.pomodoro_state == "paused":
            # Resume focus run
            self.pomodoro_state = "focus"
            self.lbl_pomo_state.setText("FOCUS SESSION IN PROGRESS")
            self.lbl_pomo_state.setStyleSheet("color: #ff3e3e; border: none;")
            self.btn_pomo_control.setText("PAUSE FOCUS")
            self.btn_pomo_control.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 170, 255, 20);
                    color: #00aaff;
                    border: 1px solid #00aaff;
                    border-radius: 6px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 170, 255, 50);
                }
            """)
            play_notification_beep()

    def reset_pomodoro(self):
        self.pomodoro_state = "idle"
        self.pomodoro_seconds_left = 25 * 60
        self.pomodoro_total_seconds = 25 * 60
        self.pomo_progress.setValue(100)
        self.lbl_pomo_time.setText("25:00")
        self.lbl_pomo_state.setText("READY FOR DEPLOYMENT")
        self.lbl_pomo_state.setStyleSheet("color: #00aaff; border: none;")
        self.btn_pomo_control.setText("START FOCUS")
        self.btn_pomo_control.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 170, 20);
                color: #00ffaa;
                border: 1px solid #00ffaa;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 170, 50);
            }
        """)
        play_notification_beep()

    def pomodoro_tick(self):
        """
        Calculates remaining focus session seconds and handles state transitions.
        """
        if self.pomodoro_state in ("idle", "paused"):
            return

        self.pomodoro_seconds_left -= 1
        
        # Display minutes:seconds
        mins = self.pomodoro_seconds_left // 60
        secs = self.pomodoro_seconds_left % 60
        self.lbl_pomo_time.setText(f"{mins:02d}:{secs:02d}")
        
        # Progress percent
        ratio = (self.pomodoro_seconds_left / float(self.pomodoro_total_seconds)) * 100
        self.pomo_progress.setValue(int(ratio))

        if self.pomodoro_seconds_left <= 0:
            self.handle_pomodoro_completion()

    def handle_pomodoro_completion(self):
        play_notification_beep()
        
        if self.pomodoro_state == "focus":
            self.completed_sessions += 1
            self.lbl_sessions.setText(f"Completed Focus Runs: {self.completed_sessions}")
            
            # Log completed timer to database
            add_timer_log(25 * 60, datetime.datetime.now().isoformat(), "Pomodoro Focus")
            
            # Transition to break
            speak_alert("Focus run completed. Take a five minute rest, Sir.")
            self.pomodoro_state = "short_break"
            self.pomodoro_seconds_left = 5 * 60
            self.pomodoro_total_seconds = 5 * 60
            self.lbl_pomo_state.setText("SHORT BREAK PROTOCOL ACTIVE")
            self.lbl_pomo_state.setStyleSheet("color: #00ffaa; border: none;")
        else:
            # Transition from break back to focus
            speak_alert("Rest period completed. Commencing next focus session.")
            self.pomodoro_state = "focus"
            self.pomodoro_seconds_left = 25 * 60
            self.pomodoro_total_seconds = 25 * 60
            self.lbl_pomo_state.setText("FOCUS SESSION IN PROGRESS")
            self.lbl_pomo_state.setStyleSheet("color: #ff3e3e; border: none;")

    def refresh_upcoming_and_stats(self):
        """
        Gathers database totals and compiles upcoming reminder notifications list.
        """
        # Fetch totals
        tasks = get_tasks()
        reminders = get_reminders(include_completed=False)
        events = get_events()
        
        # 1. Update metric count displays
        self.card_tasks.property("count_lbl").setText(str(len([t for t in tasks if t['status'].lower() != 'done'])))
        self.card_reminders.property("count_lbl").setText(str(len(reminders)))
        self.card_events.property("count_lbl").setText(str(len(events)))

        # 2. Compile Upcoming text readout
        text = ""
        now = datetime.datetime.now()
        
        # Next active reminder
        active_rem = [r for r in reminders if datetime.datetime.fromisoformat(r['datetime']) > now]
        if active_rem:
            next_r = active_rem[0]
            dt_rem = datetime.datetime.fromisoformat(next_r['datetime'])
            diff_rem = dt_rem - now
            mins = int(diff_rem.total_seconds() // 60)
            h = mins // 60
            m = mins % 60
            text += f"⏰ **Next Reminder:** {next_r['text']} (in {h}h {m}m)\n\n"
        else:
            text += "⏰ **Next Reminder:** None scheduled\n\n"

        # Overdue Tasks
        overdue_list = []
        for t in tasks:
            if t['status'].lower() != 'done' and t['due_date']:
                due_dt = datetime.datetime.strptime(t['due_date'], "%Y-%m-%d").date()
                if due_dt < now.date():
                    overdue_list.append(t['title'])
                    
        if overdue_list:
            text += f"⚠️ **Overdue Tasks ({len(overdue_list)}):**\n"
            for t_title in overdue_list[:3]:
                text += f" - {t_title}\n"
            text += "\n"
        else:
            text += "⚠️ **Overdue Tasks:** None. Good job!\n\n"

        # Next upcoming event
        upcoming_events = [e for e in events if datetime.datetime.fromisoformat(e['start_time']) > now]
        if upcoming_events:
            next_e = upcoming_events[0]
            dt_ev = datetime.datetime.fromisoformat(next_e['start_time'])
            text += f"📅 **Next Event:** {next_e['title']} on {dt_ev.strftime('%d %b, %I:%M %p')}\n"
        else:
            text += "📅 **Next Event:** None scheduled\n"

        # Format and display
        self.lbl_upcoming.setText(text)
