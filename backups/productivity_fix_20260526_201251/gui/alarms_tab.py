# gui/alarms_tab.py

import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QCheckBox, QTimeEdit, QLineEdit, QGridLayout
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QTime

from database.db_manager import add_alarm, get_alarms, delete_alarm, update_alarm
from utils.audio_player import play_notification_beep


class AlarmsTab(QWidget):
    """
    Futuristic panel for adding, toggling, and displaying active alarms,
    including live countdown calculations.
    """
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_alarms_list()
        
        # Connect to system tick timer via global scheduler
        from scheduler.background_scheduler import get_scheduler
        get_scheduler().second_tick.connect(self.update_countdowns)

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # =====================================================================
        # LEFT SIDE: ALARMS LIST
        # =====================================================================
        list_container = QWidget()
        list_container.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("CURRENT ACTIVE ALARMS")
        title.setFont(QFont("Consolas", 11, QFont.Bold))
        title.setStyleSheet("color: #ff3e3e; letter-spacing: 1px; border: none;")
        list_layout.addWidget(title)

        # Scroll Area for active items
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(12)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.addStretch()

        self.scroll.setWidget(self.scroll_content)
        list_layout.addWidget(self.scroll)
        main_layout.addWidget(list_container, stretch=3)

        # =====================================================================
        # RIGHT SIDE: ADD NEW ALARM
        # =====================================================================
        add_container = QWidget()
        add_container.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        add_layout = QVBoxLayout(add_container)
        add_layout.setContentsMargins(20, 20, 20, 20)

        add_title = QLabel("PROVISION NEW ALARM")
        add_title.setFont(QFont("Consolas", 11, QFont.Bold))
        add_title.setStyleSheet("color: #00e5ff; letter-spacing: 1px; border: none;")
        add_layout.addWidget(add_title)

        # Alarm Time selector
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setFont(QFont("Consolas", 16, QFont.Bold))
        self.time_edit.setStyleSheet("""
            QTimeEdit {
                color: white;
                background-color: #0c0c14;
                border: 1px solid rgba(0, 170, 255, 60);
                border-radius: 6px;
                padding: 10px;
            }
        """)
        add_layout.addWidget(self.time_edit)

        # Alarm Note / Label input
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Alarm Label (e.g. Work, Workout)")
        self.label_edit.setFont(QFont("Consolas", 10))
        self.label_edit.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: #0c0c14;
                border: 1px solid rgba(0, 170, 255, 60);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        add_layout.addWidget(self.label_edit)

        # Weekdays selection
        add_layout.addWidget(QLabel("RECURRENCE SCHEDULE:"))
        grid = QGridLayout()
        grid.setSpacing(6)
        
        self.day_checkboxes = []
        days_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for idx, day in enumerate(days_names):
            cb = QCheckBox(day)
            cb.setFont(QFont("Consolas", 9))
            cb.setStyleSheet("""
                QCheckBox {
                    color: white;
                    border: none;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            grid.addWidget(cb, idx // 4, idx % 4)
            self.day_checkboxes.append(cb)
        add_layout.addLayout(grid)

        # Save Alarm button
        btn_save = QPushButton("SAVE ALARM MODULE")
        btn_save.setFont(QFont("Consolas", 10, QFont.Bold))
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 62, 62, 20);
                color: #ff3e3e;
                border: 1px solid #ff3e3e;
                border-radius: 6px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 62, 62, 50);
            }
        """)
        btn_save.clicked.connect(self.save_new_alarm)
        add_layout.addWidget(btn_save)
        add_layout.addStretch()

        main_layout.addWidget(add_container, stretch=2)
        self.setLayout(main_layout)

    def refresh_alarms_list(self):
        """
        Loads alarms from SQLite database and displays cards inside scroll container.
        """
        # Clear layout children except final stretch spacer
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        alarms = get_alarms()
        if not alarms:
            no_alarms = QLabel("No active alarms configured.")
            no_alarms.setFont(QFont("Consolas", 11))
            no_alarms.setStyleSheet("color: rgba(255, 255, 255, 100); border: none;")
            self.scroll_layout.insertWidget(0, no_alarms)
            return

        # Add active alarm cards
        for idx, alarm in enumerate(alarms):
            card = QWidget()
            card.setStyleSheet("""
                QWidget {
                    background-color: rgba(10, 10, 15, 200);
                    border: 1px solid rgba(0, 170, 255, 30);
                    border-radius: 8px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(15, 10, 15, 10)

            # Checkbox state toggle
            cb_active = QCheckBox()
            cb_active.setChecked(bool(alarm['is_active']))
            cb_active.setStyleSheet("border: none; background: transparent;")
            # Capture variable inside lambda
            cb_active.stateChanged.connect(
                lambda state, aid=alarm['id']: self.toggle_alarm_state(aid, state)
            )
            card_layout.addWidget(cb_active)

            # Details
            details = QVBoxLayout()
            lbl_time = QLabel(alarm['time'])
            lbl_time.setFont(QFont("Consolas", 22, QFont.Bold))
            lbl_time.setStyleSheet("color: white; border: none; background: transparent;")
            details.addWidget(lbl_time)

            lbl_label = QLabel(alarm['label'] or "Alarm")
            lbl_label.setFont(QFont("Consolas", 10))
            lbl_label.setStyleSheet("color: #00e5ff; border: none; background: transparent;")
            details.addWidget(lbl_label)

            # Parse days representation
            days_idx = json.loads(alarm['repeat_days'])
            if not days_idx:
                days_txt = "Once"
            else:
                names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                days_txt = ", ".join(names[d] for d in days_idx)

            lbl_days = QLabel(f"Days: {days_txt}")
            lbl_days.setFont(QFont("Consolas", 8))
            lbl_days.setStyleSheet("color: rgba(255, 255, 255, 120); border: none; background: transparent;")
            details.addWidget(lbl_days)
            card_layout.addLayout(details)

            # Live Countdown widget
            countdown = QLabel()
            countdown.setFont(QFont("Consolas", 10, QFont.Bold))
            countdown.setStyleSheet("color: #ff3e3e; border: none; background: transparent;")
            # Save metadata reference for dynamic second updates
            countdown.setProperty("alarm_time", alarm['time'])
            countdown.setProperty("alarm_days", alarm['repeat_days'])
            countdown.setProperty("alarm_active", alarm['is_active'])
            card.setProperty("alarm_time", alarm['time'])
            card.setProperty("alarm_days", alarm['repeat_days'])
            card.setProperty("alarm_active", alarm['is_active'])
            card_layout.addWidget(countdown, stretch=1, alignment=Qt.AlignVCenter)

            # Delete Button
            btn_del = QPushButton("✕")
            btn_del.setFont(QFont("Consolas", 10, QFont.Bold))
            btn_del.setFixedSize(30, 30)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 50, 50, 20);
                    color: #ff5252;
                    border: 1px solid #ff5252;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 50, 50, 60);
                }
            """)
            btn_del.clicked.connect(
                lambda checked, aid=alarm['id']: self.delete_alarm_action(aid)
            )
            card_layout.addWidget(btn_del)

            # Insert card in layout
            self.scroll_layout.insertWidget(idx, card)

        self.update_countdowns()

    def toggle_alarm_state(self, alarm_id, state):
        is_active = 1 if state == Qt.Checked else 0
        update_alarm(alarm_id, is_active=is_active)
        play_notification_beep()
        self.update_countdowns()

    def delete_alarm_action(self, alarm_id):
        delete_alarm(alarm_id)
        self.refresh_alarms_list()
        play_notification_beep()

    def save_new_alarm(self):
        time_str = self.time_edit.time().toString("HH:mm")
        label = self.label_edit.text().strip() or "Alarm"
        
        # Collect weekdays
        repeat_days = []
        for idx, cb in enumerate(self.day_checkboxes):
            if cb.isChecked():
                repeat_days.append(idx)

        add_alarm(
            time=time_str,
            label=label,
            repeat_days=json.dumps(repeat_days),
            is_active=1
        )
        
        # Reset UI controls
        self.label_edit.clear()
        for cb in self.day_checkboxes:
            cb.setChecked(False)
            
        play_notification_beep()
        self.refresh_alarms_list()

    def update_countdowns(self):
        """
        Iterates over all visually listed alarm cards and recalculates remaining
        durations to display live count-down outputs.
        """
        now = datetime.now()
        current_wday = now.weekday()
        current_time = now.time()

        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if not widget:
                continue

            countdown_lbl = widget.findChild(QLabel)
            # Find the specific countdown label by locating widget in columns
            labels = widget.findChildren(QLabel)
            if len(labels) < 3:
                continue
                
            # Get the exact countdown text widget
            countdown_lbl = labels[-1] 
            
            # Check properties
            time_str = widget.property("alarm_time")
            days_json = widget.property("alarm_days")
            is_active = widget.property("alarm_active")

            if not time_str or not is_active:
                countdown_lbl.setText("Inactive")
                countdown_lbl.setStyleSheet("color: rgba(255, 255, 255, 100); border: none;")
                continue

            # Calculate next trigger date
            alarm_h, alarm_m = map(int, time_str.split(":"))
            repeat_days = json.loads(days_json)
            
            next_trigger = None
            if not repeat_days:
                # One-time alarm
                candidate = now.replace(hour=alarm_h, minute=alarm_m, second=0, microsecond=0)
                if candidate <= now:
                    candidate += timedelta(days=1)
                next_trigger = candidate
            else:
                # Find matching weekday in future
                min_diff = timedelta(days=9)
                for day_idx in repeat_days:
                    days_diff = day_idx - current_wday
                    if days_diff < 0:
                        days_diff += 7
                    elif days_diff == 0:
                        # Today. Check if time has already passed
                        if now.time() >= datetime.min.time().replace(hour=alarm_h, minute=alarm_m):
                            days_diff += 7  # Push to next week's matching day
                    
                    candidate = now.replace(hour=alarm_h, minute=alarm_m, second=0, microsecond=0) + timedelta(days=days_diff)
                    diff = candidate - now
                    if diff < min_diff:
                        min_diff = diff
                        next_trigger = candidate

            if next_trigger:
                diff = next_trigger - now
                tot_sec = int(diff.total_seconds())
                hours = tot_sec // 3600
                minutes = (tot_sec % 3600) // 60
                
                if hours > 0:
                    countdown_lbl.setText(f"In {hours}h {minutes}m")
                else:
                    countdown_lbl.setText(f"In {minutes}m")
                countdown_lbl.setStyleSheet("color: #ff3e3e; border: none;")
