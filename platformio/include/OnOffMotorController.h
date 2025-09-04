#pragma once
#include <Arduino.h>

class OnOffMotorController {
public:
    OnOffMotorController(const char* name, uint8_t r_digital, uint8_t l_digital);
    void begin();
    void setEffort(int8_t effort); // -1, 0, 1
    void stop();
    const char* getName() const;

private:
    const char* _name;
    uint8_t _r_digital;
    uint8_t _l_digital;
    int8_t _effort;
};