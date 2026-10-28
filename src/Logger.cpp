#include <Arduino.h>

#include "Logger.h"

void logMessage(const char* message)
{
    Serial.println(message);
}

void printBanner()
{
    Serial.println();
    Serial.println("===============================");
    Serial.println(" Merlin LED Counter");
    Serial.println("===============================");
}