#include "Drivetrain.h"

Drivetrain::Drivetrain()
    : _fl("Front Left",
          LEFT_FRONT_R_PWM, LEFT_FRONT_L_PWM, FRONT_LEFT_DEADBAND, NOT_REVERSED,
          LEFT_FRONT_TURN_R_DIGITAL, LEFT_FRONT_TURN_L_DIGITAL,
          LEFT_FRONT_POT),
      _fr("Front Right",
          RIGHT_FRONT_R_PWM, RIGHT_FRONT_L_PWM, FRONT_RIGHT_DEADBAND, NOT_REVERSED,
          RIGHT_FRONT_TURN_R_DIGITAL, RIGHT_FRONT_TURN_L_DIGITAL,
          RIGHT_FRONT_POT),
      _bl("Back Left",
          LEFT_BACK_R_PWM, LEFT_BACK_L_PWM, BACK_LEFT_DEADBAND, NOT_REVERSED,
          LEFT_BACK_TURN_R_DIGITAL, LEFT_BACK_TURN_L_DIGITAL,
          LEFT_BACK_POT),
      _br("Back Right",
          RIGHT_BACK_R_PWM, RIGHT_BACK_L_PWM, BACK_RIGHT_DEADBAND, REVERSED,
          RIGHT_BACK_TURN_R_DIGITAL, RIGHT_BACK_TURN_L_DIGITAL,
          RIGHT_BACK_POT),
      _mode(DRIVE_MODE_STRAIGHT),
      _driveEffort(0) {}

void Drivetrain::begin() {
    _fl.begin();
    _fr.begin();
    _bl.begin();
    _br.begin();
    applyTargetsForMode();
}

void Drivetrain::setMode(uint8_t mode) {
    if (mode != DRIVE_MODE_STRAIGHT && mode != DRIVE_MODE_ROTATE && mode != DRIVE_MODE_STRAFE) {
        return;
    }
    _mode = mode;
    applyTargetsForMode();
}

uint8_t Drivetrain::getMode() const {
    return _mode;
}

void Drivetrain::setDriveEffort(int8_t effort) {
    if (effort < EFFORT_MIN) effort = EFFORT_MIN;
    if (effort > EFFORT_MAX) effort = EFFORT_MAX;
    _driveEffort = effort;
}

int8_t Drivetrain::getDriveEffort() const {
    return _driveEffort;
}

void Drivetrain::update() {
    _fl.updateTurn();
    _fr.updateTurn();
    _bl.updateTurn();
    _br.updateTurn();

    applyDriveEfforts();
}

void Drivetrain::stop() {
    _fl.stop();
    _fr.stop();
    _bl.stop();
    _br.stop();
}

bool Drivetrain::allPodsAligned() const {
    return _fl.isAligned() && _fr.isAligned() && _bl.isAligned() && _br.isAligned();
}

bool Drivetrain::isFaultFrozen() const {
    return _fl.isFaultFrozen() || _fr.isFaultFrozen() || _bl.isFaultFrozen() || _br.isFaultFrozen();
}

uint8_t Drivetrain::readFL() { return _fl.readPot8bit(); }
uint8_t Drivetrain::readFR() { return _fr.readPot8bit(); }
uint8_t Drivetrain::readBL() { return _bl.readPot8bit(); }
uint8_t Drivetrain::readBR() { return _br.readPot8bit(); }

void Drivetrain::applyTargetsForMode() {
    switch (_mode) {
        case DRIVE_MODE_STRAIGHT:
            _fl.setTargetPot(FL_POT_STRAIGHT);
            _fr.setTargetPot(FR_POT_STRAIGHT);
            _bl.setTargetPot(BL_POT_STRAIGHT);
            _br.setTargetPot(BR_POT_STRAIGHT);
            break;
        case DRIVE_MODE_ROTATE:
            _fl.setTargetPot(FL_POT_ROTATE);
            _fr.setTargetPot(FR_POT_ROTATE);
            _bl.setTargetPot(BL_POT_ROTATE);
            _br.setTargetPot(BR_POT_ROTATE);
            break;
        case DRIVE_MODE_STRAFE:
            _fl.setTargetPot(FL_POT_STRAFE);
            _fr.setTargetPot(FR_POT_STRAFE);
            _bl.setTargetPot(BL_POT_STRAFE);
            _br.setTargetPot(BR_POT_STRAFE);
            break;
        default:
            break;
    }
}

void Drivetrain::applyDriveEfforts() {
    if (isFaultFrozen()) {
        stop();
        return;
    }

    // Gate drive until all pods aligned
    if (!allPodsAligned()) {
        _fl.setDriveEffort(0);
        _fr.setDriveEffort(0);
        _bl.setDriveEffort(0);
        _br.setDriveEffort(0);
        return;
    }

    int8_t base = _driveEffort;

    switch (_mode) {
        case DRIVE_MODE_STRAIGHT:
            _fl.setDriveEffort(base);
            _fr.setDriveEffort(base);
            _bl.setDriveEffort(base);
            _br.setDriveEffort(base);
            break;
        case DRIVE_MODE_ROTATE:
            // CCW positive: left side -, right side +
            _fl.setDriveEffort(-base);
            _bl.setDriveEffort(-base);
            _fr.setDriveEffort(base);
            _br.setDriveEffort(base);
            break;
        case DRIVE_MODE_STRAFE:
            // Left positive: FL -, FR +, BL +, BR -
            _fl.setDriveEffort(-base);
            _fr.setDriveEffort(base);
            _bl.setDriveEffort(base);
            _br.setDriveEffort(-base);
            break;
        default:
            _fl.setDriveEffort(0);
            _fr.setDriveEffort(0);
            _bl.setDriveEffort(0);
            _br.setDriveEffort(0);
            break;
    }
}


