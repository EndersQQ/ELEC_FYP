#include <Arduino.h>
#include <Preferences.h>

/*
  RF-PUL9Z-V1 9-zone FSR array + IMU-ready gripper sensor node for ESP32-S3.

  Sensor connector from the datasheet:
    C 1 2 3 4 5 6 7 8 9

  External resistor wiring for each sensing point:
    3.3V -> 2k resistor -> ADC pin -> FSR point N -> sensor C -> GND

  The GPIO/ADC pin is the shared point between the 2k resistor and the FSR.

  Serial protocol:
    STATUS,<state>[,<detail>...]
    FRAME,<schema>,<seq>,<ms>,<dt_ms>,<connected>,<raw1>,<pct1>...<raw9>,<pct9>,
          <imu_status>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<temp_c>

  IMU status:
    0 = not configured / not available
    1 = valid sample

  The IMU fields are intentionally part of the stable frame now, even before a
  specific IMU driver is selected. Add the real driver inside readImuSample().
*/

struct SensorPoint {
  uint8_t sensorNumber;
  uint8_t pin;
  const char *label;
};

struct ImuSample {
  bool available;
  float accelX;
  float accelY;
  float accelZ;
  float gyroX;
  float gyroY;
  float gyroZ;
  float tempC;
};

constexpr uint8_t FRAME_SCHEMA_VERSION = 1;
constexpr uint32_t CALIBRATION_MAGIC = 0x46535239;  // "FSR9"
constexpr uint8_t CALIBRATION_VERSION = 1;
constexpr float VCC = 3.3F;
constexpr uint16_t ADC_MAX = 4095;
constexpr uint8_t MEDIAN_SAMPLES_PER_POINT = 7;
constexpr uint16_t IDLE_CALIBRATION_SAMPLES = 180;
constexpr uint32_t MAX_CALIBRATION_MS = 7000;
constexpr uint32_t PRINT_INTERVAL_MS = 30;
constexpr uint16_t MIN_DEADBAND = 45;
constexpr uint16_t MIN_VALID_RANGE = 180;
constexpr uint8_t ADC_DISCARD_READS = 5;
constexpr uint16_t ADC_SETTLE_US = 1000;
constexpr uint16_t ADC_SAMPLE_GAP_US = 500;
constexpr uint8_t CONNECTED_SENSOR_COUNT = 9;

// Grid labels from the datasheet drawing:
//   3 6 9
//   2 5 8
//   1 4 7
SensorPoint SENSOR_PINS[9] = {
    {1, 1, "bottom-left "},
    {2, 2, "middle-left "},
    {3, 3, "top-left    "},
    {4, 4, "bottom-mid  "},
    {5, 5, "center      "},
    {6, 6, "top-mid     "},
    {7, 7, "bottom-right"},
    {8, 8, "middle-right"},
    {9, 9, "top-right   "},
};

Preferences preferences;
uint16_t idleRawBySensor[10] = {};
uint16_t maxPressRawBySensor[10] = {};
uint16_t smoothedRawBySensor[10] = {};
uint16_t deadbandBySensor[10] = {};
uint8_t displayPercentBySensor[10] = {};
String commandBuffer;
uint32_t frameSequence = 0;

void readSerialCommands();

uint8_t connectedSensorCount() {
  return min<uint8_t>(CONNECTED_SENSOR_COUNT, 9);
}

bool isSensorConnected(uint8_t sensorNumber) {
  return sensorNumber >= 1 && sensorNumber <= connectedSensorCount();
}

void sortSamples(uint16_t *samples, uint16_t count) {
  for (uint16_t i = 1; i < count; ++i) {
    const uint16_t value = samples[i];
    int16_t j = i - 1;
    while (j >= 0 && samples[j] > value) {
      samples[j + 1] = samples[j];
      --j;
    }
    samples[j + 1] = value;
  }
}

