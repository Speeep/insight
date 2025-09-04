#include <Arduino.h>
#include "Drivetrain.h"
#include "RobotMap.h"

Drivetrain drivetrain;

unsigned long last_packet_time = 0;

// Feedback pins and timing
const uint8_t right_front_pot = RIGHT_FRONT_POT;
const uint8_t right_back_pot = RIGHT_BACK_POT;
const uint8_t left_front_pot = LEFT_FRONT_POT;
const uint8_t left_back_pot = LEFT_BACK_POT;
unsigned long last_status_time = 0;
const unsigned long status_interval = STATUS_INTERVAL_MS;

void setup() {
    Serial.begin(115200);
    drivetrain.begin();
    Serial.println("GO");
    pinMode(52, OUTPUT);
    digitalWrite(52, HIGH);
}

void sendFeedback() {
    uint8_t pot1 = drivetrain.readFR();
    uint8_t pot2 = drivetrain.readBR();
    uint8_t pot3 = drivetrain.readFL();
    uint8_t pot4 = drivetrain.readBL();
    uint8_t checksum = pot1 ^ pot2 ^ pot3 ^ pot4;
    Serial.write(FEEDBACK_START_BYTE);
    Serial.write(pot1);
    Serial.write(pot2);
    Serial.write(pot3);
    Serial.write(pot4);
    Serial.write(checksum);
}

void loop() {
    static uint8_t packet[PACKET_LENGTH];
    static uint8_t idx = 0;
    static bool receiving = false;
    static unsigned long receive_start_time = 0;

    // Read serial data
    while (Serial.available()) {
        uint8_t b = Serial.read();
        unsigned long now = millis();
        if (!receiving) {
            if (b == PACKET_START_BYTE) {
                receiving = true;
                idx = 0;
                packet[idx++] = b;
                receive_start_time = now;
            }
        } else {
            packet[idx++] = b;
            // Timeout fallback: if packet not completed in SERIAL_RECEIVE_TIMEOUT_MS, reset
            if (now - receive_start_time > SERIAL_RECEIVE_TIMEOUT_MS) {
                receiving = false;
                idx = 0;
                continue;
            }
            if (idx == PACKET_LENGTH) {
                // New packet format: [0]=start, [1]=effort(int8), [2]=mode(uint8), [3]=reserved, [4]=checksum
                uint8_t checksum = packet[1] ^ packet[2] ^ packet[3];
                if (checksum == packet[4]) {
                    int8_t effort = (int8_t)packet[1];
                    uint8_t mode = packet[2];
                    if (effort < EFFORT_MIN) effort = EFFORT_MIN;
                    if (effort > EFFORT_MAX) effort = EFFORT_MAX;
                    drivetrain.setDriveEffort(effort);
                    drivetrain.setMode(mode);
                    last_packet_time = millis();
                }
                receiving = false;
                idx = 0;
            }
        }
    }

    drivetrain.update();

    // Send feedback at interval
    unsigned long now = millis();
    if (now - last_status_time >= status_interval) {
        sendFeedback();
        last_status_time = now;
    }

    // Watchdog: stop all motors if no packet received in timeout
    if (now - last_packet_time > WATCHDOG_TIMEOUT_MS) {
        drivetrain.stop();
    }
}