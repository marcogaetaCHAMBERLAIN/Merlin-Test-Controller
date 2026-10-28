#include <Arduino.h>

#include "Logger.h"
#include "LedSensor.h"
#include "LedCounter.h"

void setup()
{
    Serial.begin(115200);

    while (!Serial)
    {
        delay(10);
    }

    initializeLedSensor();

    printBanner();

    // Tells the PC logger which columns to write.
    Serial.println("CSV_HEADER,Count,Device_ms,Interval_ms");
}

void loop()
{
    updateLedCounter();
}
