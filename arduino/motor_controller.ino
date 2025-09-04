#define NUM_MOTORS 7
#define WATCHDOG_TIMEOUT_MS 500  // Stop motors if no packet received within this time

// PWM output pins for each motor
const uint8_t r_pwm_pins[NUM_MOTORS] = {2, 4, 6, 8, 10, 12, 44};  // Forward
const uint8_t l_pwm_pins[NUM_MOTORS] = {3, 5, 7, 9, 11, 13, 45};  // Reverse

int8_t efforts[NUM_MOTORS] = {0};        // Last received effort values
unsigned long last_packet_time = 0;      // Timestamp of last valid packet

// Feedback pins and timing
const uint8_t pot1_pin = A3;
const uint8_t pot2_pin = A4;
const uint8_t digital_input_pin = 22;
unsigned long last_status_time = 0;
const unsigned long status_interval = 50;  // Send status every 50 ms

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_MOTORS; i++) {
    pinMode(r_pwm_pins[i], OUTPUT);
    pinMode(l_pwm_pins[i], OUTPUT);
    analogWrite(r_pwm_pins[i], 0);
    analogWrite(l_pwm_pins[i], 0);
  }

  pinMode(pot1_pin, INPUT);
  pinMode(pot2_pin, INPUT);
  pinMode(digital_input_pin, INPUT);

  last_packet_time = millis();
  last_status_time = millis();

  Serial.println("GO");  // Signal host that Arduino is ready
}

void loop() {
  // Check for complete packet
  if (Serial.available() >= 17) {
    if (Serial.read() != 0xAA) return;

    for (int i = 0; i < NUM_MOTORS; i++) {
      efforts[i] = Serial.read();  // int8_t values: -100 to +100
    }

    Serial.read();  // Reserved byte (ignore for now)
    uint8_t received_checksum = Serial.read();

    // Validate checksum
    uint8_t calc_checksum = 0;
    for (int i = 0; i < NUM_MOTORS; i++) {
      calc_checksum ^= efforts[i];
    }
    calc_checksum ^= 0x00;  // Reserved byte is always 0

    if (calc_checksum != received_checksum) return;  // Invalid packet

    // Apply efforts and reset watchdog
    applyEfforts();
    last_packet_time = millis();
  }

  // Check for watchdog timeout
  if (millis() - last_packet_time > WATCHDOG_TIMEOUT_MS) {
    stopAllMotors();
    last_packet_time = millis();  // Avoid repeat stopping
  }

  // Send feedback status every 50 ms
  if (millis() - last_status_time >= status_interval) {
    uint16_t pot1_raw = analogRead(pot1_pin);
    uint16_t pot2_raw = analogRead(pot2_pin);
    uint8_t pot1_scaled = map(pot1_raw, 0, 1023, 0, 255);
    uint8_t pot2_scaled = map(pot2_raw, 0, 1023, 0, 255);
    uint8_t digital_state = digitalRead(digital_input_pin);
    uint8_t checksum = pot1_scaled ^ pot2_scaled ^ digital_state;

    Serial.write(0xBB);
    Serial.write(pot1_scaled);
    Serial.write(pot2_scaled);
    Serial.write(digital_state);
    Serial.write(checksum);

    last_status_time = millis();
  }
}

void applyEfforts() {
  for (int i = 0; i < NUM_MOTORS; i++) {
    int effort = efforts[i];
    int pwm = map(abs(effort), 0, 100, 0, 255);

    if (effort > 0) {
      analogWrite(r_pwm_pins[i], pwm);
      analogWrite(l_pwm_pins[i], 0);
    } else if (effort < 0) {
      analogWrite(r_pwm_pins[i], 0);
      analogWrite(l_pwm_pins[i], pwm);
    } else {
      analogWrite(r_pwm_pins[i], 0);
      analogWrite(l_pwm_pins[i], 0);
    }
  }
}

void stopAllMotors() {
  for (int i = 0; i < NUM_MOTORS; i++) {
    analogWrite(r_pwm_pins[i], 0);
    analogWrite(l_pwm_pins[i], 0);
  }
}
