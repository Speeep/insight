#include "WheelPod.h"

WheelPod::WheelPod(const char* name,
                   uint8_t drive_r_pwm,
                   uint8_t drive_l_pwm,
                   uint8_t drive_deadband,
                   bool drive_reverse,
                   uint8_t turn_r_digital,
                   uint8_t turn_l_digital,
                   uint8_t pot_pin)
    : _name(name),
      _drive(name, drive_r_pwm, drive_l_pwm, drive_deadband, drive_reverse),
      _turn(name, turn_r_digital, turn_l_digital),
      _pot_pin(pot_pin),
      _target_pot(127),
      _last_pot(127),
      _extreme_count(0),
      _fault_frozen(false),
      _aligned(false) {}

void WheelPod::begin() {
    _drive.begin();
    _turn.begin();
}

void WheelPod::setTargetPot(uint8_t target) {
    _target_pot = target;
}

uint8_t WheelPod::getTargetPot() const {
    return _target_pot;
}

void WheelPod::setDriveEffort(int8_t effort) {
    if (_fault_frozen) {
        _drive.stop();
        return;
    }
    _drive.setEffort(effort);
}

uint8_t WheelPod::readPot8bit() {
    int raw10 = analogRead(_pot_pin);
    uint8_t value8 = (uint8_t)(raw10 >> 2);
    _last_pot = value8;

    // Fault detection: exact extremes
    if (value8 == POT_FAULT_EXTREME_LOW || value8 == POT_FAULT_EXTREME_HIGH) {
        _extreme_count++;
        if (_extreme_count >= POT_FAULT_CONSECUTIVE_SAMPLES) {
            _fault_frozen = true;
        }
    } else {
        _extreme_count = 0;
    }
    return value8;
}

bool WheelPod::isAligned() const {
    return _aligned;
}

void WheelPod::updateTurn() {
    if (_fault_frozen) {
        _turn.stop();
        _aligned = false;
        return;
    }

    uint8_t current = readPot8bit();
    int error = (int)_target_pot - (int)current;
    int absError = error >= 0 ? error : -error;

    // Hysteresis: stop inside STOP, re-engage outside REENGAGE
    if (_aligned) {
        if (absError <= POT_TOLERANCE_REENGAGE) {
            // remain stopped until error grows beyond reengage
            _turn.stop();
            return;
        }
        // else fall through to re-engage
    } else {
        if (absError <= POT_TOLERANCE_STOP) {
            _turn.stop();
            _aligned = true;
            return;
        }
    }

    _aligned = false;

    // Edge guards: prevent moving further toward extremes
    if ((current <= POT_EDGE_GUARD && error < 0) ||
        (current >= (uint8_t)(255 - POT_EDGE_GUARD) && error > 0)) {
        _turn.stop();
        return;
    }

    // Command direction: positive turn effort should increase pot value
    int8_t turnEffort = (error > 0) ? 1 : -1;
    _turn.setEffort(turnEffort);
}

void WheelPod::stop() {
    _drive.stop();
    _turn.stop();
}

bool WheelPod::isFaultFrozen() const {
    return _fault_frozen;
}