uint16_t readMedianRaw(uint8_t pin) {
  uint16_t samples[MEDIAN_SAMPLES_PER_POINT] = {};

  for (uint8_t i = 0; i < ADC_DISCARD_READS; ++i) {
    analogRead(pin);
    delayMicroseconds(ADC_SETTLE_US);
  }

  for (uint8_t i = 0; i < MEDIAN_SAMPLES_PER_POINT; ++i) {
    samples[i] = analogRead(pin);
    delayMicroseconds(ADC_SAMPLE_GAP_US);
  }

  sortSamples(samples, MEDIAN_SAMPLES_PER_POINT);
  return samples[MEDIAN_SAMPLES_PER_POINT / 2];
}

void readAllSensors(uint16_t rawBySensor[10]) {
  for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
    const SensorPoint &sensor = SENSOR_PINS[i];
    const uint16_t raw = readMedianRaw(sensor.pin);

    if (smoothedRawBySensor[sensor.sensorNumber] == 0) {
      smoothedRawBySensor[sensor.sensorNumber] = raw;
    } else {
      smoothedRawBySensor[sensor.sensorNumber] =
          ((smoothedRawBySensor[sensor.sensorNumber] * 7U) + raw + 4U) / 8U;
    }

    rawBySensor[sensor.sensorNumber] = smoothedRawBySensor[sensor.sensorNumber];
  }
}

uint8_t pressToPercent(uint8_t sensorNumber, uint16_t raw) {
  const uint16_t idleRaw = idleRawBySensor[sensorNumber];
  const uint16_t maxPressRaw = maxPressRawBySensor[sensorNumber];
  const uint16_t deadband = deadbandBySensor[sensorNumber];

  if (idleRaw <= maxPressRaw + MIN_VALID_RANGE || raw + deadband >= idleRaw) {
    return 0;
  }

  const uint16_t activeRange = idleRaw - maxPressRaw - deadband;
  const uint16_t press = idleRaw - raw - deadband;
  const uint32_t percent = (static_cast<uint32_t>(press) * 100U) / activeRange;
  return min<uint32_t>(percent, 100U);
}

uint8_t smoothPercent(uint8_t sensorNumber, uint8_t targetPercent) {
  uint8_t &displayPercent = displayPercentBySensor[sensorNumber];

  if (targetPercent < 3) {
    targetPercent = 0;
  }

  if (targetPercent > displayPercent) {
    displayPercent += max<uint8_t>(1, (targetPercent - displayPercent + 1) / 2);
  } else if (targetPercent < displayPercent) {
    displayPercent -= max<uint8_t>(1, (displayPercent - targetPercent + 3) / 4);
  }

  if (displayPercent < 3) {
    displayPercent = 0;
  }

  return displayPercent;
}

uint16_t updateTemporarySmooth(uint16_t previous, uint16_t raw) {
  if (previous == 0) {
    return raw;
  }
  return ((previous * 7U) + raw + 4U) / 8U;
}

String sensorKey(const char *prefix, uint8_t sensorNumber) {
  char key[8];
  snprintf(key, sizeof(key), "%s%u", prefix, sensorNumber);
  return String(key);
}

void saveCalibration() {
  preferences.putUInt("magic", CALIBRATION_MAGIC);
  preferences.putUChar("version", CALIBRATION_VERSION);
  preferences.putUChar("count", connectedSensorCount());

  for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
    const SensorPoint &sensor = SENSOR_PINS[i];
    preferences.putUShort(sensorKey("i", sensor.sensorNumber).c_str(), idleRawBySensor[sensor.sensorNumber]);
    preferences.putUShort(sensorKey("m", sensor.sensorNumber).c_str(), maxPressRawBySensor[sensor.sensorNumber]);
    preferences.putUShort(sensorKey("d", sensor.sensorNumber).c_str(), deadbandBySensor[sensor.sensorNumber]);
  }

  Serial.println("STATUS,calibration_saved");
}

