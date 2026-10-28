#pragma once

// Call repeatedly from loop(). Never blocks.
// Each debounced OFF-to-ON transition is one activation (flash).
void updateLedCounter();

// Activations counted since boot.
unsigned long getLedCount();
