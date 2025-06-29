# Unified Controller eMMC Mount Verification

This repository validates the feasibility of deploying eMMC storage on a unified controller that combines the car head unit and TBox.

Although the eMMC is deployed under the car head unit, the Linux-based TBox must successfully mount it after each suspend and wake-up cycle. The TBox accesses the eMMC via internal Ethernet or other bus interfaces.

---

## 📌 Objective

To ensure that the eMMC can be reliably mounted and accessed by the TBox after every suspend and wake-up cycle, confirming the solution’s stability in a unified automotive controller architecture.

---

## 🧩 System Structure

- **Unified Controller**: Combines the head unit and TBox into a single domain controller.
- **eMMC Deployment**: Physically under the car head unit system.
- **TBox OS**: Linux-based system requiring access to eMMC after each power cycle.
- **Connection**: TBox accesses eMMC via internal Ethernet or bus.

---

## 🔁 Test Workflow

1. **Sleep/Wake Control via CAPL**
   - CAPL scripts send sleep and wake-up CAN messages.
   - These control the power states of the TBox and head unit.

2. **Mount Verification via Python**
   - After wake-up, a Python script uses ADB to connect to the TBox.
   - The script logs in with a username and password.
   - It checks a specific directory on the TBox Linux file system.
   - The presence of expected folders confirms eMMC is mounted successfully.

---

## 🛠 Scripts Overview

- `can_sleep_wake.capl`  
  CAPL script that sends CAN messages to trigger suspend and wake-up events.

- `emmc_mount_check.py`  
  Python script using ADB to log into the Linux system, validate login, and verify mount status.

---

## 🚀 How to Use

1. Connect the test bench (TBox + Head Unit + CAN + eMMC).
2. Run the CAPL script using CANoe or CANalyzer to trigger suspend/wake cycles.
3. After each wake-up:
   - Use ADB over USB/Ethernet to connect to the TBox.
   - Execute the Python script:
     ```bash
     python emmc_mount_check.py
     ```
4. The script will:
   - Authenticate to the Linux system
   - Check the presence of the target eMMC mount path
   - Output success/failure log for each cycle

---

## 📁 Folder Structure
📂 capl/
    └── sleep_wake_controller.can  # CAPL script for controlling suspend/wake cycles and triggering mount check
📂 python/
    └── adb_emmc_mount_check.py  # This script verifies whether the eMMC partition is correctly mounted after a Linux-based domain controller wakes up from sleep. Useful for automotive integration of TBox + Head Unit systems.

Note:

Real credentials and paths have been anonymized.

Replace "your_username" and "your_password" and paths with actual values securely.

Do not hardcode credentials in production environments.


