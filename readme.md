![Industry 4.0](https://img.shields.io/badge/-Industry%204.0-4CAF50?logo=industry&logoColor=FFFF00)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=ffd343)
![MQTT](https://img.shields.io/badge/-MQTT-660099?logo=mosquitto&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)
![Kathará](https://img.shields.io/badge/-Kathara-blue?logo=linux&logoColor=white) 
![GitHub License](https://img.shields.io/badge/License-MIT-ff69b4)

# Industrial IoT Simulator on Kathará

This project ports the original [Industrial IoT Simulator](https://github.com/fillol/IIoT-simulator) to run within the [Kathará](https://github.com/KatharaFramework/Kathara) network simulation environment. It allows simulating an Industrial IoT (IIoT) setup using Docker containers orchestrated by Kathará, providing a flexible platform for testing network interactions, security postures, and data flow patterns in complex IIoT scenarios.

## 📜 How it Works
This simulator emulates three production lines (pressing, welding, painting) with virtual sensors compliant with Industry 4.0 standards. It generates realistic data (vibration, temperature, quality) transmitted via MQTT over a Kathará-managed network to a central control center with predictive alert logic.

### Key Features (Inherited from original):
* **Realistic Sensor Data**: Vibration (ISO 10816 principles), Temperature (ISO 13732 principles), Quality Control metrics.
* **MQTT Communication**: Configurable QoS levels, payload sizes, and frequencies.
* **Modular Design**: Separate containers for production lines, MQTT broker, and control center.
* **Dynamic Configuration**: Sensor behavior defined in JSON files, decoupled from Python logic.

### Kathará Adaptation:
* Uses Kathará for network topology definition and container orchestration (`lab.conf`, `.startup` files).
* Allows for complex network setups (routers, different subnets) managed by Kathará.
* Provides interactive shells into each component via Kathará.

## 🚀 Usage

### Prerequisites
* [Kathará](https://github.com/KatharaFramework/Kathara) installed.
* Docker and Docker Compose (used for building images).
* Python 3.10+ (Optional: for potential local script testing).

### Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/fillol/IIoT-sim-on-Kathara.git
    cd IIoT-sim-on-Kathara
    ```

2.  **Build the Docker Images:**
    Navigate to the repository's root directory. The Docker services are defined in `src/compose.yml`.
    ```bash
    # Build all images defined in the compose file within the src directory
    docker compose -f src/compose.yml build
    ```

3.  **Launch the Kathará Lab:**
    Use the `lstart` command to start the network simulation environment defined in `lab.conf`.
    *Important:* This often requires `sudo` permissions.
    ```bash
    sudo kathara lstart
    ```
    This command will:
    * Read `lab.conf` to understand the network topology and devices (p1, p2, p3, cc, mqtt, rtr).
    * Start Docker containers for each device.
    * Execute the corresponding `.startup` scripts within each container.
    * Open terminal windows connected to each running container (p1, p2, p3, cc, mqtt, rtr).

4.  **Monitor the Simulation:**
    * **Kathará Terminals**: The terminals opened by `Kathara lstart` provide direct shell access. However, due to the `entrypoint.sh` workaround (see notes below), the main Python scripts might not output directly to these terminals initially.
    * **Docker Logs**: The primary way to see the simulator's output (sensor data, control center messages) is via `docker logs`. The container names are typically defined in `lab.conf` (e.g., `p1`, `p2`, `p3`, `cc`, `mqtt`).
        ```bash
        # Example: View logs for production line 1 and the control center
        docker logs -f p1
        docker logs -f cc
        ```
    * **Manual Execution (If Needed)**: Sometimes, the main scripts might not start automatically within the Kathará environment. If you don't see output in `docker logs` after a short while, you may need to manually start them in the respective Kathará terminals:
        * In the `p1` terminal: `python main.py`
        * In the `p2` terminal: `python main.py`
        * In the `p3` terminal: `python main.py`
        * In the `cc` terminal: `python main.py`
        (The `mqtt` broker and `rtr` usually don't require manual intervention if their startup scripts are configured correctly).

### Kathará Specific Notes:
* **Entrypoint Workaround**: Each service (`p1`, `p2`, `p3`, `cc`) uses an `entrypoint.sh` that typically launches `/bin/bash`. This keeps the container running and prevents Kathará from potentially terminating it immediately after the main process (like `python main.py`) might finish or if started as a background task within the `.startup` script. The actual application (`python main.py`) is intended to be launched by the `.startup` script or manually.
* **Startup Reliability**: Script execution via `.startup` can sometimes be inconsistent depending on timing or environment factors within Kathará. Manual execution or checking `docker logs` is often necessary.

## 🏗️ Project Structure

```
.
├── cc.startup          # Startup script for the Control Center container
├── lab.conf            # Kathará lab configuration (topology, devices)
├── mqtt.startup        # Startup script for the MQTT Broker container
├── p1.startup          # Startup script for Production Line 1
├── p2.startup          # Startup script for Production Line 2
├── p3.startup          # Startup script for Production Line 3
├── readme.md           # This file
├── rtr.startup         # Startup script for the Router container
├── shared/             # Directory mounted into containers (if needed by Kathará config)
└── src/                # Source code for the simulation components
    ├── compose.yml     # Docker Compose file (used for building images)
    ├── control-center/ # Central monitoring system logic
    │   ├── Dockerfile
    │   ├── entrypoint.sh # Keeps container alive for Kathará
    │   ├── main.py       # Real-time analysis logic
    │   └── requirements.txt
    ├── publisher1/     # Production Line 1 simulator
    │   ├── Dockerfile
    │   ├── entrypoint.sh
    │   ├── line1.json    # Configuration for Line 1
    │   ├── main.py       # Sensor data generation/publishing
    │   ├── requirements.txt
    │   └── sensors/      # Sensor implementation code (shared logic)
    │       ├── base_sensor.py
    │       ├── __init__.py
    │       ├── QualitySensor.py
    │       ├── TemperatureSensor.py
    │       └── VibrationSensor.py
    ├── publisher2/     # Production Line 2 simulator (similar structure)
    │   ├── ...
    │   └── line2.json
    └── publisher3/     # Production Line 3 simulator (similar structure)
        ├── ...
        └── line3.json
```

> **Note:** MQTT Broker (Mosquitto) is likely pulled as a standard image via lab.conf, not built from src/.

## 🔍 Composition:

### 🐳 Key Actors:

#### 1. Production Lines (p1, p2, p3)
* **Implementation:** Python scripts (`src/publisherX/main.py`) using sensor classes (`src/publisherX/sensors/`).
* **Configuration:** Defined in JSON files (`src/publisherX/lineX.json`). Example (`src/publisher1/line1.json`):
    ```json
    {
      "line_id": "PRESS-LINE-1",
      "sensors": [
        {
          "type": "vibration",
          "interval": 0.5,
          "payload": "small",
          "qos": 2
        }
      ]
    }
    ```
* **Data Generation:** Simulates Vibration, Temperature, and Quality sensors based on industrial standards.

#### 2. Control Center (cc)
* **Subscription:** Monitors MQTT topics (e.g., `factory/#`). Logic in `src/control-center/main.py`.
* **Alert Logic:** Processes incoming data and triggers alerts based on predefined rules.

#### 3. MQTT Broker (mqtt)
* Typically the standard `eclipse-mosquitto` image, configured via `mqtt.startup` or a custom config file mounted by Kathará. Handles message queuing and delivery.

#### 4. Router (rtr)
* A simple container (e.g., based on Alpine or FRR) configured by Kathará (`rtr.startup`) to route traffic between different network segments defined in `lab.conf`.

### 📦 Payload Strategy

| Category   | Size          | Frequency | Use Case             | Example Line   |
| :--------- | :------------ | :-------- | :------------------- | :------------- |
| **Small**  | 1-10 KB       | 0.5-2 sec | Real-time monitoring | PRESS-LINE-1   |
| **Medium** | 10-100 KB     | 2-5 sec   | Historical trends    | WELDING-LINE-2 |
| **Large**  | 100 KB - 1 MB | 5-10 sec  | Big Data/Analytics   | PAINT-LINE-3   |

---

## 🔬 Realistic Industrial Metrics

This simulator aims to generate data reflecting real-world industrial conditions. The following sensor configurations provide a baseline.

#### 1. **VibrationSensor** (Predictive Maintenance)

* **Reference Standard:** Based on principles similar to [ISO 10816-3](https://www.iso.org/standard/78311.html) (Vibrations in industrial machinery).
* **Simulated Data Points:**
    ```python
    {
      "x": random.uniform(2.0, 15.0),  # Simulated RMS Velocity [mm/s] or Acceleration [m/s²]
      "fft": [random.random() for _ in range(100)],  # Simulated frequency components
      "metadata": {
         "samples": size//1000  # Abstract representation
      }
    }
    ```
* **Simulator Default Configuration:** Examples use a **2 Hz** reporting frequency with a **"small" (1-10 KB)** payload, including FFT data.
* **Real-World Context:** Industrial predictive maintenance often employs high sampling rates (e.g., kHz range, like 10-20 kHz) to capture detailed vibration signatures for effective FFT analysis, especially for bearing faults. The simulator's 2 Hz default frequency represents a reporting interval for processed data.
* **Simulated Alarm Thresholds (Example logic):**
    * Warning: >8 (unit depends on metric)
    * Critical: >15 (unit depends on metric)

#### 2. **TemperatureSensor** (Thermal Management)

* **Reference Standard:** Relevant to principles in [ISO 13732-1](https://www.iso.org/standard/43558.html) (Thermal contact safety).
* **Simulated Data Points:**
    ```python
    {
      "motor_temp": random.uniform(30.0, 90.0),  # °C
      "bearing_temp": random.normalvariate(60.0, 5.0),  # °C
      "trend": [...]  # Simulated recent data points
    }
    ```
* **Simulator Default Configuration:** Implied frequencies range from **0.1 Hz (10s interval) to 2 Hz (0.5s interval)**.
* **Real-World Context:** Temperature reporting intervals vary by application, from seconds for critical processes to minutes for general monitoring. The simulator’s configuration is plausible and can be customized to reflect specific thermal dynamics.
* **Simulated Critical Thresholds (Example logic):**
    * Motor: >85°C
    * Bearings: >70°C

#### 3. **QualitySensor** (Quality Control 4.0)

* **AI-driven Metrics Concept:** Simulates output from an AI-based quality control system.
* **Simulated Data Points:**
    ```python
    {
      "defect_count": random.randint(0, 5),
      "image_meta": {
         "size_kb": target_size//1024,
         "defect_coordinates": [...],
         "image_hash": "..."  # Simulated hash/identifier
      }
    }
    ```
* **Simulator Default Configuration:** Examples use a **0.1 Hz (10s interval)** frequency with a **"large" (100 KB - 1 MB)** payload.
* **Real-World Context:** Visual inspection data volumes vary, and edge processing is used to reduce transmitted data. The simulator's configuration abstracts detailed image analysis by using a large payload for a processed "image hash."
* **Simulated Alert (Example logic):** More than 3 defects per batch triggers an alert.

### 📚 Supporting Sources

To reinforce the design choices of the simulator, the following reputable sources provide validation for each sensor type:

#### 1. Vibration Sensors
- **TE Connectivity – [Predictive Maintenance with Vibration Sensors](https://www.te.com/en/whitepapers/sensors/predictive-maintenance-with-vibration-sensors.html)**  
  Demonstrates how high-frequency sensors can provide actionable data for predictive maintenance.  

- **CBM Connect – [Simplified Vibration Monitoring: ISO 10816‑3 Guidelines](https://www.cbmconnect.com/simplified-vibration-monitoring-iso-10816-3-guidelines/)**  
  Offers guidelines on vibration monitoring based on ISO 10816‑3, reinforcing the importance of realistic sensor parameters.  

- **EEWeb – [Sensors in Industry 4.0: Vibration Monitoring](https://www.eeweb.com/sensors-in-industry-4-0-vibration-monitoring/)**  
  Provides an extensive overview of the technologies behind industrial vibration sensors within the Industry 4.0 framework.  

#### 2. Temperature Sensors
- **Phase IV Engineering – [Wireless Motor Sensor for Predictive Maintenance](https://www.phaseivengr.com/product/sensors/temperature/wireless-motor-sensor-predictive-maintenance/)**  
  Highlights the importance of thermal monitoring for preventive maintenance, even with adjustable reporting intervals.  

- **NCD Store – [Smart Industrial IoT Wireless Vibration Temperature Sensor](https://store.ncd.io/product/smart-industrial-iot-wireless-vibration-temperature-sensor/)**  
  Demonstrates the integration of temperature measurement in multi-sensor IoT devices, supporting the simulator’s approach.

- **Standard - [ISO 13732](https://www.iso.org/standard/43558.html)**  
  This internationally recognized standard provides reliable criteria for thermal monitoring, supporting the sensor configuration.

#### 3. Quality Control Sensor
- **IMechE – [How Condition Monitoring Led the Way to Industry 4.0](https://www.imeche.org/news/news-article/how-condition-monitoring-led-the-way-to-industry-4-0)**  
  Discusses the evolution of monitoring systems in industrial settings, including AI-driven quality analysis.

- **Maintenance and Engineering – [Vibration Monitoring: A Case Study](https://www.maintenanceandengineering.com/2014/01/01/vibration-monitoring-a-case-study/)**  
  Presents case studies where advanced monitoring techniques, including image analysis, have improved process reliability.

- **Analog Devices – [Choosing the Best Vibration Sensor for Wind Turbine Condition Monitoring](https://www.analog.com/en/resources/analog-dialogue/articles/choosing-the-best-vibration-sensor-for-wind-turbine-condition-monitoring.html)**  
  Exemplifies the use of advanced sensor technologies and data processing, including image-based methods, in modern industrial applications.

---

## 🛠️ Customization in Kathará Environment

### 🔧 Customizing Sensor Parameters
1.  Modify the desired JSON configuration file (e.g., `src/publisher1/line1.json`) within your project directory. Change intervals, payload sizes, or QoS levels.
2.  Rebuild the specific Docker image if required (often JSON changes do not require a rebuild if mounted correctly, but check your `.startup` and `lab.conf`). If unsure, rebuild:
    ```bash
    docker compose -f src/compose.yml build publisher1  # Or the specific service
    ```
3.  Restart the Kathará lab:
    ```bash
    sudo kathara lclean  # Stop the currently running lab
    sudo kathara lstart
    ```

### 🏭 Adding a New Production Line (e.g., Line 4)
1.  **Create Source Files:** Duplicate an existing publisher directory (e.g., copy `src/publisher1` to `src/publisher4`).
2.  **Configure Line 4:** Create/modify `src/publisher4/line4.json` with the desired `line_id` and sensor configuration.
3.  **Update Docker Build:** Add a service definition for `production-line-4` in `src/compose.yml` pointing to the `src/publisher4` directory and its Dockerfile.
4.  **Update Kathará Config:**
    - Add the new device (e.g., `p4`) to `lab.conf`, connecting it to the appropriate network(s).
    - Specify the Docker image to use for `p4` (e.g., `your_dockerhub_user/Kathara-iiot-p4:latest` or the locally built image name).
    - Create a `p4.startup` script to launch the application inside the container.
5.  **Build the New Image:**
    ```bash
    docker compose -f src/compose.yml build production-line-4  # Use the service name from compose.yml
    ```
6.  **Launch the Updated Lab:**
    ```bash
    sudo kathara lstart
    ```

### Other Modifications
* **Custom Alert Rules:** Modify `src/control-center/main.py` and rebuild/restart `cc`.
* **New Sensor Types:** Create new Python classes in `src/publisherX/sensors/`, register them, update JSON configs, rebuild images, and restart the lab.
* **Network Topology:** Modify `lab.conf` to change connections, add routers, or introduce network impairments (using Kathará's advanced features).

---

## 🏭 Conclusion: IIoT Simulation in a Network Context

This Kathará-adapted simulator provides a powerful environment for:
* Testing IIoT architectures within realistic or complex network topologies.
* Analyzing the impact of network conditions (latency, packet loss—if simulated via Kathará) on MQTT communication.
* Developing and validating network security policies for IIoT systems.
* Training cybersecurity and network professionals on IIoT scenarios.