bool loadCalibration() {
  if (preferences.getUInt("magic", 0) != CALIBRATION_MAGIC ||
      preferences.getUChar("version", 0) != CALIBRATION_VERSION ||
      preferences.getUChar("count", 0) != connectedSensorCount()) {
    return false;
  }

  for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
    const SensorPoint &sensor = SENSOR_PINS[i];
    const uint8_t sensorNumber = sensor.sensorNumber;
    idleRawBySensor[sensorNumber] = preferences.getUShort(sensorKey("i", sensorNumber).c_str(), 0);
    maxPressRawBySensor[sensorNumber] = preferences.getUShort(sensorKey("m", sensorNumber).c_str(), 0);
    deadbandBySensor[sensorNumber] = preferences.getUShort(sensorKey("d", sensorNumber).c_str(), MIN_DEADBAND);

    if (idleRawBySensor[sensorNumber] == 0 || idleRawBySensor[sensorNumber] <= maxPressRawBySensor[sensorNumber]) {
      return false;
    }

    smoothedRawBySensor[sensorNumber] = idleRawBySensor[sensorNumber];
    displayPercentBySensor[sensorNumber] = 0;
  }

  Serial.printf("STATUS,calibration_loaded,%u,%lu\n", connectedSensorCount(), PRINT_INTERVAL_MS);
  return true;
}

void clearCalibration() {
  preferences.clear();
  Serial.println("STATUS,calibration_cleared");
}

void calibrateIdle() {
  Serial.println("STATUS,calibrating");

  for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
    const SensorPoint &sensor = SENSOR_PINS[i];
    uint32_t total = 0;
    uint16_t lowest = ADC_MAX;
    uint16_t highest = 0;
    uint16_t smoothed = smoothedRawBySensor[sensor.sensorNumber];

    for (uint16_t sample = 0; sample < IDLE_CALIBRATION_SAMPLES; ++sample) {
      smoothed = updateTemporarySmooth(smoothed, readMedianRaw(sensor.pin));
      if (sample >= 20) {
        total += smoothed;
        lowest = min<uint16_t>(lowest, smoothed);
        highest = max<uint16_t>(highest, smoothed);
      }
      delay(3);
    }

    idleRawBySensor[sensor.sensorNumber] =
        total / (IDLE_CALIBRATION_SAMPLES - 20);
    deadbandBySensor[sensor.sensorNumber] =
        max<uint16_t>(MIN_DEADBAND, highest - lowest);
    maxPressRawBySensor[sensor.sensorNumber] =
        idleRawBySensor[sensor.sensorNumber] > 900 ? idleRawBySensor[sensor.sensorNumber] - 900 : 0;
    smoothedRawBySensor[sensor.sensorNumber] = idleRawBySensor[sensor.sensorNumber];
    displayPercentBySensor[sensor.sensorNumber] = 0;
  }

  saveCalibration();
  Serial.printf("STATUS,ready,%u,%lu\n", connectedSensorCount(), PRINT_INTERVAL_MS);
}

void calibrateMaxPress() {
  Serial.println("STATUS,max_calibrating");

  uint16_t lowestRaw[10] = {};
  for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
    const SensorPoint &sensor = SENSOR_PINS[i];
    lowestRaw[sensor.sensorNumber] = idleRawBySensor[sensor.sensorNumber];
  }

  const uint32_t startMs = millis();
  while (millis() - startMs < MAX_CALIBRATION_MS) {
    readSerialCommands();

    for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
      const SensorPoint &sensor = SENSOR_PINS[i];
      const uint16_t raw = readMedianRaw(sensor.pin);
      smoothedRawBySensor[sensor.sensorNumber] =
          updateTemporarySmooth(smoothedRawBySensor[sensor.sensorNumber], raw);
      lowestRaw[sensor.sensorNumber] =
          min<uint16_t>(lowestRaw[sensor.sensorNumber], smoothedRawBySensor[sensor.sensorNumber]);
    }

    delay(5);
  }

  for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
    const SensorPoint &sensor = SENSOR_PINS[i];
    const uint16_t idleRaw = idleRawBySensor[sensor.sensorNumber];
    uint16_t learnedMax = lowestRaw[sensor.sensorNumber];

    if (idleRaw <= learnedMax + MIN_VALID_RANGE) {
      learnedMax = idleRaw > 900 ? idleRaw - 900 : 0;
    }

    maxPressRawBySensor[sensor.sensorNumber] = learnedMax;
    displayPercentBySensor[sensor.sensorNumber] = 0;
  }

  saveCalibration();
  Serial.printf("STATUS,max_ready,%u,%lu\n", connectedSensorCount(), PRINT_INTERVAL_MS);
}

