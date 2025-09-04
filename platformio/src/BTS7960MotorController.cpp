#include "BTS7960MotorController.h"
#include "RobotMap.h"

BTS7960MotorController::BTS7960MotorController(const char* name, uint8_t r_pwm, uint8_t l_pwm, uint8_t deadband, bool reverse)
    : _name(name), _r_pwm(r_pwm), _l_pwm(l_pwm), _effort(0), _deadband(deadband), _reverse(reverse) {}

void BTS7960MotorController::begin() {
    pinMode(_r_pwm, OUTPUT);
    pinMode(_l_pwm, OUTPUT);
    analogWrite(_r_pwm, PWM_MIN);
    analogWrite(_l_pwm, PWM_MIN);
}

void BTS7960MotorController::setEffort(int8_t effort) {
    _effort = constrain(effort, EFFORT_MIN, EFFORT_MAX);
    int pwm = PWM_MIN;
    int actualEffort = _reverse ? -_effort : _effort;
    if (actualEffort == 0) {
        pwm = PWM_MIN;
    } else if (actualEffort > 0) {
        pwm = map(actualEffort, 1, EFFORT_MAX, _deadband, PWM_MAX);
    } else if (actualEffort < 0) {
        pwm = map(-actualEffort, 1, EFFORT_MAX, _deadband, PWM_MAX);
    }
    if (actualEffort > 0) {
        analogWrite(_r_pwm, pwm);
        analogWrite(_l_pwm, PWM_MIN);
    } else if (actualEffort < 0) {
        analogWrite(_r_pwm, PWM_MIN);
        analogWrite(_l_pwm, pwm);
    } else {
        analogWrite(_r_pwm, PWM_MIN);
        analogWrite(_l_pwm, PWM_MIN);
    }
}

void BTS7960MotorController::stop() {
    analogWrite(_r_pwm, PWM_MIN);
    analogWrite(_l_pwm, PWM_MIN);
}

const char* BTS7960MotorController::getName() const {
    return _name;
}