#include <Arduino.h>

#include "LedSensor.h"
#include "Pins.h"

void initializeLedSensor()
{
    pinMode(LED_SENSOR, INPUT);
}

bool isLedOn()
{
    // LM393 is active LOW.
    return digitalRead(LED_SENSOR) == LOW;
}
