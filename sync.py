import datetime
import hashlib
import os
import shutil
import time
from collections import defaultdict

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

    def hash_directory(directory):
        block_size = 65536
        hashed_dir = {}
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_hash = hashlib.sha256()

                full_path = os.path.join(dirpath, filename)
                with open(full_path, 'rb') as f:
                    fb = f.read(block_size)
                    while len(fb) > 0:
                        file_hash.update(fb)
                        fb = f.read(block_size)
                hashed_dir.update({full_path: file_hash.hexdigest()})

        return hashed_dir

    def compare(self):
        source_diff_keys = {}
        source_diff_keys_clones = {}
        marked_for_del = {}
        source_keys_rel = {os.path.relpath(key, self.dir_source): value for key, value in
                           self.dir_source_hashed.items()}
        replica_keys_rel = {os.path.relpath(key, self.dir_replica): value for key, value in
                            self.dir_replica_hashed.items()}

        for key, value in source_keys_rel.items():
            source_diff_keys_clones[os.path.join(self.dir_source, key)] = value
            if key not in replica_keys_rel:
                source_diff_keys[os.path.join(self.dir_source, key)] = value

        for key, value in replica_keys_rel.items():
            if key not in source_keys_rel:
                marked_for_del[os.path.join(self.dir_replica, key)] = value

        if source_diff_keys_clones is not {}:
            duplicate_values = defaultdict(list)
            for key, value in source_diff_keys_clones.items():
                duplicate_values[value].append(key)
            for hash_value, file_paths in duplicate_values.items():
                if len(file_paths) > 1:
                    # Dictionary to store files grouped by extension and directory name
                    extension_groups = {}

                    for file_path in file_paths:
                        # Extract the file extension and directory name
                        file_extension = os.path.splitext(file_path)[1].lower()
                        dir_name = os.path.dirname(file_path)

                        # Group files by extension and directory name
                        key = (file_extension, dir_name)
                        if key not in extension_groups:
                            extension_groups[key] = []
                        extension_groups[key].append(file_path)

                    for (file_extension, dir_name), group_file_paths in extension_groups.items():
                        if len(group_file_paths) > 1:
                            # Find the file with the longest filename (without extension)
                            shorter_file_path = min(group_file_paths,
                                                    key=lambda x: len(os.path.splitext(os.path.basename(x))[0]))
                            longest_file_path = max(group_file_paths,
                                                    key=lambda x: len(os.path.splitext(os.path.basename(x))[0]))
                            if (os.path.splitext(os.path.basename(shorter_file_path))[0] in
                                    os.path.splitext(os.path.basename(longest_file_path))[0]):
                                try:
                                    source_diff_keys.pop(longest_file_path)
                                except:
                                    message = f"Error when trying ignore duplicate file {longest_file_path}"
                                    print(message)
                                    log_to_file(log_file_path, message)
                                    continue

        source_diff_message = "All files in source folder are present in target folder" if not source_diff_keys else source_diff_keys
        marked_for_del_message = "All files in target folder are present in source folder" if not marked_for_del else marked_for_del

        return source_diff_keys, marked_for_del, source_diff_message, marked_for_del_message

    def sync_copy(self):
        for key in self.keys():
            try:
                dir_replica = sync_instance.dir_replica
                dir_source = sync_instance.dir_source
                full_path = os.path.normpath(key)
                message = (
                    f"copying {os.path.basename(key)} from: {os.path.join(dir_replica, os.path.relpath(full_path, dir_source))}"
                    f" to replica {os.path.join(dir_replica)}")
                print(message)
                log_to_file(log_file_path, message)
                if os.sep.join(full_path.split(os.sep)[-2:-1]) == os.path.basename(dir_source):
                    shutil.copy2(full_path, os.path.join(dir_replica, os.path.basename(key)))
                else:
                    if os.path.isdir(os.path.dirname(os.path.join(dir_replica, os.path.relpath(full_path, dir_source)))):
                        shutil.copy2(full_path, os.path.join(dir_replica, os.path.relpath(full_path, dir_source)))
                    else:
                        os.makedirs(os.path.dirname(os.path.join(dir_replica, os.path.relpath(full_path, dir_source))))
                        shutil.copy2(full_path, os.path.join(dir_replica, os.path.relpath(full_path, dir_source)))


            except Exception as e:
                current_datetime = datetime.datetime.now()
                message = f"{current_datetime}: encountered an error during copy {e}."
                print(message)
                log_to_file(log_file_path, message)

    def remove_excess(self):
        for key in self.keys():
            try:
                message = f"delete: {os.path.join(sync_instance.dir_replica, key)}"
                print(message)
                log_to_file(log_file_path, message)
                os.remove(os.path.join(sync_instance.dir_replica, key))
            except Exception as e:
                current_datetime = datetime.datetime.now()
                message = f"{current_datetime}: encountered an Error during removal from target folder: {e}."
                print(message)
                log_to_file(log_file_path, message)
        Sync.delete_empty_folders(sync_instance.dir_replica)
        log_to_file(log_file_path, "removing empty folders from target folder.")

    def delete_empty_folders(self):
        for dirpath, dirnames, filenames in os.walk(self, topdown=False):
            for dirname in dirnames:
                full_path = os.path.join(dirpath, dirname)
                if not os.listdir(full_path):
                    os.rmdir(full_path)


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


def path_validity_check(message):
    while True:
        data = input(f"{message}")
        if not os.path.isdir(data):
            print("Inputed folder doesn't exist")
            continue
        else:
            break
    return data


def interval_validity(message):
    while True:
        data = input(f"{message}")
        words = data.lower().split()
        if len(words) < 2 or (words[1] not in ('second', 'hour', 'seconds', 'hours')):
            print(f"{data} is not a valid input")
        else:
            break
    return data


if __name__ == "__main__":
    source_input = path_validity_check("Please enter path to source folder: ")
    target_input = path_validity_check("Please enter path to target folder: ")
    sync_instance = Sync(source_input, target_input)
    interval_input = interval_validity(
        "Enter the time interval in seconds, minutes, or hours (e.g., '30 seconds', '1 hour'): ")
    input_log = path_validity_check("Please enter logfile path: ") + "\\" + "sync.log"
    log_file_path = input_log

    # log_file_path = "C:\\Users\\GeeLord\\PycharmProjects\\veeam_task\\sync.log"
    # sync_instance = Sync("C:\\Users\\GeeLord\\Downloads\\ProcessMonitor", "C:\\Users\\GeeLord\\Downloads\\Nová složka")
    # interval_input = "2 seconds"

    create_log(input_log)


    def sync_job():
        # sync_instance = Sync("C:\\Users\\GeeLord\\Downloads\\ProcessMonitor",
        #                      "C:\\Users\\GeeLord\\Downloads\\Nová složka")
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
