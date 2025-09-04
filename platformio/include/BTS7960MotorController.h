#pragma once
#include <Arduino.h>

class BTS7960MotorController {
public:
    BTS7960MotorController(const char* name, uint8_t r_pwm, uint8_t l_pwm, uint8_t deadband, bool reverse);
    void begin();
    void setEffort(int8_t effort); // -100 to 100
    void stop();
    const char* getName() const;

private:
    const char* _name;
    uint8_t _r_pwm;
    uint8_t _l_pwm;
    int8_t _effort;
    uint8_t _deadband;
    bool _reverse;
};