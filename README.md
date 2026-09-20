# Brazo Robotico v1 - ESP32-C3 SuperMini

Sistema de control para brazo robotico de 4 grados de libertad (4 servomotores) utilizando un microcontrolador ESP32-C3 SuperMini e interfaz grafica en Python (`CustomTkinter`).

---

## Conexiones de Hardware

> **Alimentacion:** Usar una fuente de alimentacion externa de 5V (2A - 3A) para los servomotores. Unir la masa (GND) de la fuente externa con el pin GND del ESP32-C3 SuperMini.

### Pines GPIO (ESP32-C3 SuperMini)

| Servomotor | Articulacion | Pin GPIO | Señal PWM | Alimentacion |
| :--- | :--- | :--- | :--- | :--- |
| **Servo 0** | Base | `GPIO 0` | Cable Señal | 5V Externa / GND |
| **Servo 1** | Hombro | `GPIO 1` | Cable Señal | 5V Externa / GND |
| **Servo 2** | Codo | `GPIO 2` | Cable Señal | 5V Externa / GND |
| **Servo 3** | Pinza | `GPIO 3` | Cable Señal | 5V Externa / GND |

---

## Instalación y Uso

### 1. Cargar Firmware (Arduino IDE)

1. Abrir `Codigo Esp32 y Interfaz/esp32_c3_arm/esp32_c3_arm.ino` en Arduino IDE.
2. Instalar la libreria `ESP32Servo` desde el Gestor de Librerias.
3. Seleccionar la placa **ESP32C3 Dev Module**.
4. Cargar el programa al ESP32-C3 SuperMini.

### 2. Ejecutar Interfaz Grafica (Python)

1. Crear entorno virtual e instalar dependencias:
   ```powershell
   uv venv
   uv pip install -r requirements.txt
   ```
2. Ejecutar la GUI:
   ```powershell
   python "Codigo Esp32 y Interfaz/Interfaz de control.py"
   ```
