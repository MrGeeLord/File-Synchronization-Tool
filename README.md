# File Synchronization Tool

This Python script is designed to synchronize files between a source directory and a replica directory at regular intervals. It uses the `apscheduler` library to schedule synchronization tasks and MD5 hashing to identify duplicates.

## Features

- Synchronize files from a source directory to a replica directory.
- Compare the contents of the source and replica directories to identify differences.
- Copy new files from the source to the replica. This script doesn't allow copies of a file  in same folder (file with same content but with a different filename will not be copied). 
- Remove excess files from the replica directory.
- Log synchronization actions with timestamps.

## Getting Started

To use this script, you need to have Python installed on your system.

1. Clone the repository to your local machine or download the script.

2. Install the required Python libraries using pip.

## Usage

1. Run the script using Python:

2. You will be prompted to provide the following information:

- Path to the source folder: Enter the directory path you want to synchronize.
- Path to the target (replica) folder: Enter the destination directory where files will be synchronized.
- Time interval: Specify the synchronization interval in seconds, minutes, or hours (e.g., '30 seconds', '1 hour').
- Log file path: Enter the path for the log file where synchronization actions will be recorded.

3. The script will start synchronizing files at the specified intervals.

## Customization

You can customize the script by modifying the following parameters in the `sync.py` file:

- `block_size`: Adjust the block size for reading files during hashing.
- Add any additional logic or customizations to the synchronization process within the `Sync` class methods.

## Logging

The script logs synchronization actions with timestamps. The log file is specified during setup and is located at the provided path. Actions such as copying files and removing excess files will be recorded in this log.
