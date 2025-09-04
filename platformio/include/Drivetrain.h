#pragma once
#include <Arduino.h>
#include "WheelPod.h"
#include "RobotMap.h"

class Drivetrain {
public:
    Drivetrain();

    void begin();

    void setMode(uint8_t mode);
    uint8_t getMode() const;

    void setDriveEffort(int8_t effort);
    int8_t getDriveEffort() const;

    void update();
    void stop();

    // True if all pods within tolerance of targets
    bool allPodsAligned() const;

    // Fault freeze propagated from any pod
    bool isFaultFrozen() const;

    // Accessors for pot values (8-bit)
    uint8_t readFL();
    uint8_t readFR();
    uint8_t readBL();
    uint8_t readBR();

private:
    WheelPod _fl;
    WheelPod _fr;
    WheelPod _bl;
    WheelPod _br;

    uint8_t _mode; // DRIVE_MODE_*
    int8_t _driveEffort;

    void applyTargetsForMode();
    void applyDriveEfforts();
};


