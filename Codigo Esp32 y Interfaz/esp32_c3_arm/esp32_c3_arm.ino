/*
 * Firmware Control de Brazo Robótico (4 Servos) - ESP32-C3 SuperMini
 * Colegio Científico Los Santos
 * 
 * Requisitos de Hardware:
 * - Placa ESP32-C3 SuperMini
 * - 4 Servomotores (SG90, MG90S o MG996R)
 * - Fuente de alimentación externa 5V (2A - 3A) para servos
 * 
 * Asignación de Pines:
 * - Servo 0 (Base):    GPIO 2
 * - Servo 1 (Hombro):  GPIO 3
 * - Servo 2 (Codo):    GPIO 4
 * - Servo 3 (Pinza):   GPIO 5
 */

#include <ESP32Servo.h>

const int NUM_SERVOS = 4;
const int SERVO_PINS[NUM_SERVOS] = {2, 3, 4, 5};

Servo servos[NUM_SERVOS];
int currentAngles[NUM_SERVOS] = {90, 90, 90, 90};

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n=== ESP32-C3 SuperMini Robot Arm Controller - Colegio Cientifico Los Santos ===");

    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    for (int i = 0; i < NUM_SERVOS; i++) {
        servos[i].setPeriodHertz(50);
        servos[i].attach(SERVO_PINS[i], 500, 2400);
        servos[i].write(currentAngles[i]);
        delay(100);
    }

    Serial.println("OK: 4 Servomotores inicializados en posicion Home (90 deg)");
}

void loop() {
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim();

        if (input.length() > 0) {
            processCommand(input);
        }
    }
}

void processCommand(String cmd) {
    int colonIndex = cmd.indexOf(':');
    
    if (colonIndex != -1) {
        int servoId = cmd.substring(0, colonIndex).toInt();
        int angle = cmd.substring(colonIndex + 1).toInt();

        if (servoId >= 0 && servoId < NUM_SERVOS) {
            if (angle >= 0 && angle <= 180) {
                servos[servoId].write(angle);
                currentAngles[servoId] = angle;

                Serial.print("OK: Servo ");
                Serial.print(servoId);
                Serial.print(" -> ");
                Serial.print(angle);
                Serial.println(" deg");
            } else {
                Serial.println("ERROR: Angulo fuera de rango (0-180)");
            }
        } else {
            Serial.println("ERROR: ID de Servo invalido (0-3)");
        }
    } else {
        Serial.println("ERROR: Formato invalido. Usar 'SERVO_ID:ANGULO'");
    }
}
