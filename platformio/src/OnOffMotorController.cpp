#include "OnOffMotorController.h"
#include "RobotMap.h"

OnOffMotorController::OnOffMotorController(const char* name, uint8_t r_digital, uint8_t l_digital)
    : _name(name), _r_digital(r_digital), _l_digital(l_digital), _effort(0) {}

void OnOffMotorController::begin() {
    pinMode(_r_digital, OUTPUT);
    pinMode(_l_digital, OUTPUT);
    digitalWrite(_r_digital, LOW);
    digitalWrite(_l_digital, LOW);
}

void OnOffMotorController::setEffort(int8_t effort) {
    _effort = (effort > 0) ? 1 : (effort < 0 ? -1 : 0);
    if (_effort > 0) {
        digitalWrite(_r_digital, HIGH);
        digitalWrite(_l_digital, LOW);
    } else if (_effort < 0) {
        digitalWrite(_r_digital, LOW);
        digitalWrite(_l_digital, HIGH);
    } else {
        digitalWrite(_r_digital, LOW);
        digitalWrite(_l_digital, LOW);
    }
}

void OnOffMotorController::stop() {
    digitalWrite(_r_digital, LOW);
    digitalWrite(_l_digital, LOW);
}

const char* OnOffMotorController::getName() const {
    return _name;
}