#pragma once

// Time the LED must hold a new state before the change is accepted.
// Rejects electrical noise. Lower this if fast flashes are missed.
const unsigned long LED_DEBOUNCE_MS = 5;
