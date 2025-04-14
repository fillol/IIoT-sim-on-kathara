# Industrial IoT Simulator on Kathara

![Industry 4.0](https://img.shields.io/badge/-Industry%204.0-4CAF50?logo=industry&logoColor=FFFF00)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=ffd343)
![MQTT](https://img.shields.io/badge/-MQTT-660099?logo=mosquitto&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)
![Kathara](https://img.shields.io/badge/-Kathara-blue?logo=linux&logoColor=white) ![GitHub License](https://img.shields.io/badge/License-MIT-ff69b4)

This project ports the original [Industrial IoT Simulator](https://github.com/fillol/IIoT-simulator) to run within the [Kathara](https://github.com/KatharaFramework/Kathara) network simulation environment. It allows simulating an Industrial IoT (IIoT) setup using Docker containers orchestrated by Kathara, providing a flexible platform for testing network interactions, security postures, and data flow patterns in complex IIoT scenarios.

## 📜 How it Works
This simulator emulates three production lines (pressing, welding, painting) with virtual sensors compliant with Industry 4.0 standards. It generates realistic data (vibration, temperature, quality) transmitted via MQTT over a Kathara-managed network to a central control center with predictive alert logic.

### Key Features (Inherited from original):
* **Realistic Sensor Data**: Vibration (ISO 10816), Temperature (ISO 13732), Quality Control metrics.
* **MQTT Communication**: Configurable QoS levels, payload sizes, and frequencies.
* **Modular Design**: Separate containers for production lines, MQTT broker, and control center.
* **Dynamic Configuration**: Sensor behavior defined in JSON files, decoupled from Python logic.

### Kathara Adaptation:
* Uses Kathara for network topology definition and container orchestration (`lab.conf`, `.startup` files).
* Allows for complex network setups (routers, different subnets) managed by Kathara.
* Provides interactive shells into each component via Kathara.

## 🚀 Usage

### Prerequisites
* [Kathara](https://github.com/KatharaFramework/Kathara) installed.
* Docker and Docker Compose (used for building images).
* Python 3.10+ (Optional: for potential local script testing).

### Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/fillol/IIoT-sim-on-kathara.git
    cd IIoT-sim-on-kathara
    ```

2.  **Build the Docker Images:**
    Navigate to the repository's root directory. The Docker services are defined in `src/compose.yml`.
    ```bash
    # Build all images defined in the compose file within the src directory
    docker compose -f src/compose.yml build
    ```

3.  **Launch the Kathara Lab:**
    Use the `kathara lstart` command to start the network simulation environment defined in `lab.conf`.
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
    * **Kathara Terminals**: The terminals opened by `kathara lstart` provide direct shell access. However, due to the `entrypoint.sh` workaround (see notes below), the main Python scripts might not output directly to these terminals initially.
    * **Docker Logs**: The primary way to see the simulator's output (sensor data, control center messages) is via `docker logs`. The container names are typically defined in `lab.conf` (e.g., `p1`, `p2`, `p3`, `cc`, `mqtt`).
      ```bash
      # Example: View logs for production line 1 and the control center
      docker logs p1 -f
      docker logs cc -f
      ```
    * **Manual Execution (If Needed)**: Sometimes, the main scripts might not start automatically within the Kathara environment. If you don't see output in `docker logs` after a short while, you may need to manually start them in the respective Kathara terminals:
      * In the `p1` terminal: `python main.py`
      * In the `p2` terminal: `python main.py`
      * In the `p3` terminal: `python main.py`
      * In the `cc` terminal: `python main.py`
      (The `mqtt` broker and `rtr` usually don't require manual intervention if their startup scripts are configured correctly).

### Kathara Specific Notes:
* **Entrypoint Workaround**: Each service (`p1`, `p2`, `p3`, `cc`) uses an `entrypoint.sh` that typically launches `/bin/bash`. This keeps the container running and prevents Kathara from potentially terminating it immediately after the main process (like `python main.py`) might finish or if started as a background task within the `.startup` script. The actual application (`python main.py`) is intended to be launched by the `.startup` script or manually.
* **Startup Reliability**: Script execution via `.startup` can sometimes be inconsistent depending on timing or environment factors within Kathara. Manual execution or checking `docker logs` is often necessary.

## 🏗️ Project Structure

```
.
├── cc.startup          # Startup script for the Control Center container
├── lab.conf            # Kathara lab configuration (topology, devices)
├── mqtt.startup        # Startup script for the MQTT Broker container
├── p1.startup          # Startup script for Production Line 1
├── p2.startup          # Startup script for Production Line 2
├── p3.startup          # Startup script for Production Line 3
├── readme.md           # This file
├── rtr.startup         # Startup script for the Router container
├── shared/             # Directory mounted into containers (if needed by Kathara config)
└── src/                # Source code for the simulation components
    ├── compose.yml     # Docker Compose file (used for building images)
    ├── control-center/ # Central monitoring system logic
    │   ├── Dockerfile
    │   ├── entrypoint.sh # Keeps container alive for Kathara
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

# Note: MQTT Broker (Mosquitto) is likely pulled as a standard image via lab.conf, not built from src/.
```

## 🔍 Composition:

(This section can largely remain the same as the original, describing the roles of Production Lines, Control Center, MQTT Broker, Payload Strategy, and Realistic Metrics. Ensure paths mentioned like `lineX.json` reflect the new structure, e.g., they are inside `src/publisherX/`.)

### 🐳 Key Actors:

#### 1. Production Lines (p1, p2, p3)
* **Implementation**: Python scripts (`src/publisherX/main.py`) using sensor classes (`src/publisherX/sensors/`).
* **Configuration**: Defined in JSON files (`src/publisherX/lineX.json`). Example (`src/publisher1/line1.json`):
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
* **Data Generation**: Simulates Vibration, Temperature, and Quality sensors based on industrial standards.

#### 2. Control Center (cc)
* **Subscription**: Monitors MQTT topics (e.g., `factory/#`). Logic in `src/control-center/main.py`.
* **Alert Logic**: Processes incoming data and triggers alerts based on predefined rules.

#### 3. MQTT Broker (mqtt)
* Typically the standard `eclipse-mosquitto` image, configured via `mqtt.startup` or a custom config file mounted by Kathara. Handles message queuing and delivery.

#### 4. Router (rtr)
* A simple container (e.g., based on Alpine or FRR) configured by Kathara (`rtr.startup`) to route traffic between different network segments defined in `lab.conf`.

### 📦 Payload Strategy & 🔬 Realistic Industrial Metrics

(These sections detailing payload sizes, frequencies, sensor standards like ISO 10816/13732, and data parameters can be copied directly from your original README as the core simulation logic remains unchanged.)

---

## 🛠️ Customization in Kathara Environment

### 🔧 **Customizing Sensor Parameters**
1.  Modify the desired JSON configuration file (e.g., `src/publisher1/line1.json`) within your project directory. Change intervals, payload sizes, or QoS levels.
2.  Rebuild the specific Docker image if changes require it (though often JSON changes don't require a rebuild if mounted correctly, check your `.startup` and `lab.conf`). If unsure, rebuild:
    ```bash
    docker compose -f src/compose.yml build publisher1 # Or the specific service
    ```
3.  Restart the Kathara lab:
    ```bash
    sudo kathara lstop # Stop the currently running lab
    sudo kathara lstart
    ```

### 🏭 **Adding a New Production Line (e.g., Line 4)**
1.  **Create Source Files**: Duplicate an existing publisher directory (e.g., copy `src/publisher1` to `src/publisher4`).
2.  **Configure Line 4**: Create/modify `src/publisher4/line4.json` with the desired `line_id` and sensor configuration.
3.  **Update Docker Build**: Add a service definition for `production-line-4` in `src/compose.yml` pointing to the `src/publisher4` directory and its Dockerfile.
4.  **Update Kathara Config**:
    * Add the new device (e.g., `p4`) to `lab.conf`, connecting it to the appropriate network(s).
    * Specify the Docker image to use for `p4` (e.g., `your_dockerhub_user/kathara-iiot-p4:latest` or the locally built image name).
    * Create a `p4.startup` script to launch the application inside the container.
5.  **Build the New Image**:
    ```bash
    docker compose -f src/compose.yml build production-line-4
    ```
6.  **Launch the Updated Lab**:
    ```bash
    sudo kathara lstart
    ```

### Other Modifications
* **Custom Alert Rules**: Modify `src/control-center/main.py` and rebuild/restart `cc`.
* **New Sensor Types**: Create new Python classes in `src/publisherX/sensors/`, register them, update JSON configs, rebuild images, and restart the lab.
* **Network Topology**: Modify `lab.conf` to change connections, add routers, or introduce network impairments (if using Kathara's advanced features).

---

## 🏭 Conclusion: IIoT Simulation in a Network Context

This Kathara-adapted simulator provides a powerful environment for:
* Testing IIoT architectures within realistic or complex network topologies.
* Analyzing the impact of network conditions (latency, packet loss - if simulated via Kathara) on MQTT communication.
* Developing and validating network security policies for IIoT systems.
* Training cybersecurity and network professionals on IIoT scenarios.