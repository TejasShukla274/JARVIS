# gui/tasks_tab.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Task Manager — Kanban board + list view with futuristic styling.
# ─────────────────────────────────────────────────────────────────────────────

import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFrame, QStackedWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from database.db_manager import add_task, get_tasks, update_task, delete_task
from utils.audio_player import play_notification_beep
from gui import styles


class TasksTab(QWidget):
    """
    Futuristic Task Manager with Kanban Board and List Views,
    priority flags, progress statistics, and task creation.
    """

    def __init__(self):
        super().__init__()
        self.view_mode = "kanban"
        self.setup_ui()
        self.refresh_tasks()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ═══════════════════════════════════════════════════════════════
        # LEFT: KANBAN / LIST VIEWS
        # ═══════════════════════════════════════════════════════════════
        left_panel = QFrame()
        left_panel.setStyleSheet(styles.GLASS_PANEL)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)

        # Header row
        ctrl = QHBoxLayout()
        title = QLabel("TASK SCHEMATICS")
        title.setFont(QFont("Consolas", 12, QFont.Bold))
        title.setStyleSheet(styles.SECTION_LABEL)
        ctrl.addWidget(title)

        self.lbl_stats = QLabel("Stats: Loading...")
        self.lbl_stats.setFont(QFont("Consolas", 9))
        self.lbl_stats.setStyleSheet(styles.HEADER_LABEL)
        ctrl.addWidget(self.lbl_stats)

        self.btn_view_mode = QPushButton("LIST VIEW")
        self.btn_view_mode.setFont(QFont("Consolas", 9, QFont.Bold))
        self.btn_view_mode.setStyleSheet(styles.button_style(styles.CYAN, 6))
        self.btn_view_mode.clicked.connect(self.toggle_view_mode)
        ctrl.addWidget(self.btn_view_mode)
        left_layout.addLayout(ctrl)

        # Stacked views
        self.view_stack = QStackedWidget()
        self.view_stack.setStyleSheet("background: transparent; border: none;")

        # Kanban
        self.kanban_widget = QWidget()
        self.kanban_widget.setStyleSheet("background: transparent; border: none;")
        kanban_layout = QHBoxLayout(self.kanban_widget)
        kanban_layout.setSpacing(10)
        kanban_layout.setContentsMargins(0, 0, 0, 0)

        self.col_todo = self._create_column("TO-DO LIST", styles.RED)
        self.col_doing = self._create_column("IN PROGRESS", styles.AMBER)
        self.col_done = self._create_column("COMPLETED", styles.GREEN)

        kanban_layout.addWidget(self.col_todo)
        kanban_layout.addWidget(self.col_doing)
        kanban_layout.addWidget(self.col_done)

        # List view
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent; border: none;")
        list_layout = QVBoxLayout(self.list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setStyleSheet(styles.SCROLL_STYLE)

        self.list_scroll_content = QWidget()
        self.list_scroll_content.setStyleSheet("background: transparent;")
        self.list_scroll_layout = QVBoxLayout(self.list_scroll_content)
        self.list_scroll_layout.setSpacing(8)
        self.list_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.list_scroll_layout.addStretch()

        self.list_scroll.setWidget(self.list_scroll_content)
        list_layout.addWidget(self.list_scroll)

        self.view_stack.addWidget(self.kanban_widget)
        self.view_stack.addWidget(self.list_widget)
        left_layout.addWidget(self.view_stack)

        main_layout.addWidget(left_panel, stretch=3)

        # ═══════════════════════════════════════════════════════════════
        # RIGHT: CREATE NEW TASK
        # ═══════════════════════════════════════════════════════════════
        right_panel = QFrame()
        right_panel.setStyleSheet(styles.GLASS_PANEL)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 16, 18, 16)
        right_layout.setSpacing(12)

        right_title = QLabel("REGISTER NEW TASK")
        right_title.setFont(QFont("Consolas", 11, QFont.Bold))
        right_title.setStyleSheet(styles.HEADER_LABEL)
        right_layout.addWidget(right_title)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Task title...")
        self.title_edit.setFont(QFont("Consolas", 10))
        self.title_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.title_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Description...")
        self.desc_edit.setFont(QFont("Consolas", 10))
        self.desc_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.desc_edit)

        self.due_edit = QLineEdit()
        self.due_edit.setPlaceholderText("Due Date (YYYY-MM-DD or 'None')")
        self.due_edit.setFont(QFont("Consolas", 10))
        self.due_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.due_edit)

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

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Category (e.g. Work, Study)")
        self.category_edit.setFont(QFont("Consolas", 10))
        self.category_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.category_edit)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tags (comma separated)")
        self.tags_edit.setFont(QFont("Consolas", 10))
        self.tags_edit.setStyleSheet(styles.INPUT_STYLE)
        right_layout.addWidget(self.tags_edit)

        btn_deploy = QPushButton("DEPLOY TASK")
        btn_deploy.setFont(QFont("Consolas", 10, QFont.Bold))
        btn_deploy.setStyleSheet(styles.button_style(styles.GREEN))
        btn_deploy.clicked.connect(self.save_new_task)
        right_layout.addWidget(btn_deploy)
        right_layout.addStretch()

        main_layout.addWidget(right_panel, stretch=2)

    # ── Kanban column factory ────────────────────────────────────────────

    def _create_column(self, title, border_color):
        col = QFrame()
        col.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(4, 10, 18, 140);
                border: 1px solid {styles.CYAN_FAINT};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(col)
        layout.setContentsMargins(10, 10, 10, 10)

        hdr = QLabel(title)
        hdr.setFont(QFont("Consolas", 10, QFont.Bold))
        hdr.setStyleSheet(
            f"color: {border_color}; border: none; background: transparent;"
        )
        layout.addWidget(hdr, alignment=Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(styles.SCROLL_STYLE)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        col.setProperty("scroll_layout", scroll_layout)
        return col

    # ── View toggle ──────────────────────────────────────────────────────

    def toggle_view_mode(self):
        if self.view_mode == "kanban":
            self.view_mode = "list"
            self.btn_view_mode.setText("KANBAN VIEW")
            self.view_stack.setCurrentIndex(1)
        else:
            self.view_mode = "kanban"
            self.btn_view_mode.setText("LIST VIEW")
            self.view_stack.setCurrentIndex(0)
        self.refresh_tasks()

    # ── Refresh ──────────────────────────────────────────────────────────

    def refresh_tasks(self):
        tasks = get_tasks()

        total = len(tasks)
        completed = sum(1 for t in tasks if t["status"].lower() == "done")
        ratio = (completed / total * 100) if total > 0 else 0
        self.lbl_stats.setText(f"Done: {completed}/{total} ({ratio:.0f}%)")

        self._clear_column(self.col_todo)
        self._clear_column(self.col_doing)
        self._clear_column(self.col_done)
        self._clear_list()

        for idx, task in enumerate(tasks):
            # Kanban card
            card = self._make_card(task)
            status = task["status"].lower()
            col = (
                self.col_todo if status == "todo"
                else self.col_doing if status == "doing"
                else self.col_done
            )
            sl = col.property("scroll_layout")
            sl.insertWidget(sl.count() - 1, card)

            # List card
            list_card = self._make_card(task)
            self.list_scroll_layout.insertWidget(idx, list_card)

    def _clear_column(self, col):
        layout = col.property("scroll_layout")
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def _clear_list(self):
        for i in reversed(range(self.list_scroll_layout.count())):
            widget = self.list_scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    # ── Card factory ─────────────────────────────────────────────────────

    def _make_card(self, task):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(4, 10, 18, 230);
                border: 1px solid {styles.CYAN_FAINT};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Title + category
        title_row = QHBoxLayout()
        lbl_title = QLabel(task["title"])
        lbl_title.setFont(QFont("Consolas", 10, QFont.Bold))
        lbl_title.setWordWrap(True)
        is_done = task["status"].lower() == "done"
        lbl_title.setStyleSheet(
            styles.BODY_LABEL if not is_done
            else f"color: {styles.WHITE_FAINT}; text-decoration: line-through; "
                 "border: none; background: transparent;"
        )
        title_row.addWidget(lbl_title, stretch=1)

        lbl_cat = QLabel(task["category"].upper())
        lbl_cat.setFont(QFont("Consolas", 7, QFont.Bold))
        lbl_cat.setStyleSheet(f"""
            QLabel {{
                color: {styles.CYAN}; border: 1px solid {styles.CYAN_DIM};
                border-radius: 4px; padding: 2px 6px;
                background: transparent;
            }}
        """)
        title_row.addWidget(lbl_cat)
        layout.addLayout(title_row)

        if task["description"]:
            lbl_desc = QLabel(task["description"])
            lbl_desc.setFont(QFont("Consolas", 8))
            lbl_desc.setStyleSheet(styles.DIM_LABEL)
            lbl_desc.setWordWrap(True)
            layout.addWidget(lbl_desc)

        # Meta row
        meta_row = QHBoxLayout()
        color_map = {
            "high": styles.RED,
            "medium": styles.AMBER,
            "low": styles.GREEN
        }
        p_color = color_map.get(task["priority"].lower(), styles.WHITE)
        lbl_pri = QLabel(task["priority"].upper())
        lbl_pri.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_pri.setStyleSheet(
            f"color: {p_color}; border: none; background: transparent;"
        )
        meta_row.addWidget(lbl_pri)

        lbl_due = QLabel(
            f"Due: {task['due_date']}" if task["due_date"] else "No Due"
        )
        lbl_due.setFont(QFont("Consolas", 8))
        lbl_due.setStyleSheet(styles.DIM_LABEL)
        meta_row.addWidget(lbl_due, alignment=Qt.AlignRight)
        layout.addLayout(meta_row)

        # Actions row — FIXED: lambda captures task_id via default arg
        action_row = QHBoxLayout()
        status = task["status"].lower()
        task_id = task["id"]

        if status == "todo":
            btn = QPushButton("ADVANCE ▶")
            btn.setStyleSheet(styles.button_style(styles.CYAN, 6))
            btn.clicked.connect(
                lambda checked, tid=task_id: self.update_task_status(tid, "doing")
            )
            action_row.addWidget(btn)
        elif status == "doing":
            btn = QPushButton("COMPLETE ✓")
            btn.setStyleSheet(styles.button_style(styles.GREEN, 6))
            btn.clicked.connect(
                lambda checked, tid=task_id: self.update_task_status(tid, "done")
            )
            action_row.addWidget(btn)
        else:
            lbl = QLabel("✓ Completed")
            lbl.setFont(QFont("Consolas", 9, QFont.Bold))
            lbl.setStyleSheet(
                f"color: {styles.GREEN}; border: none; background: transparent;"
            )
            action_row.addWidget(lbl)

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(26, 26)
        btn_del.setStyleSheet(styles.button_style(styles.RED, 6))
        btn_del.clicked.connect(
            lambda checked, tid=task_id: self.delete_task_action(tid)
        )
        action_row.addWidget(btn_del, alignment=Qt.AlignRight)
        layout.addLayout(action_row)

        return card

    # ── Actions ──────────────────────────────────────────────────────────

    def update_task_status(self, task_id, new_status):
        update_task(task_id, status=new_status)
        play_notification_beep()
        self.refresh_tasks()

    def delete_task_action(self, task_id):
        delete_task(task_id)
        play_notification_beep()
        self.refresh_tasks()

    def save_new_task(self):
        title = self.title_edit.text().strip()
        if not title:
            return

        desc = self.desc_edit.text().strip()
        due = self.due_edit.text().strip()
        if not due or due.lower() == "none":
            due = None

        priority = self.combo_priority.currentText()
        category = self.category_edit.text().strip() or "Work"
        raw_tags = self.tags_edit.text().split(",")
        tags = json.dumps([t.strip() for t in raw_tags if t.strip()])

        add_task(
            title=title,
            description=desc,
            due_date=due,
            priority=priority,
            tags=tags,
            category=category,
            status="todo",
        )

        self.title_edit.clear()
        self.desc_edit.clear()
        self.due_edit.clear()
        self.category_edit.clear()
        self.tags_edit.clear()

        play_notification_beep()
        self.refresh_tasks()
