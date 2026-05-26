from datetime import datetime

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import (
    QDateTimeEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from database.db_manager import add_reminder, delete_reminder, get_reminders


class ReminderPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(260)
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(5, 12, 18, 220);
                color: white;
                font-family: Consolas;
            }
            QLabel {
                color: #8be9ff;
                font-weight: bold;
            }
            QLineEdit, QDateTimeEdit, QListWidget {
                background-color: #0b1720;
                border: 1px solid #17475c;
                border-radius: 4px;
                color: white;
                padding: 6px;
            }
            QPushButton {
                background-color: #0f95c8;
                border: 0;
                border-radius: 4px;
                color: white;
                padding: 7px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #17b8f2;
            }
            """
        )

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Reminder")

        self.time_input = QDateTimeEdit()
        self.time_input.setCalendarPopup(True)
        self.time_input.setDateTime(
            QDateTime.currentDateTime()
        )
        self.time_input.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        self.refresh_button = QPushButton("Refresh")

        self.list_widget = QListWidget()

        header = QLabel("REMINDERS")

        button_row = QHBoxLayout()
        button_row.addWidget(self.add_button)
        button_row.addWidget(self.delete_button)

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(self.title_input)
        layout.addWidget(self.time_input)
        layout.addLayout(button_row)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.add_button.clicked.connect(self.add_reminder)
        self.delete_button.clicked.connect(self.delete_selected)
        self.refresh_button.clicked.connect(self.refresh)

        self.refresh()

    def add_reminder(self):
        title = self.title_input.text().strip()

        if not title:
            QMessageBox.warning(
                self,
                "Reminder",
                "Please enter a reminder."
            )
            return

        remind_at = self.time_input.dateTime().toPyDateTime()

        if remind_at < datetime.now():
            QMessageBox.warning(
                self,
                "Reminder",
                "Please choose a future time."
            )
            return

        add_reminder(
            text=title,
            datetime_str=remind_at.isoformat(timespec="seconds"),
            category="Panel",
            priority="Medium",
            recurrence="None"
        )
        self.title_input.clear()
        self.refresh()

    def delete_selected(self):
        item = self.list_widget.currentItem()

        if not item:
            return

        delete_reminder(item.data(1))
        self.refresh()

    def refresh(self):
        self.list_widget.clear()

        for reminder in get_reminders(include_completed=False):
            remind_at = datetime.fromisoformat(reminder["datetime"])
            text = (
                f"{reminder['id']} | {reminder['text']} | "
                f"{remind_at.strftime('%d %b %I:%M %p')}"
            )
            item = QListWidgetItem(text)
            item.setData(1, reminder["id"])
            self.list_widget.addItem(item)
