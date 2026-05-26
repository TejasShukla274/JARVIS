# gui/calendar_tab.py

import calendar
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QLineEdit, QDateTimeEdit
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

from database.db_manager import add_event, get_events, get_reminders, get_tasks, delete_event
from utils.audio_player import play_notification_beep


class DayCell(QFrame):
    """
    Custom cell for calendar day grids.
    Paints highlights and indicator dots.
    """
    def __init__(self, day_num, full_date, is_today=False, is_selected=False, callback=None):
        super().__init__()
        self.day_num = day_num
        self.full_date = full_date
        self.is_today = is_today
        self.is_selected = is_selected
        self.callback = callback
        self.indicators = {'events': False, 'reminders': False, 'tasks': False}

        self.setup_ui()

    def setup_ui(self):
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(45, 45)
        self.update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Day Number
        self.lbl_num = QLabel(str(self.day_num) if self.day_num > 0 else "")
        self.lbl_num.setFont(QFont("Consolas", 10, QFont.Bold))
        self.lbl_num.setStyleSheet("color: white; border: none; background: transparent;")
        layout.addWidget(self.lbl_num, alignment=Qt.AlignTop | Qt.AlignLeft)
        
        # Indicator dots layout
        dot_layout = QHBoxLayout()
        dot_layout.setSpacing(2)
        dot_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(dot_layout)
        
        self.dots = []
        # Setup small color pins for active items
        for key, color in [('events', '#00aaff'), ('reminders', '#00ffaa'), ('tasks', '#ffaa00')]:
            dot = QFrame()
            dot.setFixedSize(5, 5)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 2px; border: none;")
            dot.setVisible(False)
            dot_layout.addWidget(dot)
            self.indicators[key] = dot

    def update_style(self):
        bg = "rgba(10, 10, 15, 200)"
        border = "rgba(0, 170, 255, 30)"
        
        if self.is_today:
            bg = "rgba(0, 170, 255, 40)"
            border = "#00aaff"
        elif self.is_selected:
            bg = "rgba(0, 255, 170, 30)"
            border = "#00ffaa"
            
        self.setStyleSheet(f"""
            DayCell {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
        """)

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def set_has_indicator(self, key, active):
        if key in self.indicators:
            self.indicators[key].setVisible(active)

    def mousePressEvent(self, event):
        if self.callback and self.day_num > 0:
            self.callback(self.full_date, self)
        super().mousePressEvent(event)


