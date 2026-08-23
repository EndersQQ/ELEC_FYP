#include <Arduino.h>
#include <Preferences.h>
#include <Wire.h>

/*
  RF-PUL9Z-V1 9-zone FSR array for ESP32-S3.

  Voltage divider wiring (pressure raises the ADC reading):
    3.3V -> sensor C/common -> FSR point N -> ADC pin -> resistor -> GND

  Serial:
    STATUS,<state>[,<detail>...]
    FRAME,<schema>,<seq>,<ms>,<dt_ms>,9,<raw1>,<pct1>...<raw9>,<pct9>,
          <imu_ok>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<temp_c>
*/

struct SensorPoint {
  uint8_t sensorNumber;
  uint8_t pin;
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
constexpr uint8_t CALIBRATION_VERSION = 4;
constexpr uint16_t ADC_MAX = 4095;
constexpr uint8_t MEDIAN_SAMPLES_PER_POINT = 5;
constexpr uint16_t IDLE_CALIBRATION_SAMPLES = 180;
constexpr uint32_t PRINT_INTERVAL_MS = 20;
constexpr uint16_t MIN_DEADBAND = 70;
constexpr uint16_t MIN_ACTIVE_RISE = 80;
constexpr uint8_t ADC_DISCARD_READS = 2;
constexpr uint16_t ADC_SETTLE_US = 250;
constexpr uint16_t ADC_SAMPLE_GAP_US = 100;
constexpr uint8_t CONNECTED_SENSOR_COUNT = 9;
constexpr uint8_t MPU6050_SDA_PIN = 17;
constexpr uint8_t MPU6050_SCL_PIN = 18;
constexpr uint32_t MPU6050_I2C_FREQUENCY = 400000;
constexpr uint8_t MPU6050_ADDRESS_LOW = 0x68;
constexpr uint8_t MPU6050_ADDRESS_HIGH = 0x69;
constexpr uint8_t MPU6050_REG_ACCEL_XOUT_H = 0x3B;
constexpr uint8_t MPU6050_REG_PWR_MGMT_1 = 0x6B;
constexpr uint8_t MPU6050_REG_WHO_AM_I = 0x75;

// Sensor layout:
//   3 6 9
//   2 5 8
//   1 4 7
SensorPoint SENSOR_PINS[9] = {
    {1, 1},
    {2, 2},
    {3, 3},
    {4, 4},
    {5, 5},
    {6, 6},
    {7, 7},
    {8, 8},
    {9, 9},
};

Preferences preferences;
uint16_t idleRawBySensor[10] = {};
uint16_t smoothedRawBySensor[10] = {};
uint16_t deadbandBySensor[10] = {};
uint8_t displayPercentBySensor[10] = {};
String commandBuffer;
uint32_t frameSequence = 0;
uint8_t mpu6050Address = 0;
bool mpu6050Ready = false;

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
          ((smoothedRawBySensor[sensor.sensorNumber] * 3U) + raw + 2U) / 4U;
    }

    rawBySensor[sensor.sensorNumber] = smoothedRawBySensor[sensor.sensorNumber];

    const uint8_t sensorNumber = sensor.sensorNumber;
    const uint16_t idleRaw = idleRawBySensor[sensorNumber];
    const uint16_t deadband = deadbandBySensor[sensorNumber];
    if (idleRaw > deadband && rawBySensor[sensorNumber] + deadband < idleRaw) {
      idleRawBySensor[sensorNumber] = rawBySensor[sensorNumber];
    }
  }
}

uint8_t pressToPercent(uint8_t sensorNumber, uint16_t raw) {
  const uint16_t idleRaw = idleRawBySensor[sensorNumber];
  const uint16_t deadband = deadbandBySensor[sensorNumber];

  if (static_cast<uint32_t>(raw) <=
      static_cast<uint32_t>(idleRaw) + deadband + MIN_ACTIVE_RISE) {
    return 0;
  }

  if (static_cast<uint32_t>(idleRaw) + deadband >= ADC_MAX) {
    return 0;
  }

  const uint16_t activeRange = ADC_MAX - idleRaw - deadband;
  const uint16_t press = raw - idleRaw - deadband;
  const uint32_t percent = (static_cast<uint32_t>(press) * 100U) / activeRange;
  return min<uint32_t>(percent, 100U);
}

