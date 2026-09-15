/*
 * Firmware Control de Brazo Robótico (4 Servos) - ESP32-C3 SuperMini
 * 
 * Requisitos de Hardware:
 * - Placa ESP32-C3 SuperMini
 * - 4 Servomotores (SG90, MG90S o MG996R)
 * - Fuente de alimentación externa 5V (2A - 3A) para servos
 * 
 * Librerías necesarias en Arduino IDE:
 * - "ESP32Servo" por Kevin Harrington (instalar vía gestor de librerías)
 * 
 * Asignación de Pines:
 * - Servo 0 (Base):    GPIO 2
 * - Servo 1 (Hombro):  GPIO 3
 * - Servo 2 (Codo):    GPIO 4
 * - Servo 3 (Pinza):   GPIO 5
 * 
 * Protocolo Serie (115200 Baudios):
 * Formato de comando: <SERVO_ID>:<ANGULO>\n
 * Ejemplo: "0:90\n"  -> Establece Servo Base a 90 grados
 * Ejemplo: "3:45\n"  -> Establece Servo Pinza a 45 grados
 */

#include <ESP32Servo.h>

// Configuración de Servos
const int NUM_SERVOS = 4;
const int SERVO_PINS[NUM_SERVOS] = {2, 3, 4, 5};

// Objetos Servo
Servo servos[NUM_SERVOS];

// Ángulos iniciales (90° = posición neutral / Home)
int currentAngles[NUM_SERVOS] = {90, 90, 90, 90};

void setup() {
    // Inicializar puerto serie USB
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n=== ESP32-C3 SuperMini Robot Arm Controller ===");

    // Permitir asignación dinámica de timers para ESP32Servo
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    // Adjuntar los 4 servos con el rango de pulso estándar (500us - 2400us a 50Hz)
    for (int i = 0; i < NUM_SERVOS; i++) {
        servos[i].setPeriodHertz(50);
        servos[i].attach(SERVO_PINS[i], 500, 2400);
        servos[i].write(currentAngles[i]);
        delay(100);
    }

    Serial.println("✓ 4 Servomotores inicializados en posicion Home (90 deg)");
    Serial.println("Listo para recibir comandos serie (ejemplo: '0:90')");
}

void loop() {
    // Escuchar comandos por el puerto serie
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

        // Validar índice de servo y ángulo
        if (servoId >= 0 && servoId < NUM_SERVOS) {
            if (angle >= 0 && angle <= 180) {
                servos[servoId].write(angle);
                currentAngles[servoId] = angle;

                // Respuesta de confirmación
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
