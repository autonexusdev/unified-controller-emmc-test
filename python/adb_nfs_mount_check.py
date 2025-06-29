#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
eMMC Mount Check Script for Unified Controller (TBox + Head Unit)

Python Version Requirement: 3.10 or above

This script is designed to verify whether the eMMC storage has been correctly
mounted in a unified automotive domain controller (combining TBox and head unit)
after each suspend/wake-up cycle.

The script connects to the controller's Linux system via ADB, performs login,
and checks the status of a specific mount path (e.g., /mnt/emmc_mount) using several
Linux commands. Log outputs are saved to a local file for traceability.

Usage:
  - Make sure the device is connected via ADB.
  - Configure login credentials if needed.
  - Run the script after the system wakes up from a sleep cycle.
"""

import subprocess
import sys
import time
import os
import re
from datetime import datetime

# =============================================================================
# Purpose:
#   This script is designed to verify whether the eMMC storage has been correctly
#   mounted in a unified automotive domain controller (combining TBox and head unit)
#   after each suspend/wake-up cycle.
#
#   The script connects to the controller's Linux system via ADB, performs login,
#   and checks the status of a specific mount path (e.g., /mnt/emmc_mount) using several
#   Linux commands. Log outputs are saved to a local file for traceability.
#
# Usage:
#   - Make sure the device is connected via ADB.
#   - Configure login credentials if needed.
#   - Run the script after the system wakes up from a sleep cycle.
# =============================================================================

# Global log file path
LOG_FILE = "emmc_mount_check.log"

# -----------------------------------------------------------------------------
# Function: save_to_log
# Purpose : Append content to the specified log file with separator lines.
# Arguments:
#   content (str): The log content to append.
# -----------------------------------------------------------------------------
def save_to_log(content):
    """Append content to the log file, with separator lines"""
    with open(LOG_FILE, 'a') as f:
        f.write(content)
        f.write("\n" + "=" * 80 + "\n")

# -----------------------------------------------------------------------------
# Function: adb_shell_login
# Purpose : Connects to the controller via ADB shell, handles login prompts,
#           and executes a set of mount-checking commands. It parses output
#           to determine whether the mount path (e.g., /mnt/emmc_mount) is NFS-mounted.
#           The results are saved to log and printed on-screen.
# -----------------------------------------------------------------------------
def adb_shell_login():
    # Start an adb shell subprocess
    process = subprocess.Popen(
        ['adb', 'shell'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # line-buffered
        universal_newlines=True
    )

    # Define prompt strings
    login_prompt = "login:"
    password_prompt = "Password:"

    # Dummy credentials for demonstration (do NOT hardcode real credentials)
    username = "your_username"
    password = "your_password"

    success_prompt = "#"  # Expected shell prompt after successful login

    login_complete = False
    timeout = 3  # Maximum login wait time (in seconds)
    start_time = time.time()

    # Variables to capture results
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    login_status = "Failed"
    mount_result = ""
    command_output = ""

    try:
        buffer = ''
        while not login_complete and (time.time() - start_time) < timeout:
            # Check if subprocess ended
            if process.poll() is not None:
                break

            # Read one character at a time (non-blocking)
            char = process.stdout.read(1)
            if not char:
                time.sleep(0.1)
                continue

            sys.stdout.write(char)  # Real-time print
            sys.stdout.flush()
            buffer += char

            # Respond to login prompt
            if login_prompt in buffer:
                process.stdin.write(username + '\n')
                process.stdin.flush()
                buffer = buffer.replace(login_prompt, '')

            elif password_prompt in buffer:
                process.stdin.write(password + '\n')
                process.stdin.flush()
                buffer = buffer.replace(password_prompt, '')

            # If login is successful, run mount check commands
            if success_prompt in buffer:
                login_complete = True
                login_status = "Success"
                print("\nLogin successful. Checking mount status of /mnt/emmc_mount...")

                # Linux shell commands to check if mount path is mounted
                commands = [
                    "df -h | grep emmc_mount  || echo '/mnt/emmc_mount not found'",
                    "mount | grep emmc_mount || echo '/mnt/emmc_mount not mounted'",
                    "cat /proc/mounts | grep emmc_mount || true"
                ]

                all_output = ""
                for cmd in commands:
                    process.stdin.write(cmd + '\n')
                    process.stdin.flush()

                    # Capture each command’s output with timeout
                    cmd_output = ""
                    cmd_start = time.time()

                    while (time.time() - cmd_start) < 3:
                        char = process.stdout.read(1)
                        if not char:
                            time.sleep(0.1)
                            continue

                        sys.stdout.write(char)
                        sys.stdout.flush()
                        cmd_output += char

                        if "#" in cmd_output:
                            break

                    all_output += f"Command: {cmd}\nOutput:\n{cmd_output}\n\n"

                command_output = all_output.strip()

                # Analyze whether NFS is detected in the mount information
                nfs_patterns = [
                    r"\bnfs\b",
                    r"\bnfs4\b",
                    r":[0-9]+/"
                ]

                for pattern in nfs_patterns:
                    if re.search(pattern, command_output, re.IGNORECASE):
                        mount_result = "Yes"
                        break
                else:
                    if "emmc_mount" in command_output:
                        mount_result = "No"
                    else:
                        mount_result = "Unknown (/mnt/emmc_mount not found)"

                break  # Exit main loop after execution

            # Limit buffer size to keep memory usage low
            if len(buffer) > 100:
                buffer = buffer[-50:]

    except Exception as e:
        print(f"\nException occurred: {str(e)}")
        mount_result = f"Error: {str(e)}"

    finally:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)

        # Format and save log
        log_content = (
            f"[Check Time] {timestamp}\n"
            f"[Login Status] {login_status}\n"
            f"[NFS Mounted] {mount_result}\n\n"
            f"[Command Output]\n{command_output}\n"
        )

        save_to_log(log_content)
        print(f"\nCheck complete! Results saved to: {LOG_FILE}")

        # Display summary
        print("\n" + "=" * 40)
        print(f"Time: {timestamp}")
        print(f"Login: {login_status}")
        print(f"NFS Mounted: {mount_result}")
        print("=" * 40)

        # Clean up process
        if process.stdin:
            process.stdin.close()
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=1)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    process.kill()
                except:
                    pass

# -----------------------------------------------------------------------------
# Entry point of the script.
# Checks if log file exists; creates it with a header if it doesn't.
# Then starts the ADB login and mount check procedure.
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.write("eMMC Mount Check Log\n")
            f.write("=" * 80 + "\n")

    adb_shell_login()
    sys.exit()
