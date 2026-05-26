# gui/alarms_tab.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Alarm Configuration — Create, toggle, and monitor alarms.
# ─────────────────────────────────────────────────────────────────────────────

import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QCheckBox, QTimeEdit, QLineEdit, QGridLayout,
    QSlider, QFileDialog, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTime

from database.db_manager import add_alarm, get_alarms, delete_alarm, update_alarm
from utils.audio_player import play_notification_beep
from gui import styles


class AlarmsTab(QWidget):
    """
    Futuristic alarm panel with live countdowns, volume control,
    repeat-day selection, and custom WAV sound support.
    """

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_alarms_list()

        from scheduler.background_scheduler import get_scheduler
        get_scheduler().second_tick.connect(self.update_countdowns)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ═══════════════════════════════════════════════════════════════
        # LEFT: ACTIVE ALARMS LIST
        # ═══════════════════════════════════════════════════════════════
        left_panel = QFrame()
        left_panel.setStyleSheet(styles.GLASS_PANEL)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)

        title = QLabel("ACTIVE ALARM SYSTEMS")
        title.setFont(QFont("Consolas", 12, QFont.Bold))
        title.setStyleSheet(
            f"color: {styles.RED}; letter-spacing: 2px; border: none; "
            "background: transparent;"
        )
        left_layout.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(styles.SCROLL_STYLE)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.addStretch()

        self.scroll.setWidget(self.scroll_content)
        left_layout.addWidget(self.scroll)
        main_layout.addWidget(left_panel, stretch=3)

        # ═══════════════════════════════════════════════════════════════
        # RIGHT: ADD NEW ALARM
        # ═══════════════════════════════════════════════════════════════
        right_panel = QFrame()
        right_panel.setStyleSheet(styles.GLASS_PANEL)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 16, 18, 16)
        right_layout.setSpacing(12)

        add_title = QLabel("PROVISION NEW ALARM")
        add_title.setFont(QFont("Consolas", 11, QFont.Bold))
        add_title.setStyleSheet(styles.HEADER_LABEL)
        right_layout.addWidget(add_title)

        # Time
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setFont(QFont("Consolas", 18, QFont.Bold))
        self.time_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.time_edit)

        # Label
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Alarm Label (e.g. Workout)")
        self.label_edit.setFont(QFont("Consolas", 10))
        self.label_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.label_edit)

        # Sound
        self.sound_path_edit = QLineEdit()
        self.sound_path_edit.setPlaceholderText("Optional local WAV alarm sound")
        self.sound_path_edit.setReadOnly(True)
        self.sound_path_edit.setFont(QFont("Consolas", 9))
        self.sound_path_edit.setStyleSheet(styles.INPUT_STYLE)

        sound_row = QHBoxLayout()
        sound_row.addWidget(self.sound_path_edit, stretch=1)
        btn_sound = QPushButton("Browse")
        btn_sound.setStyleSheet(styles.button_style(styles.CYAN, 6))
        btn_sound.clicked.connect(self.choose_alarm_sound)
        sound_row.addWidget(btn_sound)
        right_layout.addLayout(sound_row)

        # Volume
        lbl_vol = QLabel("VOLUME:")
        lbl_vol.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_vol.setStyleSheet(styles.DIM_LABEL)
        right_layout.addWidget(lbl_vol)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(10, 100)
        self.volume_slider.setValue(85)
        self.volume_slider.setStyleSheet(styles.SLIDER_STYLE)
        right_layout.addWidget(self.volume_slider)

        # Weekdays
        lbl_days = QLabel("RECURRENCE SCHEDULE:")
        lbl_days.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_days.setStyleSheet(styles.DIM_LABEL)
        right_layout.addWidget(lbl_days)

        grid = QGridLayout()
        grid.setSpacing(6)
        self.day_checkboxes = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for idx, day in enumerate(day_names):
            cb = QCheckBox(day)
            cb.setFont(QFont("Consolas", 9))
            cb.setStyleSheet(styles.CHECKBOX_STYLE)
            grid.addWidget(cb, idx // 4, idx % 4)
            self.day_checkboxes.append(cb)
        right_layout.addLayout(grid)

        # Save
        btn_save = QPushButton("DEPLOY ALARM")
        btn_save.setFont(QFont("Consolas", 10, QFont.Bold))
        btn_save.setStyleSheet(styles.button_style(styles.RED))
        btn_save.clicked.connect(self.save_new_alarm)
        right_layout.addWidget(btn_save)
        right_layout.addStretch()

        main_layout.addWidget(right_panel, stretch=2)

    # ── Sound picker ─────────────────────────────────────────────────────

    def choose_alarm_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select local alarm sound", "",
            "Wave files (*.wav);;All files (*.*)"
        )
        if path:
            self.sound_path_edit.setText(path)

    # ── List rendering ───────────────────────────────────────────────────

    def refresh_alarms_list(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        alarms = get_alarms()
        if not alarms:
            empty = QLabel("No alarms configured.")
            empty.setFont(QFont("Consolas", 11))
            empty.setStyleSheet(styles.DIM_LABEL)
            self.scroll_layout.insertWidget(0, empty)
            return

        for idx, alarm in enumerate(alarms):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(4, 10, 18, 210);
                    border: 1px solid {styles.CYAN_FAINT};
                    border-radius: 8px;
                }}
            """)
            row = QHBoxLayout(card)
            row.setContentsMargins(14, 10, 14, 10)

            # Active toggle
            cb = QCheckBox()
            cb.setChecked(bool(alarm["is_active"]))
            cb.setStyleSheet(styles.CHECKBOX_STYLE)
            cb.stateChanged.connect(
                lambda state, aid=alarm["id"]:
                    self.toggle_alarm_state(aid, state)
            )
            row.addWidget(cb)

            # Details
            details = QVBoxLayout()
            details.setSpacing(2)

            lbl_time = QLabel(alarm["time"])
            lbl_time.setFont(QFont("Consolas", 22, QFont.Bold))
            lbl_time.setStyleSheet(styles.BODY_LABEL)
            details.addWidget(lbl_time)

            lbl_label = QLabel(alarm["label"] or "Alarm")
            lbl_label.setFont(QFont("Consolas", 10))
            lbl_label.setStyleSheet(styles.HEADER_LABEL)
            details.addWidget(lbl_label)

            if alarm.get("custom_sound"):
                lbl_snd = QLabel("♪ Custom sound")
                lbl_snd.setFont(QFont("Consolas", 8))
                lbl_snd.setStyleSheet(
                    f"color: {styles.GREEN}; border: none; "
                    "background: transparent;"
                )
                details.addWidget(lbl_snd)

            days_idx = json.loads(alarm["repeat_days"])
            names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            days_txt = (
                ", ".join(names[d] for d in days_idx) if days_idx else "Once"
            )
            lbl_days = QLabel(f"Days: {days_txt}")
            lbl_days.setFont(QFont("Consolas", 8))
            lbl_days.setStyleSheet(styles.DIM_LABEL)
            details.addWidget(lbl_days)
            row.addLayout(details, stretch=1)

            # Countdown
            countdown = QLabel()
            countdown.setFont(QFont("Consolas", 10, QFont.Bold))
            countdown.setStyleSheet(
                f"color: {styles.RED}; border: none; background: transparent;"
            )
            countdown.setProperty("alarm_time", alarm["time"])
            countdown.setProperty("alarm_days", alarm["repeat_days"])
            countdown.setProperty("alarm_active", alarm["is_active"])
            card.setProperty("alarm_time", alarm["time"])
            card.setProperty("alarm_days", alarm["repeat_days"])
            card.setProperty("alarm_active", alarm["is_active"])
            row.addWidget(countdown, alignment=Qt.AlignVCenter)

            # Delete
            btn_del = QPushButton("✕")
            btn_del.setFixedSize(30, 30)
            btn_del.setStyleSheet(styles.button_style(styles.RED, 6))
            btn_del.clicked.connect(
                lambda checked, aid=alarm["id"]:
                    self.delete_alarm_action(aid)
            )
            row.addWidget(btn_del)

            self.scroll_layout.insertWidget(idx, card)

        self.update_countdowns()

    # ── Actions ──────────────────────────────────────────────────────────

    def toggle_alarm_state(self, alarm_id, state):
        update_alarm(alarm_id, is_active=1 if state == Qt.Checked else 0)
        play_notification_beep()
        self.update_countdowns()

    def delete_alarm_action(self, alarm_id):
        delete_alarm(alarm_id)
        play_notification_beep()
        self.refresh_alarms_list()

    def save_new_alarm(self):
        time_str = self.time_edit.time().toString("HH:mm")
        label = self.label_edit.text().strip() or "Alarm"

        repeat_days = [
            idx for idx, cb in enumerate(self.day_checkboxes)
            if cb.isChecked()
        ]

        add_alarm(
            time=time_str,
            label=label,
            repeat_days=json.dumps(repeat_days),
            is_active=1,
            custom_sound=self.sound_path_edit.text().strip() or None,
            volume=self.volume_slider.value(),
        )

        self.label_edit.clear()
        self.sound_path_edit.clear()
        for cb in self.day_checkboxes:
            cb.setChecked(False)

        play_notification_beep()
        self.refresh_alarms_list()

    # ── Live countdown ───────────────────────────────────────────────────

    def update_countdowns(self):
        now = datetime.now()
        current_wday = now.weekday()

        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if not widget:
                continue

            labels = widget.findChildren(QLabel)
            if len(labels) < 3:
                continue
            countdown_lbl = labels[-1]

            time_str = widget.property("alarm_time")
            days_json = widget.property("alarm_days")
            is_active = widget.property("alarm_active")

            if not time_str or not is_active:
                countdown_lbl.setText("Inactive")
                countdown_lbl.setStyleSheet(styles.DIM_LABEL)
                continue

            alarm_h, alarm_m = map(int, time_str.split(":"))
            repeat_days = json.loads(days_json)

            next_trigger = None
            if not repeat_days:
                candidate = now.replace(
                    hour=alarm_h, minute=alarm_m, second=0, microsecond=0
                )
                if candidate <= now:
                    candidate += timedelta(days=1)
                next_trigger = candidate
            else:
                min_diff = timedelta(days=9)
                for day_idx in repeat_days:
                    days_diff = day_idx - current_wday
                    if days_diff < 0:
                        days_diff += 7
                    elif days_diff == 0:
                        test_time = datetime.min.time().replace(
                            hour=alarm_h, minute=alarm_m
                        )
                        if now.time() >= test_time:
                            days_diff += 7
                    candidate = now.replace(
                        hour=alarm_h, minute=alarm_m, second=0, microsecond=0
                    ) + timedelta(days=days_diff)
                    diff = candidate - now
                    if diff < min_diff:
                        min_diff = diff
                        next_trigger = candidate

            if next_trigger:
                tot_sec = int((next_trigger - now).total_seconds())
                hours = tot_sec // 3600
                minutes = (tot_sec % 3600) // 60
                text = f"In {hours}h {minutes}m" if hours > 0 else f"In {minutes}m"
                countdown_lbl.setText(text)
                countdown_lbl.setStyleSheet(
                    f"color: {styles.RED}; border: none; "
                    "background: transparent;"
                )
