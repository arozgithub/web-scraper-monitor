import schedule
import time
import threading

class SchedulerService:
    def __init__(self):
        self.cease_continuous_run = threading.Event()
        self._start_background_thread()

    def _start_background_thread(self):
        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not self.cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(1)

        self.continuous_thread = ScheduleThread()
        self.continuous_thread.start()

    def add_job(self, root_url, interval_val, interval_unit, job_func, *args):
        """Add or update a job for a specific root URL."""
        # Remove existing job for this tag first
        schedule.clear(root_url)
        
        print(f"Scheduling {root_url} every {interval_val} {interval_unit}")
        
        if interval_unit == 'seconds':
            schedule.every(interval_val).seconds.do(job_func, *args).tag(root_url)
        elif interval_unit == 'minutes':
            schedule.every(interval_val).minutes.do(job_func, *args).tag(root_url)
        elif interval_unit == 'hours':
            schedule.every(interval_val).hours.do(job_func, *args).tag(root_url)
        elif interval_unit == 'days':
            schedule.every(interval_val).days.do(job_func, *args).tag(root_url)

    def remove_job(self, root_url):
        """Remove a job by its tag (root_url)."""
        print(f"Removing schedule for {root_url}")
        schedule.clear(root_url)

    def stop(self):
        self.cease_continuous_run.set()
