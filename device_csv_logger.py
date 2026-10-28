import csv
import os
import sys
import time
from datetime import datetime

import serial
import serial.tools.list_ports


BAUD_RATE = 115200

# Lines from the device that start with these prefixes are used.
HEADER_PREFIX = "CSV_HEADER,"
DATA_PREFIX = "CSV_DATA,"

# Name used for the log folder and CSV file names.
LOG_NAME = "Merlin_LED_Log"

# A flash that comes more than this long after the previous one starts
# a new burst. One burst is one timer click / transmission.
# In the test data, flashes inside a burst were at most 1103 ms apart,
# and bursts were about 8-10 s apart, so 3000 ms separates them cleanly.
BURST_GAP_MS = 3000

# Columns written to the CSV file, in order.
OUTPUT_COLUMNS = [
    "Timestamp",
    "Elapsed_s",
    "Burst",
    "Flash_In_Burst",
    "Count",
    "Device_ms",
    "Gap_ms",
]


def format_timestamp(moment):
    # Whole seconds, as the logger wrote before. Example: 2026-10-28 09:40:12
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def find_device_port(requested_port=None):
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        return None

    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")

    print()

    # A port given on the command line always wins.
    if requested_port:
        print(f"Using requested port: {requested_port}")
        return requested_port

    candidates = []

    for port in ports:
        description = port.description.lower()

        if (
            "pico" in description
            or "usb serial" in description
            or "serial device" in description
        ):
            candidates.append(port.device)

    if len(candidates) == 1:
        print(f"Automatically selected: {candidates[0]}")
        return candidates[0]

    # More than one match: guessing can pick the wrong device.
    if len(candidates) > 1:
        print(
            "More than one possible port was found: "
            + ", ".join(candidates)
        )

    port_name = input(
        "Enter the device COM port (example COM43): "
    ).strip()

    return port_name


def create_log_file():
    now = datetime.now()

    log_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "logs",
    )

    os.makedirs(log_folder, exist_ok=True)

    filename = f"{LOG_NAME}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    return os.path.join(log_folder, filename)


class FlashTracker:
    """Adds burst and timing columns to each flash from the device."""

    def __init__(self):
        self.first_ms = None
        self.prev_ms = None
        self.burst_number = 0
        self.flash_in_burst = 0
        self.bursts = []

    def add_flash(self, device_count, device_ms, timestamp):
        if self.first_ms is None:
            self.first_ms = device_ms

        gap_ms = None if self.prev_ms is None else device_ms - self.prev_ms

        starts_new_burst = gap_ms is None or gap_ms > BURST_GAP_MS

        if starts_new_burst:
            gap_before_burst = None

            if self.bursts:
                gap_before_burst = device_ms - self.bursts[-1]["last_ms"]

            self.burst_number += 1
            self.flash_in_burst = 1

            self.bursts.append({
                "number": self.burst_number,
                "start_timestamp": timestamp,
                "first_ms": device_ms,
                "last_ms": device_ms,
                "flashes": 1,
                "gap_before_ms": gap_before_burst,
            })
        else:
            self.flash_in_burst += 1

            self.bursts[-1]["last_ms"] = device_ms
            self.bursts[-1]["flashes"] += 1

        self.prev_ms = device_ms

        elapsed_s = (device_ms - self.first_ms) / 1000

        return [
            timestamp,
            f"{elapsed_s:.3f}",
            self.burst_number,
            self.flash_in_burst,
            device_count,
            device_ms,
            "" if gap_ms is None else gap_ms,
        ]

    def total_flashes(self):
        return sum(burst["flashes"] for burst in self.bursts)

    def summary_lines(self):
        lines = [
            "Merlin LED Count Summary",
            "=" * 72,
            f"Total flashes : {self.total_flashes()}",
            f"Bursts        : {len(self.bursts)}",
            f"Burst rule    : a flash more than {BURST_GAP_MS} ms after "
            "the previous one starts a new burst",
            "",
        ]

        if not self.bursts:
            lines.append("No flashes were received.")
            return lines

        lines.append(
            f"{'Burst':>5}  {'Start time':<24}{'Flashes':>8}"
            f"{'Burst length':>15}{'Gap before':>13}"
        )
        lines.append("-" * 72)

        for burst in self.bursts:
            length_ms = burst["last_ms"] - burst["first_ms"]

            if burst["gap_before_ms"] is None:
                gap_text = "-"
            else:
                gap_text = f"{burst['gap_before_ms']} ms"

            lines.append(
                f"{burst['number']:>5}  "
                f"{burst['start_timestamp']:<24}"
                f"{burst['flashes']:>8}"
                f"{length_ms:>12} ms"
                f"{gap_text:>13}"
            )

        return lines


def print_and_save_summary(filepath, tracker):
    summary_path = os.path.splitext(filepath)[0] + "_summary.txt"

    lines = tracker.summary_lines()

    print()
    for line in lines:
        print(line)

    with open(summary_path, mode="w", encoding="utf-8") as summary_file:
        summary_file.write("\n".join(lines) + "\n")

    print()
    print("Summary saved:")
    print(summary_path)


def main():
    print()
    print("===================================")
    print(" Merlin LED Counter Logger")
    print("===================================")
    print()

    # Optional: python device_csv_logger.py COM9
    requested_port = sys.argv[1] if len(sys.argv) > 1 else None

    port = find_device_port(requested_port)

    if not port:
        print("No serial port found.")
        sys.exit(1)

    filepath = create_log_file()

    print()
    print(f"Connecting to {port} at {BAUD_RATE} baud...")
    print(f"CSV log: {filepath}")
    print()

    try:
        ser = serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            timeout=1,
        )
    except serial.SerialException as error:
        print(f"Could not open {port}:")
        print(error)
        sys.exit(1)

    time.sleep(2)

    # The columns are fixed, so the file is created right away. The
    # Pico only prints its header once at power-up, so waiting for it
    # fails if the logger starts after the Pico has booted.
    csv_file = open(
        filepath,
        mode="w",
        newline="",
        encoding="utf-8",
    )

    writer = csv.writer(csv_file)
    writer.writerow(OUTPUT_COLUMNS)
    csv_file.flush()

    tracker = FlashTracker()

    print("Logger running.")
    print("Press CTRL+C to stop.")
    print()
    print("-----------------------------------")

    try:
        while True:
            raw_line = ser.readline()

            if not raw_line:
                continue

            line = raw_line.decode(
                "utf-8",
                errors="replace",
            ).strip()

            if not line:
                continue

            print(line)

            if line.startswith(DATA_PREFIX):
                # Device sends: Count,Device_ms,Interval_ms
                fields = line[len(DATA_PREFIX):].split(",")

                try:
                    device_count = int(fields[0])
                    device_ms = int(fields[1])
                except (IndexError, ValueError):
                    print("[CSV WARNING] Unexpected CSV_DATA format:")
                    print(line)
                    continue

                timestamp = format_timestamp(datetime.now())

                row = tracker.add_flash(device_count, device_ms, timestamp)

                writer.writerow(row)
                csv_file.flush()

                burst = tracker.burst_number
                flash_in_burst = tracker.flash_in_burst

                print(
                    f"[CSV SAVED] {timestamp}  "
                    f"Burst {burst}  "
                    f"Flash {flash_in_burst}  "
                    f"Count {device_count}"
                )

    except KeyboardInterrupt:
        print()
        print("-----------------------------------")
        print("Logger stopped by user.")

    finally:
        ser.close()
        csv_file.close()

    print()
    print("CSV file saved:")
    print(filepath)

    print_and_save_summary(filepath, tracker)


if __name__ == "__main__":
    main()