uint8_t smoothPercent(uint8_t sensorNumber, uint8_t targetPercent) {
  uint8_t &displayPercent = displayPercentBySensor[sensorNumber];

  if (targetPercent < 3) {
    targetPercent = 0;
  }

  if (targetPercent > displayPercent) {
    displayPercent += max<uint8_t>(1, (targetPercent - displayPercent + 2) / 3);
  } else if (targetPercent < displayPercent) {
    displayPercent -= max<uint8_t>(1, (displayPercent - targetPercent + 1) / 2);
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
    deadbandBySensor[sensorNumber] = preferences.getUShort(sensorKey("d", sensorNumber).c_str(), MIN_DEADBAND);

    if (static_cast<uint32_t>(idleRawBySensor[sensorNumber]) +
            deadbandBySensor[sensorNumber] >=
        ADC_MAX) {
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
    smoothedRawBySensor[sensor.sensorNumber] = idleRawBySensor[sensor.sensorNumber];
    displayPercentBySensor[sensor.sensorNumber] = 0;
  }

  saveCalibration();
  Serial.printf("STATUS,ready,%u,%lu\n", connectedSensorCount(), PRINT_INTERVAL_MS);
}

bool writeMpuRegister(uint8_t address, uint8_t reg, uint8_t value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readMpuRegister(uint8_t address, uint8_t reg, uint8_t &value) {
  Wire.beginTransmission(address);
  Wire.write(reg);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom(address, static_cast<uint8_t>(1)) != 1) {
    return false;
  }

  value = Wire.read();
  return true;
}

bool mpuAddressResponds(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

int16_t readWireInt16() {
  const uint8_t highByte = Wire.read();
  const uint8_t lowByte = Wire.read();

  return static_cast<int16_t>(
      (static_cast<uint16_t>(highByte) << 8) | lowByte);
}

bool initializeMpu6050() {
  if (mpuAddressResponds(MPU6050_ADDRESS_LOW)) {
    mpu6050Address = MPU6050_ADDRESS_LOW;
  } else if (mpuAddressResponds(MPU6050_ADDRESS_HIGH)) {
    mpu6050Address = MPU6050_ADDRESS_HIGH;
  } else {
    Serial.println("STATUS,imu_error,mpu6050_not_found");
    return false;
  }

  uint8_t whoAmI = 0;
  if (!readMpuRegister(mpu6050Address, MPU6050_REG_WHO_AM_I, whoAmI)) {
    Serial.println("STATUS,imu_error,who_am_i_read_failed");
    return false;
  }

  Serial.printf("STATUS,imu_detected,address,0x%02X,who_am_i,0x%02X\n",
                mpu6050Address, whoAmI);

  if (whoAmI != 0x68) {
    Serial.printf("STATUS,imu_warning,unexpected_who_am_i,0x%02X\n", whoAmI);
  }

  if (!writeMpuRegister(mpu6050Address, MPU6050_REG_PWR_MGMT_1, 0x00)) {
    Serial.println("STATUS,imu_error,wake_failed");
    return false;
  }

  delay(100);
  Serial.println("STATUS,imu_ready,mpu6050");
  return true;
}

ImuSample readImuSample() {
  if (!mpu6050Ready) {
    return {false, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F};
  }

  Wire.beginTransmission(mpu6050Address);
  Wire.write(MPU6050_REG_ACCEL_XOUT_H);

  if (Wire.endTransmission(false) != 0) {
    return {false, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F};
  }

  constexpr uint8_t SAMPLE_BYTES = 14;
  if (Wire.requestFrom(mpu6050Address, SAMPLE_BYTES) != SAMPLE_BYTES) {
    return {false, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F};
  }

  const int16_t rawAccelX = readWireInt16();
  const int16_t rawAccelY = readWireInt16();
  const int16_t rawAccelZ = readWireInt16();
  const int16_t rawTemp = readWireInt16();
  const int16_t rawGyroX = readWireInt16();
  const int16_t rawGyroY = readWireInt16();
  const int16_t rawGyroZ = readWireInt16();

  constexpr float ACCEL_LSB_PER_G = 16384.0F;
  constexpr float GRAVITY_MPS2 = 9.80665F;
  constexpr float GYRO_LSB_PER_DPS = 131.0F;

  return {
      true,
      (rawAccelX / ACCEL_LSB_PER_G) * GRAVITY_MPS2,
      (rawAccelY / ACCEL_LSB_PER_G) * GRAVITY_MPS2,
      (rawAccelZ / ACCEL_LSB_PER_G) * GRAVITY_MPS2,
      rawGyroX / GYRO_LSB_PER_DPS,
      rawGyroY / GYRO_LSB_PER_DPS,
      rawGyroZ / GYRO_LSB_PER_DPS,
      (rawTemp / 340.0F) + 36.53F,
  };
}

void handleCommand(const String &command) {
  if (command == "CAL" || command == "IDLE" || command == "TARE" || command == "ZERO") {
    calibrateIdle();
  } else if (command == "CLEAR" || command == "RESETCAL") {
    clearCalibration();
    calibrateIdle();
  } else if (command == "INFO") {
    Serial.printf("STATUS,info,schema,%u,connected,%u,interval_ms,%lu\n",
                  FRAME_SCHEMA_VERSION, connectedSensorCount(), PRINT_INTERVAL_MS);
  } else if (command == "CALINFO") {
    for (uint8_t i = 0; i < connectedSensorCount(); ++i) {
      const SensorPoint &sensor = SENSOR_PINS[i];
      const uint8_t sensorNumber = sensor.sensorNumber;
      Serial.printf("STATUS,calinfo,%u,idle,%u,deadband,%u\n",
                    sensorNumber,
                    idleRawBySensor[sensorNumber],
                    deadbandBySensor[sensorNumber]);
    }
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

  if (!Wire.begin(MPU6050_SDA_PIN, MPU6050_SCL_PIN, MPU6050_I2C_FREQUENCY)) {
    Serial.println("STATUS,imu_error,i2c_start_failed");
  } else {
    Serial.printf("STATUS,i2c_started,sda,%u,scl,%u,frequency,%lu\n",
                  MPU6050_SDA_PIN,
                  MPU6050_SCL_PIN,
                  static_cast<unsigned long>(MPU6050_I2C_FREQUENCY));
    mpu6050Ready = initializeMpu6050();
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
