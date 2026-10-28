#include <Arduino.h>

#include "LedCounter.h"
#include "LedSensor.h"
#include "Config.h"

static unsigned long ledCount = 0;
static unsigned long lastActivationMs = 0;

static bool confirmedOn = false;
static bool candidateOn = false;
static unsigned long candidateStartMs = 0;

void updateLedCounter()
{
    bool sensed = isLedOn();
    unsigned long nowMs = millis();

    // Restart the debounce timer whenever the reading changes.
    if (sensed != candidateOn)
    {
        candidateOn = sensed;
        candidateStartMs = nowMs;
    }

    // Accept the new state once it has held for LED_DEBOUNCE_MS.
    if ((candidateOn != confirmedOn) &&
        (nowMs - candidateStartMs >= LED_DEBOUNCE_MS))
    {
        confirmedOn = candidateOn;

        if (confirmedOn)
        {
            ledCount++;

            // Time since the previous activation. Zero for the first.
            unsigned long intervalMs = 0;

            if (ledCount > 1)
            {
                intervalMs = nowMs - lastActivationMs;
            }

            lastActivationMs = nowMs;

            // CSV_DATA lines are saved by the PC logger.
            Serial.print("CSV_DATA,");
            Serial.print(ledCount);
            Serial.print(",");
            Serial.print(nowMs);
            Serial.print(",");
            Serial.println(intervalMs);
        }
    }
}

unsigned long getLedCount()
{
    return ledCount;
}
