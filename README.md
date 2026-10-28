# Merlin LED Counter

Counts LED activations (flashes) on the Merlin Wireless Gateway and
logs each one with a timestamp.

## How it works

- The LM393 LED sensor on pin 22 (`include/Pins.h`) reads the LED.
  Its output is active LOW.
- The firmware debounces the signal (`LED_DEBOUNCE_MS` in
  `include/Config.h`). Each OFF-to-ON change counts as one activation.
- For each activation it prints one line:
  `CSV_DATA,<count>,<device_ms>,<interval_ms>`
  - `device_ms` is milliseconds since the gateway's LED counter started.
  - `interval_ms` is the time since the previous activation (0 for the first).
- The PC logger (`device_csv_logger.py`) adds the PC timestamp and
  writes `logs/Merlin_LED_Log_<time>.csv`.

## CSV columns

| Column | Source |
| --- | --- |
| Timestamp | PC time when the row arrived |
| Count | Activation number since boot |
| Device_ms | Gateway time of the activation |
| Interval_ms | Time since the previous activation |

## Build and run

```bash
pio run
```

```bash
python device_csv_logger.py COM43
```

## Tuning

- If fast flashes are missed, lower `LED_DEBOUNCE_MS`.
- If noise causes extra counts, raise it.

## Not yet verified

The firmware compiles, but it has not been run against a Merlin
gateway. Check the first run against a known number of flashes.
