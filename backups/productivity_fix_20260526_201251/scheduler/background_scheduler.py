# scheduler/background_scheduler.py

import json
import time
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread, pyqtSignal

from database.db_manager import get_alarms, get_reminders, update_alarm, update_reminder


class BackgroundScheduler(QThread):
    """
    Background worker thread running a persistent loop.
    Checks SQLite for alarms and reminders, and tracks countdown timers every second.
    """
    alarm_triggered = pyqtSignal(dict)
    reminder_triggered = pyqtSignal(dict)
    timer_completed = pyqtSignal(dict)
    second_tick = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True
        self.active_timers = []  # List of dicts: {'id': str, 'seconds_left': int, 'total': int, 'label': str}
        self.last_checked_minute = -1
        self.triggered_alarms_this_minute = set()
        self.triggered_reminders_this_minute = set()

    def run(self):
        print("JARVIS Background Scheduler Thread started.")
        while self.running:
            try:
                now = datetime.now()
                current_minute = now.minute
                current_time_str = now.strftime("%H:%M")  # 'HH:MM'
                weekday = now.weekday()  # 0 = Monday, 6 = Sunday

                # Clear triggered logs if a new minute starts
                if current_minute != self.last_checked_minute:
                    self.triggered_alarms_this_minute.clear()
                    self.triggered_reminders_this_minute.clear()
                    self.last_checked_minute = current_minute

                # 1. CHECK ALARMS
                alarms = get_alarms()
                for alarm in alarms:
                    if alarm['is_active'] == 0:
                        continue
                    
                    # Match exact HH:MM
                    if alarm['time'] == current_time_str:
                        alarm_id = alarm['id']
                        if alarm_id not in self.triggered_alarms_this_minute:
                            repeat_days = json.loads(alarm['repeat_days'])
                            
                            # Check repeats
                            should_trigger = False
                            if not repeat_days:
                                # One-time alarm
                                should_trigger = True
                                # Deactivate immediately
                                update_alarm(alarm_id, is_active=0)
                            else:
                                # Recurring alarm
                                if weekday in repeat_days:
                                    should_trigger = True
                                    
                            if should_trigger:
                                self.alarm_triggered.emit(dict(alarm))
                                self.triggered_alarms_this_minute.add(alarm_id)

                # 2. CHECK REMINDERS
                reminders = get_reminders(include_completed=False)
                for reminder in reminders:
                    reminder_dt = datetime.fromisoformat(reminder['datetime'])
                    
                    # If reminder time has passed or is exact
                    if now >= reminder_dt:
                        reminder_id = reminder['id']
                        if reminder_id not in self.triggered_reminders_this_minute:
                            # Mark as completed
                            update_reminder(reminder_id, is_completed=1)
                            
                            # Handle recurrence
                            recurrence = reminder['recurrence'].lower()
                            if recurrence != 'none':
                                self.schedule_next_recurring_reminder(reminder, reminder_dt)
                                
                            self.reminder_triggered.emit(dict(reminder))
                            self.triggered_reminders_this_minute.add(reminder_id)

                # 3. TICK DYNAMIC COUNTDOWN TIMERS
                for timer in self.active_timers[:]:
                    timer['seconds_left'] -= 1
                    if timer['seconds_left'] <= 0:
                        self.timer_completed.emit(timer)
                        self.active_timers.remove(timer)

                # 4. EMIT SYSTEM TICK
                self.second_tick.emit()

            except Exception as e:
                print("SCHEDULER LOOP ERROR:", e)

            # Rest 1 second
            time.sleep(1.0)

    def schedule_next_recurring_reminder(self, reminder, old_dt):
        """
        Calculates and schedules the next recurrence date for reminders.
        """
        recurrence = reminder['recurrence'].lower()
        if recurrence == 'daily':
            next_dt = old_dt + timedelta(days=1)
        elif recurrence == 'weekly':
            next_dt = old_dt + timedelta(weeks=1)
        elif recurrence == 'monthly':
            # Approximate monthly increment
            next_dt = old_dt + timedelta(days=30)
        else:
            return
            
        from database.db_manager import add_reminder
        add_reminder(
            text=reminder['text'],
            datetime_str=next_dt.isoformat(),
            category=reminder['category'],
            priority=reminder['priority'],
            recurrence=reminder['recurrence']
        )

    def start_timer(self, timer_id, duration_seconds, label="Timer"):
        """
        Registers a dynamic countdown timer in the background thread.
        """
        self.active_timers.append({
            'id': str(timer_id),
            'seconds_left': duration_seconds,
            'total': duration_seconds,
            'label': label
        })

    def stop_timer(self, timer_id):
        """
        Stops and removes a countdown timer.
        """
        for timer in self.active_timers:
            if timer['id'] == str(timer_id):
                self.active_timers.remove(timer)
                break

    def stop(self):
        self.running = False
        self.wait()


# Global Singleton Scheduler Reference
_global_scheduler = None

def get_scheduler():
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = BackgroundScheduler()
    return _global_scheduler
