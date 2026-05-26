# scheduler/background_scheduler.py

import json
import time
import threading
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread, pyqtSignal

from database.db_manager import get_alarms, get_reminders, update_alarm, update_reminder, add_timer_log
from utils.time_service import now_naive


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
        self.active_timers = []
        self._timer_lock = threading.RLock()
        self.last_checked_minute = -1
        self.triggered_alarms_this_minute = set()
        self.triggered_reminders_this_minute = set()

    def run(self):
        print("JARVIS Background Scheduler Thread started.")
        while self.running:
            try:
                now = now_naive()
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
                completed_timers = []
                with self._timer_lock:
                    monotonic_now = time.monotonic()
                    for timer in self.active_timers[:]:
                        if timer.get('status') != 'running':
                            continue
                        remaining = max(0.0, timer['end_monotonic'] - monotonic_now)
                        timer['remaining_seconds'] = remaining
                        timer['seconds_left'] = int(round(remaining))
                        if remaining <= 0:
                            timer['remaining_seconds'] = 0.0
                            timer['seconds_left'] = 0
                            completed_timers.append(dict(timer))
                            self.active_timers.remove(timer)

                for timer in completed_timers:
                    add_timer_log(timer.get('total', 0), now.isoformat(timespec="seconds"), timer.get('label', 'Timer'))
                    self.timer_completed.emit(timer)

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
        duration_seconds = max(1, int(duration_seconds))
        with self._timer_lock:
            self.active_timers.append({
                'id': str(timer_id),
                'seconds_left': duration_seconds,
                'remaining_seconds': float(duration_seconds),
                'total': duration_seconds,
                'label': label,
                'status': 'running',
                'started_at': now_naive().isoformat(timespec="seconds"),
                'end_monotonic': time.monotonic() + duration_seconds
            })

    def stop_timer(self, timer_id):
        """
        Stops and removes a countdown timer.
        """
        with self._timer_lock:
            for timer in self.active_timers[:]:
                if timer['id'] == str(timer_id):
                    self.active_timers.remove(timer)
                    break

    def pause_timer(self, timer_id):
        with self._timer_lock:
            for timer in self.active_timers:
                if timer['id'] == str(timer_id) and timer.get('status') == 'running':
                    timer['remaining_seconds'] = max(0.0, timer['end_monotonic'] - time.monotonic())
                    timer['seconds_left'] = int(round(timer['remaining_seconds']))
                    timer['status'] = 'paused'
                    return True
        return False

    def resume_timer(self, timer_id):
        with self._timer_lock:
            for timer in self.active_timers:
                if timer['id'] == str(timer_id) and timer.get('status') == 'paused':
                    timer['end_monotonic'] = time.monotonic() + float(timer.get('remaining_seconds', 0))
                    timer['status'] = 'running'
                    return True
        return False

    def reset_timer(self, timer_id):
        with self._timer_lock:
            for timer in self.active_timers:
                if timer['id'] == str(timer_id):
                    timer['remaining_seconds'] = float(timer['total'])
                    timer['seconds_left'] = int(timer['total'])
                    timer['end_monotonic'] = time.monotonic() + float(timer['total'])
                    timer['status'] = 'running'
                    return True
        return False

    def get_active_timers(self):
        with self._timer_lock:
            return [dict(timer) for timer in self.active_timers]

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
