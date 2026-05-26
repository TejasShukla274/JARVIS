# gui/calendar_tab.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Calendar — Interactive offline monthly/weekly/day grid with
# event, reminder, and task indicators.
# ─────────────────────────────────────────────────────────────────────────────

import calendar
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QLineEdit, QDateTimeEdit, QComboBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDateTime

from database.db_manager import (
    add_event, get_events, get_reminders, get_tasks,
    delete_event, update_event
)
from utils.audio_player import play_notification_beep
from gui import styles


class DayCell(QFrame):
    """Calendar day cell with glassmorphism, indicator dots, and click handler."""

    def __init__(self, day_num, full_date, is_today=False,
                 is_selected=False, callback=None):
        super().__init__()
        self.day_num = day_num
        self.full_date = full_date
        self.is_today = is_today
        self.is_selected = is_selected
        self.callback = callback
        self.indicators = {"events": False, "reminders": False, "tasks": False}
        self._build()

    def _build(self):
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(45, 45)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.lbl_num = QLabel(str(self.day_num) if self.day_num > 0 else "")
        self.lbl_num.setFont(QFont("Consolas", 10, QFont.Bold))
        self.lbl_num.setStyleSheet(styles.BODY_LABEL)
        layout.addWidget(self.lbl_num, alignment=Qt.AlignTop | Qt.AlignLeft)

        dot_row = QHBoxLayout()
        dot_row.setSpacing(2)
        dot_row.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(dot_row)

        self.dots = {}
        for key, color in (
            ("events", styles.CYAN),
            ("reminders", styles.GREEN),
            ("tasks", styles.AMBER),
        ):
            dot = QFrame()
            dot.setFixedSize(5, 5)
            dot.setStyleSheet(
                f"background-color: {color}; border-radius: 2px; border: none;"
            )
            dot.setVisible(False)
            dot_row.addWidget(dot)
            self.dots[key] = dot

    def _apply_style(self):
        bg = "rgba(4, 10, 18, 200)"
        border = styles.CYAN_FAINT
        if self.is_today:
            bg = "rgba(0, 229, 255, 35)"
            border = styles.CYAN
        elif self.is_selected:
            bg = "rgba(0, 255, 170, 25)"
            border = styles.GREEN
        self.setStyleSheet(f"""
            DayCell {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
        """)

    def set_selected(self, selected):
        self.is_selected = selected
        self._apply_style()

    def set_has_indicator(self, key, active):
        if key in self.dots:
            self.dots[key].setVisible(active)

    def mousePressEvent(self, event):
        if self.callback and self.day_num > 0:
            self.callback(self.full_date, self)
        super().mousePressEvent(event)


