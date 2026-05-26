# gui/reminders_tab.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Reminders — NLP quick-add, manual form, live countdown.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QDateTimeEdit, QComboBox, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDateTime

from database.db_manager import (
    add_reminder, get_reminders, delete_reminder, update_reminder
)
from utils.nlp_parser import parse_reminder_nlp
from utils.audio_player import play_notification_beep
from gui import styles


class RemindersTab(QWidget):
    """
    Futuristic reminders panel with offline NLP parsing bar,
    manual registration, live auto-refresh, and countdown display.
    """

    def __init__(self):
        super().__init__()
        self._refresh_tick = 0
        self.setup_ui()
        self.refresh_reminders_list()

        # Connect to scheduler for auto-refresh
        from scheduler.background_scheduler import get_scheduler
        get_scheduler().second_tick.connect(self._on_tick)

    def _on_tick(self):
        """Auto-refresh every 10 seconds via scheduler tick."""
        self._refresh_tick += 1
        if self._refresh_tick % 10 == 0:
            self.refresh_reminders_list()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ═══════════════════════════════════════════════════════════════
        # LEFT SIDE: REMINDERS VIEWER + NLP BAR
        # ═══════════════════════════════════════════════════════════════
        left_panel = QFrame()
        left_panel.setStyleSheet(styles.GLASS_PANEL)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)

        title = QLabel("REMINDERS PROTOCOLS")
        title.setFont(QFont("Consolas", 12, QFont.Bold))
        title.setStyleSheet(styles.SECTION_LABEL)
        left_layout.addWidget(title)

        # NLP quick-add bar
        nlp_frame = QFrame()
        nlp_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(4, 10, 18, 200);
                border: 1px solid {styles.GREEN_DIM};
                border-radius: 8px;
            }}
        """)
        nlp_layout = QHBoxLayout(nlp_frame)
        nlp_layout.setContentsMargins(10, 6, 10, 6)

        self.nlp_edit = QLineEdit()
        self.nlp_edit.setPlaceholderText(
            "NLP Entry (e.g. Remind me to call the bank tomorrow at 5 PM)"
        )
        self.nlp_edit.setFont(QFont("Consolas", 10))
        self.nlp_edit.setStyleSheet(
            "color: white; border: none; background: transparent;"
        )
        self.nlp_edit.returnPressed.connect(self.parse_and_save_nlp)
        nlp_layout.addWidget(self.nlp_edit, stretch=1)

        btn_parse = QPushButton("PARSE")
        btn_parse.setFont(QFont("Consolas", 9, QFont.Bold))
        btn_parse.setStyleSheet(styles.button_style(styles.GREEN, 6))
        btn_parse.clicked.connect(self.parse_and_save_nlp)
        nlp_layout.addWidget(btn_parse)

        left_layout.addWidget(nlp_frame)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(styles.SCROLL_STYLE)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.addStretch()

        self.scroll.setWidget(self.scroll_content)
        left_layout.addWidget(self.scroll)

        main_layout.addWidget(left_panel, stretch=3)

        # ═══════════════════════════════════════════════════════════════
        # RIGHT SIDE: MANUAL ADD FORM
        # ═══════════════════════════════════════════════════════════════
        right_panel = QFrame()
        right_panel.setStyleSheet(styles.GLASS_PANEL)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 16, 18, 16)
        right_layout.setSpacing(12)

        right_title = QLabel("MANUAL REGISTRATION")
        right_title.setFont(QFont("Consolas", 11, QFont.Bold))
        right_title.setStyleSheet(styles.HEADER_LABEL)
        right_layout.addWidget(right_title)

        # Text input
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Reminder message...")
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.text_edit)

        # Datetime
        self.dt_edit = QDateTimeEdit()
        self.dt_edit.setDateTime(QDateTime.currentDateTime())
        self.dt_edit.setCalendarPopup(True)
        self.dt_edit.setFont(QFont("Consolas", 10))
        self.dt_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.dt_edit)

        # Priority
        lbl_pri = QLabel("PRIORITY LEVEL:")
        lbl_pri.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_pri.setStyleSheet(styles.DIM_LABEL)
        right_layout.addWidget(lbl_pri)

        self.combo_priority = QComboBox()
        self.combo_priority.addItems(["Low", "Medium", "High"])
        self.combo_priority.setCurrentText("Medium")
        self.combo_priority.setFont(QFont("Consolas", 10))
        self.combo_priority.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.combo_priority)

        # Recurrence
        lbl_rec = QLabel("RECURRENCE FREQUENCY:")
        lbl_rec.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_rec.setStyleSheet(styles.DIM_LABEL)
        right_layout.addWidget(lbl_rec)

        self.combo_recurrence = QComboBox()
        self.combo_recurrence.addItems(["None", "Daily", "Weekly", "Monthly"])
        self.combo_recurrence.setFont(QFont("Consolas", 10))
        self.combo_recurrence.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.combo_recurrence)

        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Category (e.g. Work, Personal)")
        self.category_edit.setFont(QFont("Consolas", 10))
        self.category_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.category_edit)

        # Deploy button
        btn_deploy = QPushButton("DEPLOY REMINDER")
        btn_deploy.setFont(QFont("Consolas", 10, QFont.Bold))
        btn_deploy.setStyleSheet(styles.button_style(styles.CYAN))
        btn_deploy.clicked.connect(self.save_manual_reminder)
        right_layout.addWidget(btn_deploy)
        right_layout.addStretch()

        main_layout.addWidget(right_panel, stretch=2)

    # ── List rendering ───────────────────────────────────────────────────

    def refresh_reminders_list(self):
        """Loads reminders from DB and renders cards with live countdown."""
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        reminders = get_reminders(include_completed=True)
        now = datetime.now()

        if not reminders:
            empty = QLabel("No reminders registered.")
            empty.setFont(QFont("Consolas", 11))
            empty.setStyleSheet(styles.DIM_LABEL)
            self.scroll_layout.insertWidget(0, empty)
            return

        for idx, rem in enumerate(reminders):
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

            # Status toggle
            is_done = rem["is_completed"]
            btn_toggle = QPushButton("✓" if is_done else "○")
            btn_toggle.setFont(QFont("Consolas", 14))
            btn_toggle.setFixedSize(34, 34)
            toggle_color = styles.GREEN if is_done else styles.CYAN_DIM
            btn_toggle.setStyleSheet(
                f"color: {toggle_color}; background: transparent; "
                f"border: 1px solid {toggle_color}; border-radius: 6px;"
            )
            btn_toggle.clicked.connect(
                lambda checked, rid=rem["id"], done=is_done:
                    self.toggle_reminder_state(rid, done)
            )
            row.addWidget(btn_toggle)

            # Details column
            details = QVBoxLayout()
            details.setSpacing(2)

            lbl_text = QLabel(rem["text"])
            lbl_text.setFont(QFont("Consolas", 11, QFont.Bold))
            text_style = styles.BODY_LABEL
            if is_done:
                text_style = (
                    f"color: {styles.WHITE_FAINT}; "
                    "text-decoration: line-through; border: none; "
                    "background: transparent;"
                )
            lbl_text.setStyleSheet(text_style)
            lbl_text.setWordWrap(True)
            details.addWidget(lbl_text)

            # Datetime + countdown
            dt_obj = datetime.fromisoformat(rem["datetime"])
            dt_str = dt_obj.strftime("%d %B %Y, %I:%M %p")

            countdown = ""
            if not is_done and dt_obj > now:
                diff = dt_obj - now
                hours_left = int(diff.total_seconds() // 3600)
                mins_left = int((diff.total_seconds() % 3600) // 60)
                if hours_left > 0:
                    countdown = f" (in {hours_left}h {mins_left}m)"
                else:
                    countdown = f" (in {mins_left}m)"

            lbl_dt = QLabel(f"📅 {dt_str}{countdown}")
            lbl_dt.setFont(QFont("Consolas", 9))
            lbl_dt.setStyleSheet(styles.HEADER_LABEL)
            details.addWidget(lbl_dt)

            meta = (
                f"Category: {rem['category']} | "
                f"Priority: {rem['priority']} | "
                f"Recur: {rem['recurrence']}"
            )
            lbl_meta = QLabel(meta)
            lbl_meta.setFont(QFont("Consolas", 8))
            lbl_meta.setStyleSheet(styles.DIM_LABEL)
            details.addWidget(lbl_meta)
            row.addLayout(details, stretch=1)

            # Priority pill
            priority_pill = QLabel(rem["priority"].upper())
            priority_pill.setFont(QFont("Consolas", 8, QFont.Bold))
            color_map = {
                "high": styles.RED,
                "medium": styles.AMBER,
                "low": styles.GREEN
            }
            p_color = color_map.get(rem["priority"].lower(), styles.WHITE)
            priority_pill.setStyleSheet(f"""
                QLabel {{
                    color: {p_color}; border: 1px solid {p_color};
                    border-radius: 4px; padding: 4px 8px;
                    background: transparent;
                }}
            """)
            row.addWidget(priority_pill, alignment=Qt.AlignVCenter)

            # Delete
            btn_del = QPushButton("✕")
            btn_del.setFont(QFont("Consolas", 12, QFont.Bold))
            btn_del.setFixedSize(30, 30)
            btn_del.setStyleSheet(styles.button_style(styles.RED, 6))
            btn_del.clicked.connect(
                lambda checked, rid=rem["id"]:
                    self.delete_reminder_action(rid)
            )
            row.addWidget(btn_del)

            self.scroll_layout.insertWidget(idx, card)

    # ── Actions ──────────────────────────────────────────────────────────

    def toggle_reminder_state(self, reminder_id, current_completed):
        update_reminder(reminder_id, is_completed=0 if current_completed else 1)
        play_notification_beep()
        self.refresh_reminders_list()

    def delete_reminder_action(self, reminder_id):
        delete_reminder(reminder_id)
        play_notification_beep()
        self.refresh_reminders_list()

    def save_manual_reminder(self):
        text = self.text_edit.text().strip()
        if not text:
            return

        dt_str = self.dt_edit.dateTime().toPyDateTime().isoformat()
        add_reminder(
            text=text,
            datetime_str=dt_str,
            category=self.category_edit.text().strip() or "General",
            priority=self.combo_priority.currentText(),
            recurrence=self.combo_recurrence.currentText(),
        )

        self.text_edit.clear()
        self.category_edit.clear()
        self.dt_edit.setDateTime(QDateTime.currentDateTime())
        play_notification_beep()
        self.refresh_reminders_list()

    def parse_and_save_nlp(self):
        nlp_text = self.nlp_edit.text().strip()
        if not nlp_text:
            return
        try:
            label, parsed_dt = parse_reminder_nlp(nlp_text)
            add_reminder(
                text=label,
                datetime_str=parsed_dt.isoformat(),
                category="General",
                priority="Medium",
                recurrence="None",
            )
            self.nlp_edit.clear()
            play_notification_beep()
            self.refresh_reminders_list()
        except Exception as e:
            print("NLP PARSE ERROR:", e)
