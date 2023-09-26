import datetime
import hashlib
import os
import shutil
import time

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


class Sync:
    def __init__(self, dir_source, dir_replica):
        self.dir_source = dir_source
        self.dir_replica = dir_replica
        self.dir_source_hashed = Sync.hash_directory(dir_source)
        self.dir_replica_hashed = Sync.hash_directory(dir_replica)

    def __str__(self):
        return f"source: {self.dir_source}\nreplica: {self.dir_replica}"

    def hash_directory(self):
        block_size = 65536
        hashed_dir = {}
        for dirpath, dirnames, filenames in os.walk(self):
            for filename in filenames:
                file_hash = hashlib.sha256()
                full_path = os.path.join(dirpath, filename)
                with open(full_path, 'rb') as f:
                    fb = f.read(block_size)
                    while len(fb) > 0:
                        file_hash.update(fb)
                        fb = f.read(block_size)
                hashed_dir.update({file_hash.hexdigest(): filename})

        return hashed_dir

    def compare(self):
        source_diff_keys = {}
        marked_for_del = {}
        for key, value in self.dir_source_hashed.items():
            if key not in self.dir_replica_hashed:
                source_diff_keys[key] = value
        for key, value in self.dir_replica_hashed.items():
            if key not in self.dir_source_hashed:
                marked_for_del[key] = value

        source_diff_message = "All files in source folder are present in target folder" if not source_diff_keys else source_diff_keys
        marked_for_del_message = "All files in target folder are present in source folder" if not marked_for_del else marked_for_del

        return source_diff_keys, marked_for_del, source_diff_message, marked_for_del_message

    def sync_copy(self):
        for value in self.values():
            try:
                message = (f"copying {value} from: {os.path.join(sync_instance.dir_source)}"
                           f" to replica {os.path.join(sync_instance.dir_replica)}")
                print(message)
                log_to_file(log_file_path, message)
                shutil.copy(os.path.join(sync_instance.dir_source, value),
                            os.path.join(sync_instance.dir_replica, value))
            except Exception as e:
                current_datetime = datetime.datetime.now()
                message = (f"{current_datetime}: encountered an error during copy {e}.")
                print(message)
                log_to_file(log_file_path, message)

    def remove_excess(self):
        for value in self.values():
            try:
                print(f"delete: {os.path.join(sync_instance.dir_replica, value)}")
                message = (f"delete: {os.path.join(sync_instance.dir_replica, value)}")
                print(message)
                log_to_file(log_file_path, message)
                os.remove(os.path.join(sync_instance.dir_replica, value))
            except Exception as e:
                current_datetime = datetime.datetime.now()
                message = f"{current_datetime}: encountered an Error during removal from target folder: {e}."
                print(message)
                log_to_file(log_file_path, message)


def log_to_file(log_file_path, message):
    current_datetime = datetime.datetime.now()
    log_entry = f"{current_datetime}: {message}\n"
    operation = "a" if os.path.isfile(log_file_path) else "w"
    with open(log_file_path, operation) as log_file:
        log_file.write(log_entry)
        log_file.close()


def create_log(self):
    current_datetime = datetime.datetime.now()
    message = f"{current_datetime}: Synchronization has been started."
    log_to_file(log_file_path, message)


if __name__ == "__main__":
    source_input = input("Please enter path to source folder: ")
    target_input = input("Please enter path to target folder: ")
    sync_instance = Sync(source_input, target_input)
    interval_input = input("Enter the time interval in seconds, minutes, or hours (e.g., '30 seconds', '1 hour'): ")
    input_log = input("Please enter logfile path: ") + "\\" + "sync.log"

    # input_log = "C:\\Users\\GeeLord\\PycharmProjects\\veeam_task\\sync.log"
    log_file_path = input_log

    # sync_instance = Sync("C:\\Users\\GeeLord\\Downloads\\ProcessMonitor", "C:\\Users\\GeeLord\\Downloads\\Nová složka")

    # interval_input = "2 seconds"

    # Get the current date and time
    # current_datetime = datetime.datetime.now()

    create_log(input_log)


    def sync_job():
        # sync_instance = Sync("C:\\Users\\GeeLord\\Downloads\\ProcessMonitor", "C:\\Users\\GeeLord\\Downloads\\Nová složka")
        sync_instance = Sync(source_input, target_input)
        results = sync_instance.compare()

        source_diff_keys, marked_for_del, source_diff_message, marked_for_del_message = results

        if not source_diff_keys:
            print(source_diff_message)  # Print the message if the dictionary is empty
            log_to_file(log_file_path, source_diff_message)
        else:
            # print(f"Marked for copy: {source_diff_keys}")
            Sync.sync_copy(source_diff_keys)

        if not marked_for_del:
            print(marked_for_del_message)  # Print the message if the dictionary is empty
            log_to_file(log_file_path, marked_for_del_message)
        else:
            # print(f"Marked for removal: {marked_for_del}")
            Sync.remove_excess(marked_for_del)


    sync_job()

    try:
        # Split the user input into quantity and unit (seconds, minutes, hours)
        quantity, unit = interval_input.split()
        quantity = int(quantity)

        # Convert unit to APScheduler interval
        interval = None
        if unit.startswith('second'):
            interval = 'seconds'
        elif unit.startswith('minute'):
            interval = 'minutes'
        elif unit.startswith('hour'):
            interval = 'hours'

        if interval:
            # Schedule the job with the specified interval
            scheduler.add_job(sync_job, trigger='interval', seconds=quantity, misfire_grace_time=10)
            scheduler.start()

            while True:
                time.sleep(1)
        else:
            print("Invalid input. Please specify a valid time interval.")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
