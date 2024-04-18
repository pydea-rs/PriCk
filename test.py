import atexit
import os
import sched
import threading
import time

def scheduled_task(scheduler):
    print("This is a scheduled task.")
    # Schedule the task to run again after 5 seconds
    scheduler.enter(5, 1, scheduled_task, (scheduler,))

def scheduler_thread():
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, scheduled_task, (scheduler,))
    scheduler.run()

def initialize_scheduler():
    thread = threading.Thread(target=scheduler_thread)
    thread.daemon = True
    thread.start()

# Run the scheduler when the WSGI script is loaded
initialize_scheduler()

# Ensure that the scheduler thread is stopped when the script exits
def exit_handler():
    print("Exiting the WSGI script.")
    os._exit(0)  # Terminate the process forcefully

atexit.register(exit_handler)

print("done")