class CalendarTab(QWidget):
    """
    Fully interactive offline Calendar System. Syncs events, tasks, and reminders
    together, showing markers on a custom monthly grid and presenting a detailed daily agenda.
    """
    def __init__(self):
        super().__init__()
        self.selected_date = date.today()
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.cell_widgets = []
        
        self.setup_ui()
        self.render_calendar()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # =====================================================================
        # LEFT SIDE: CALENDAR GRID FRAME
        # =====================================================================
        cal_container = QWidget()
        cal_container.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        cal_layout = QVBoxLayout(cal_container)
        cal_layout.setContentsMargins(15, 15, 15, 15)

        # Header Month-Year Navigation
        nav_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFont(QFont("Consolas", 10, QFont.Bold))
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 170, 255, 20);
                color: #00aaff;
                border: 1px solid #00aaff;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(0, 170, 255, 50);
            }
        """)
        self.btn_prev.clicked.connect(self.prev_month)
        nav_layout.addWidget(self.btn_prev)

        self.lbl_month_yr = QLabel("Month Year")
        self.lbl_month_yr.setFont(QFont("Consolas", 12, QFont.Bold))
        self.lbl_month_yr.setStyleSheet("color: white; border: none;")
        self.lbl_month_yr.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.lbl_month_yr, stretch=1)

        self.btn_next = QPushButton("▶")
        self.btn_next.setFont(QFont("Consolas", 10, QFont.Bold))
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 170, 255, 20);
                color: #00aaff;
                border: 1px solid #00aaff;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(0, 170, 255, 50);
            }
        """)
        self.btn_next.clicked.connect(self.next_month)
        nav_layout.addWidget(self.btn_next)
        cal_layout.addLayout(nav_layout)

        # Weekdays header row
        week_grid = QGridLayout()
        week_grid.setSpacing(6)
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for idx, day in enumerate(days):
            lbl = QLabel(day)
            lbl.setFont(QFont("Consolas", 8, QFont.Bold))
            lbl.setStyleSheet("color: #00e5ff; border: none;")
            lbl.setAlignment(Qt.AlignCenter)
            week_grid.addWidget(lbl, 0, idx)
        cal_layout.addLayout(week_grid)

        # Days grid QWidget
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent; border: none;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.addWidget(self.grid_widget)

        main_layout.addWidget(cal_container, stretch=3)

        # =====================================================================
        # RIGHT SIDE: SIDEBAR DAILY AGENDA & CREATE EVENT
        # =====================================================================
        sidebar = QWidget()
        sidebar.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 25, 180);
                border: 1px solid rgba(0, 170, 255, 40);
                border-radius: 12px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)

        self.lbl_selected_title = QLabel("Selected Date")
        self.lbl_selected_title.setFont(QFont("Consolas", 11, QFont.Bold))
        self.lbl_selected_title.setStyleSheet("color: #00ffaa; letter-spacing: 1px; border: none;")
        sidebar_layout.addWidget(self.lbl_selected_title)

        # Scroll Area for Agenda items
        self.agenda_scroll = QScrollArea()
        self.agenda_scroll.setWidgetResizable(True)
        self.agenda_scroll.setStyleSheet("border: none; background: transparent;")
        
        self.agenda_content = QWidget()
        self.agenda_content.setStyleSheet("background: transparent;")
        self.agenda_layout = QVBoxLayout(self.agenda_content)
        self.agenda_layout.setSpacing(8)
        self.agenda_layout.setContentsMargins(0, 0, 0, 0)
        self.agenda_layout.addStretch()
        
        self.agenda_scroll.setWidget(self.agenda_content)
        sidebar_layout.addWidget(self.agenda_scroll, stretch=1)

        # Create Event Sub-panel
        sidebar_layout.addWidget(QLabel("SCHEDULE EVENT:"), alignment=Qt.AlignTop)
        
        self.event_title = QLineEdit()
        self.event_title.setPlaceholderText("Event Name...")
        self.event_title.setFont(QFont("Consolas", 10))
        self.event_title.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: #0c0c14;
                border: 1px solid rgba(0, 170, 255, 60);
                border-radius: 6px;
                padding: 6px;
            }
        """)
        sidebar_layout.addWidget(self.event_title)

        self.event_start = QDateTimeEdit()
        self.event_start.setDateTime(QDateTime.currentDateTime())
        self.event_start.setFont(QFont("Consolas", 9))
        self.event_start.setStyleSheet("""
            QDateTimeEdit {
                color: white;
                background-color: #0c0c14;
                border: 1px solid rgba(0, 170, 255, 60);
                border-radius: 6px;
                padding: 4px;
            }
        """)
        sidebar_layout.addWidget(self.event_start)

        btn_add = QPushButton("ADD EVENT MODULE")
        btn_add.setFont(QFont("Consolas", 9, QFont.Bold))
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 170, 20);
                color: #00ffaa;
                border: 1px solid #00ffaa;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 170, 50);
            }
        """)
        btn_add.clicked.connect(self.save_event_action)
        sidebar_layout.addWidget(btn_add)

        main_layout.addWidget(sidebar, stretch=2)
        self.setLayout(main_layout)

    def render_calendar(self):
        """
        Builds the custom day cells, checks databases for active events/reminders/tasks,
        attaches indicator dots, and populates the grid layout.
        """
        # Clear grid layout
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.cell_widgets.clear()

        # Month and year details
        cal_obj = calendar.Calendar(firstweekday=0)
        month_days = cal_obj.monthdayscalendar(self.current_year, self.current_month)
        
        # Display header
        month_name = calendar.month_name[self.current_month]
        self.lbl_month_yr.setText(f"{month_name.upper()} {self.current_year}")

        # Fetch models to calculate indicators
        events = get_events()
        reminders = get_reminders(include_completed=True)
        tasks = get_tasks()

        today = date.today()

        # Build cells row by row
        row_idx = 0
        for week in month_days:
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    # Empty space cell
                    cell = DayCell(0, None)
                    self.grid_layout.addWidget(cell, row_idx, col_idx)
                else:
                    cell_date = date(self.current_year, self.current_month, day_num)
                    is_today = (cell_date == today)
                    is_sel = (cell_date == self.selected_date)

                    cell = DayCell(day_num, cell_date, is_today, is_sel, self.on_day_clicked)
                    self.cell_widgets.append(cell)

                    # Compute indicators
                    has_ev = any(
                        datetime.fromisoformat(ev['start_time']).date() == cell_date
                        for ev in events
                    )
                    has_rem = any(
                        datetime.fromisoformat(rem['datetime']).date() == cell_date
                        for rem in reminders
                    )
                    has_ts = any(
                        task['due_date'] == cell_date.isoformat()
                        for task in tasks
                        if task['due_date']
                    )

                    cell.set_has_indicator('events', has_ev)
                    cell.set_has_indicator('reminders', has_rem)
                    cell.set_has_indicator('tasks', has_ts)

                    self.grid_layout.addWidget(cell, row_idx, col_idx)
            row_idx += 1

        self.refresh_agenda_list()

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

    def on_day_clicked(self, clicked_date, clicked_cell):
        # Deselect old cells
        for cell in self.cell_widgets:
            cell.set_selected(False)

        # Select new cell
        clicked_cell.set_selected(True)
        self.selected_date = clicked_date
        
        # Populate agenda sidebar
        self.refresh_agenda_list()
        
        # Sync datetime inputs
        self.event_start.setDateTime(
            datetime.combine(clicked_date, datetime.now().time())
        )

    def refresh_agenda_list(self):
        """
        Combines alarms, tasks, reminders, and calendar events for the selected day
        and shows them in a unified sidebar schedule view.
        """
        self.lbl_selected_title.setText(self.selected_date.strftime("%d %B %Y").upper())

        # Clear layout children except final stretch spacer
        for i in reversed(range(self.agenda_layout.count())):
            item = self.agenda_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        day_iso = self.selected_date.isoformat()
        
        # Fetch items matching day
        events = [
            ev for ev in get_events()
            if datetime.fromisoformat(ev['start_time']).date() == self.selected_date
        ]
        reminders = [
            rem for rem in get_reminders(include_completed=True)
            if datetime.fromisoformat(rem['datetime']).date() == self.selected_date
        ]
        tasks = [
            t for t in get_tasks()
            if t['due_date'] == day_iso
        ]

        agenda_idx = 0

        # Display Events
        for ev in events:
            card = self.create_agenda_card(f"EVENT: {ev['title']}", ev['description'] or "Meeting", "#00aaff", ev['id'], is_event=True)
            self.agenda_layout.insertWidget(agenda_idx, card)
            agenda_idx += 1

        # Display Reminders
        for rem in reminders:
            status = "Completed" if rem['is_completed'] else "Pending"
            card = self.create_agenda_card(f"REMINDER: {rem['text']}", f"Status: {status}", "#00ffaa", rem['id'])
            self.agenda_layout.insertWidget(agenda_idx, card)
            agenda_idx += 1

        # Display Tasks
        for t in tasks:
            status = "Todo" if t['status'].lower() == "todo" else ("Doing" if t['status'].lower() == "doing" else "Done")
            card = self.create_agenda_card(f"TASK: {t['title']}", f"Status: {status} | Priority: {t['priority']}", "#ffaa00", t['id'])
            self.agenda_layout.insertWidget(agenda_idx, card)
            agenda_idx += 1

        if agenda_idx == 0:
            empty = QLabel("No entries for this date.")
            empty.setFont(QFont("Consolas", 10))
            empty.setStyleSheet("color: rgba(255,255,255, 100); border: none;")
            self.agenda_layout.insertWidget(0, empty)

    def create_agenda_card(self, title, desc, border_color, item_id, is_event=False):
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(10, 10, 15, 200);
                border: 1px solid {border_color}50;
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header Title
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Consolas", 9, QFont.Bold))
        title_lbl.setStyleSheet("color: white; border: none; background: transparent;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        # Description
        desc_lbl = QLabel(desc)
        desc_lbl.setFont(QFont("Consolas", 8))
        desc_lbl.setStyleSheet("color: rgba(255,255,255, 150); border: none; background: transparent;")
        layout.addWidget(desc_lbl)

        # Deletion for custom scheduled events directly in daily agenda
        if is_event:
            btn_del = QPushButton("✕ REMOVE EVENT")
            btn_del.setFont(QFont("Consolas", 8, QFont.Bold))
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 50, 50, 20);
                    color: #ff5252;
                    border: 1px solid #ff5252;
                    border-radius: 4px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 50, 50, 60);
                }
            """)
            btn_del.clicked.connect(lambda checked, eid=item_id: self.delete_event_action(eid))
            layout.addWidget(btn_del)

        return card

    def delete_event_action(self, event_id):
        delete_event(event_id)
        play_notification_beep()
        self.render_calendar()

    def save_event_action(self):
        title = self.event_title.text().strip()
        if not title:
            return
            
        start = self.event_start.dateTime().toPyDateTime()
        end = start + timedelta(hours=1)  # Default 1-hour duration

        add_event(
            title=title,
            description="Scheduled via calendar HUD",
            start_time=start.isoformat(),
            end_time=end.isoformat(),
            color="#00aaff",
            category="Meeting"
        )
        
        self.event_title.clear()
        play_notification_beep()
        self.render_calendar()
