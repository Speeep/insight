#pragma once
#include <Arduino.h>
#include "BTS7960MotorController.h"
#include "OnOffMotorController.h"
#include "RobotMap.h"

class WheelPod {
public:
    WheelPod(const char* name,
             uint8_t drive_r_pwm,
             uint8_t drive_l_pwm,
             uint8_t drive_deadband,
             bool drive_reverse,
             uint8_t turn_r_digital,
             uint8_t turn_l_digital,
             uint8_t pot_pin);

    void begin();

    void setTargetPot(uint8_t target);
    uint8_t getTargetPot() const;

    // Drive effort is -100..100. Drivetrain will decide sign per mode.
    void setDriveEffort(int8_t effort);

    // Update turning control (bang-bang with hysteresis & guards)
    void updateTurn();

    // Read current potentiometer (8-bit domain)
    uint8_t readPot8bit();

    // True if within stop tolerance of target
    bool isAligned() const;

    // Stop both turn and drive
    void stop();

    // Fault status (extreme readings freeze)
    bool isFaultFrozen() const;

private:
    const char* _name;
    BTS7960MotorController _drive;
    OnOffMotorController _turn;
    uint8_t _pot_pin;

    uint8_t _target_pot;
    uint8_t _last_pot;
    int _extreme_count;
    bool _fault_frozen;

    bool _aligned;
};