class CalendarTab(QWidget):
    """
    Fully interactive offline calendar with month/week/day views,
    event CRUD, and cross-module indicator dots.
    """

    def __init__(self):
        super().__init__()
        self.selected_date = date.today()
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.cell_widgets = []
        self.view_mode = "Month"
        self.editing_event_id = None
        self.setup_ui()
        self.render_calendar()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ═══════════════════════════════════════════════════════════════
        # LEFT: CALENDAR GRID
        # ═══════════════════════════════════════════════════════════════
        cal_panel = QFrame()
        cal_panel.setStyleSheet(styles.GLASS_PANEL)
        cal_layout = QVBoxLayout(cal_panel)
        cal_layout.setContentsMargins(16, 14, 16, 14)

        # Nav row
        nav = QHBoxLayout()

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setStyleSheet(styles.button_style(styles.CYAN, 6))
        self.btn_prev.clicked.connect(self.prev_month)
        nav.addWidget(self.btn_prev)

        self.lbl_month_yr = QLabel("Month Year")
        self.lbl_month_yr.setFont(QFont("Consolas", 13, QFont.Bold))
        self.lbl_month_yr.setStyleSheet(styles.BODY_LABEL)
        self.lbl_month_yr.setAlignment(Qt.AlignCenter)
        nav.addWidget(self.lbl_month_yr, stretch=1)

        self.view_selector = QComboBox()
        self.view_selector.addItems(["Month", "Week", "Day"])
        self.view_selector.setFont(QFont("Consolas", 9, QFont.Bold))
        self.view_selector.setStyleSheet(styles.INPUT_STYLE)
        self.view_selector.currentTextChanged.connect(self.change_view_mode)
        nav.addWidget(self.view_selector)

        self.btn_next = QPushButton("▶")
        self.btn_next.setStyleSheet(styles.button_style(styles.CYAN, 6))
        self.btn_next.clicked.connect(self.next_month)
        nav.addWidget(self.btn_next)
        cal_layout.addLayout(nav)

        # Weekday headers
        week_hdr = QGridLayout()
        week_hdr.setSpacing(6)
        for idx, day in enumerate(
            ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        ):
            lbl = QLabel(day)
            lbl.setFont(QFont("Consolas", 8, QFont.Bold))
            lbl.setStyleSheet(styles.HEADER_LABEL)
            lbl.setAlignment(Qt.AlignCenter)
            week_hdr.addWidget(lbl, 0, idx)
        cal_layout.addLayout(week_hdr)

        # Day cells grid
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent; border: none;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.addWidget(self.grid_widget)

        main_layout.addWidget(cal_panel, stretch=3)

        # ═══════════════════════════════════════════════════════════════
        # RIGHT: AGENDA + CREATE EVENT
        # ═══════════════════════════════════════════════════════════════
        sidebar = QFrame()
        sidebar.setStyleSheet(styles.GLASS_PANEL)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 14, 16, 14)
        sidebar_layout.setSpacing(10)

        self.lbl_selected_title = QLabel("Selected Date")
        self.lbl_selected_title.setFont(QFont("Consolas", 11, QFont.Bold))
        self.lbl_selected_title.setStyleSheet(styles.SECTION_LABEL)
        sidebar_layout.addWidget(self.lbl_selected_title)

        self.agenda_scroll = QScrollArea()
        self.agenda_scroll.setWidgetResizable(True)
        self.agenda_scroll.setStyleSheet(styles.SCROLL_STYLE)

        self.agenda_content = QWidget()
        self.agenda_content.setStyleSheet("background: transparent;")
        self.agenda_layout = QVBoxLayout(self.agenda_content)
        self.agenda_layout.setSpacing(8)
        self.agenda_layout.setContentsMargins(0, 0, 0, 0)
        self.agenda_layout.addStretch()

        self.agenda_scroll.setWidget(self.agenda_content)
        sidebar_layout.addWidget(self.agenda_scroll, stretch=1)

        # Create event form
        lbl_sch = QLabel("SCHEDULE EVENT:")
        lbl_sch.setFont(QFont("Consolas", 9, QFont.Bold))
        lbl_sch.setStyleSheet(styles.DIM_LABEL)
        sidebar_layout.addWidget(lbl_sch)

        self.event_title = QLineEdit()
        self.event_title.setPlaceholderText("Event Name...")
        self.event_title.setFont(QFont("Consolas", 10))
        self.event_title.setStyleSheet(styles.INPUT_STYLE)
        sidebar_layout.addWidget(self.event_title)

        self.event_start = QDateTimeEdit()
        self.event_start.setDateTime(QDateTime.currentDateTime())
        self.event_start.setCalendarPopup(True)
        self.event_start.setFont(QFont("Consolas", 9))
        self.event_start.setStyleSheet(styles.INPUT_STYLE)
        sidebar_layout.addWidget(self.event_start)

        btn_add = QPushButton("ADD EVENT")
        btn_add.setFont(QFont("Consolas", 9, QFont.Bold))
        btn_add.setStyleSheet(styles.button_style(styles.GREEN))
        btn_add.clicked.connect(self.save_event_action)
        sidebar_layout.addWidget(btn_add)

        main_layout.addWidget(sidebar, stretch=2)

    # ── Calendar rendering ───────────────────────────────────────────────

    def render_calendar(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.cell_widgets.clear()

        cal_obj = calendar.Calendar(firstweekday=0)
        month_days = cal_obj.monthdayscalendar(
            self.current_year, self.current_month
        )

        month_name = calendar.month_name[self.current_month]
        self.lbl_month_yr.setText(
            f"{month_name.upper()} {self.current_year}"
        )

        events = get_events()
        reminders = get_reminders(include_completed=True)
        tasks = get_tasks()
        today = date.today()

        if self.view_mode == "Week":
            start = self.selected_date - timedelta(
                days=self.selected_date.weekday()
            )
            month_days = [
                [(start + timedelta(days=i)).day for i in range(7)]
            ]
            self.lbl_month_yr.setText(
                f"WEEK OF {start.strftime('%d %B %Y').upper()}"
            )
        elif self.view_mode == "Day":
            month_days = [[0, 0, 0, self.selected_date.day, 0, 0, 0]]
            self.lbl_month_yr.setText(
                self.selected_date.strftime("DAY VIEW - %d %B %Y").upper()
            )

        for row_idx, week in enumerate(month_days):
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    cell = DayCell(0, None)
                    self.grid_layout.addWidget(cell, row_idx, col_idx)
                    continue

                if self.view_mode == "Week":
                    week_start = self.selected_date - timedelta(
                        days=self.selected_date.weekday()
                    )
                    cell_date = week_start + timedelta(days=col_idx)
                elif self.view_mode == "Day":
                    cell_date = self.selected_date
                else:
                    cell_date = date(
                        self.current_year, self.current_month, day_num
                    )

                cell = DayCell(
                    day_num, cell_date,
                    is_today=(cell_date == today),
                    is_selected=(cell_date == self.selected_date),
                    callback=self.on_day_clicked,
                )
                self.cell_widgets.append(cell)

                cell.set_has_indicator("events", any(
                    datetime.fromisoformat(ev["start_time"]).date() == cell_date
                    for ev in events
                ))
                cell.set_has_indicator("reminders", any(
                    datetime.fromisoformat(r["datetime"]).date() == cell_date
                    for r in reminders
                ))
                cell.set_has_indicator("tasks", any(
                    t["due_date"] == cell_date.isoformat()
                    for t in tasks if t["due_date"]
                ))

                self.grid_layout.addWidget(cell, row_idx, col_idx)

        self.refresh_agenda_list()

    # ── Navigation ───────────────────────────────────────────────────────

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.render_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.render_calendar()

    def change_view_mode(self, mode):
        self.view_mode = mode
        self.render_calendar()

    def on_day_clicked(self, clicked_date, clicked_cell):
        for cell in self.cell_widgets:
            cell.set_selected(False)
        clicked_cell.set_selected(True)
        self.selected_date = clicked_date
        self.refresh_agenda_list()
        self.event_start.setDateTime(
            QDateTime.fromPyDateTime(
                datetime.combine(clicked_date, datetime.now().time())
            )
        )

    # ── Agenda sidebar ───────────────────────────────────────────────────

    def refresh_agenda_list(self):
        self.lbl_selected_title.setText(
            self.selected_date.strftime("%d %B %Y").upper()
        )

        for i in reversed(range(self.agenda_layout.count())):
            widget = self.agenda_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        day_iso = self.selected_date.isoformat()
        events = [
            ev for ev in get_events()
            if datetime.fromisoformat(ev["start_time"]).date() == self.selected_date
        ]
        reminders = [
            r for r in get_reminders(include_completed=True)
            if datetime.fromisoformat(r["datetime"]).date() == self.selected_date
        ]
        tasks = [
            t for t in get_tasks() if t["due_date"] == day_iso
        ]

        idx = 0
        for ev in events:
            card = self._agenda_card(
                f"EVENT: {ev['title']}",
                ev["description"] or "Meeting",
                styles.CYAN, ev["id"], is_event=True, event=ev,
            )
            self.agenda_layout.insertWidget(idx, card)
            idx += 1

        for r in reminders:
            status = "Completed" if r["is_completed"] else "Pending"
            card = self._agenda_card(
                f"REMINDER: {r['text']}",
                f"Status: {status}", styles.GREEN, r["id"],
            )
            self.agenda_layout.insertWidget(idx, card)
            idx += 1

        for t in tasks:
            sts = t["status"].capitalize()
            card = self._agenda_card(
                f"TASK: {t['title']}",
                f"Status: {sts} | Priority: {t['priority']}",
                styles.AMBER, t["id"],
            )
            self.agenda_layout.insertWidget(idx, card)
            idx += 1

        if idx == 0:
            empty = QLabel("No entries for this date.")
            empty.setFont(QFont("Consolas", 10))
            empty.setStyleSheet(styles.DIM_LABEL)
            self.agenda_layout.insertWidget(0, empty)

    def _agenda_card(self, title, desc, color, item_id,
                     is_event=False, event=None):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(4, 10, 18, 210);
                border: 1px solid {color}50;
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Consolas", 9, QFont.Bold))
        lbl_title.setStyleSheet(styles.BODY_LABEL)
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)

        lbl_desc = QLabel(desc)
        lbl_desc.setFont(QFont("Consolas", 8))
        lbl_desc.setStyleSheet(styles.DIM_LABEL)
        layout.addWidget(lbl_desc)

        if is_event:
            btn_edit = QPushButton("EDIT")
            btn_edit.setStyleSheet(styles.button_style(styles.CYAN, 4))
            btn_edit.clicked.connect(
                lambda checked, ev=event: self.edit_event_action(ev)
            )
            layout.addWidget(btn_edit)

            btn_del = QPushButton("✕ REMOVE")
            btn_del.setStyleSheet(styles.button_style(styles.RED, 4))
            btn_del.clicked.connect(
                lambda checked, eid=item_id: self.delete_event_action(eid)
            )
            layout.addWidget(btn_del)

        return card

    # ── Event CRUD ───────────────────────────────────────────────────────

    def delete_event_action(self, event_id):
        delete_event(event_id)
        play_notification_beep()
        self.render_calendar()

    def edit_event_action(self, event):
        if not event:
            return
        self.editing_event_id = event["id"]
        self.event_title.setText(event["title"])
        self.event_start.setDateTime(
            QDateTime.fromPyDateTime(
                datetime.fromisoformat(event["start_time"])
            )
        )

    def save_event_action(self):
        title = self.event_title.text().strip()
        if not title:
            return

        start = self.event_start.dateTime().toPyDateTime()
        end = start + timedelta(hours=1)

        if self.editing_event_id:
            update_event(
                self.editing_event_id,
                title=title,
                description="Scheduled via calendar HUD",
                start_time=start.isoformat(),
                end_time=end.isoformat(),
            )
            self.editing_event_id = None
        else:
            add_event(
                title=title,
                description="Scheduled via calendar HUD",
                start_time=start.isoformat(),
                end_time=end.isoformat(),
            )

        self.event_title.clear()
        play_notification_beep()
        self.render_calendar()