ImuSample readImuSample() {
  // Replace this stub with the actual IMU driver once the module is known.
  return {false, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F};
}

void handleCommand(const String &command) {
  if (command == "CAL" || command == "IDLE" || command == "TARE" || command == "ZERO") {
    calibrateIdle();
  } else if (command == "MAX" || command == "MAXCAL") {
    calibrateMaxPress();
  } else if (command == "CLEAR" || command == "RESETCAL") {
    clearCalibration();
    calibrateIdle();
  } else if (command == "INFO") {
    Serial.printf("STATUS,info,schema,%u,connected,%u,interval_ms,%lu\n",
                  FRAME_SCHEMA_VERSION, connectedSensorCount(), PRINT_INTERVAL_MS);
  }
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    const char ch = static_cast<char>(Serial.read());
    if (ch == '\n' || ch == '\r') {
      commandBuffer.trim();
      commandBuffer.toUpperCase();
      if (commandBuffer.length() > 0) {
        handleCommand(commandBuffer);
      }
      commandBuffer = "";
    } else if (commandBuffer.length() < 24) {
      commandBuffer += ch;
    }
  }
}

void printFrameLine(const uint16_t rawBySensor[10], uint32_t nowMs, uint32_t dtMs) {
  const ImuSample imu = readImuSample();

  Serial.printf("FRAME,%u,%lu,%lu,%lu,%u",
                FRAME_SCHEMA_VERSION,
                static_cast<unsigned long>(frameSequence++),
                static_cast<unsigned long>(nowMs),
                static_cast<unsigned long>(dtMs),
                connectedSensorCount());

  for (uint8_t sensorNumber = 1; sensorNumber <= 9; ++sensorNumber) {
    if (isSensorConnected(sensorNumber)) {
      const uint8_t targetPercent = pressToPercent(sensorNumber, rawBySensor[sensorNumber]);
      const uint8_t percent = smoothPercent(sensorNumber, targetPercent);
      Serial.printf(",%u,%u", rawBySensor[sensorNumber], percent);
    } else {
      Serial.print(",-1,-1");
    }
  }

  Serial.printf(",%u,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f\n",
                imu.available ? 1 : 0,
                imu.accelX,
                imu.accelY,
                imu.accelZ,
                imu.gyroX,
                imu.gyroY,
                imu.gyroZ,
                imu.tempC);
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  preferences.begin("fsr9", false);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);  // Allows readings near 3.3 V on ESP32 ADC.

  for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
    const SensorPoint &sensor = SENSOR_PINS[i];
    pinMode(sensor.pin, INPUT);
    analogSetPinAttenuation(sensor.pin, ADC_11db);
  }

  if (!loadCalibration()) {
    calibrateIdle();
  }

  Serial.printf("STATUS,frame_schema,%u\n", FRAME_SCHEMA_VERSION);
}

void loop() {
  static uint32_t lastPrintMs = 0;

  readSerialCommands();

  const uint32_t nowMs = millis();
  if (nowMs - lastPrintMs < PRINT_INTERVAL_MS) {
    return;
  }

  const uint32_t dtMs = lastPrintMs == 0 ? 0 : nowMs - lastPrintMs;
  lastPrintMs = nowMs;

  uint16_t rawBySensor[10] = {};
  readAllSensors(rawBySensor);
  printFrameLine(rawBySensor, nowMs, dtMs);
}
