![Industry 4.0](https://img.shields.io/badge/-Industry%204.0-4CAF50?logo=industry&logoColor=FFFF00)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=ffd343)
![Flask](https://img.shields.io/badge/-Flask-000000?logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)
![Kathará](https://img.shields.io/badge/-Kathara-blue?logo=linux&logoColor=white)
![GitHub License](https://img.shields.io/badge/License-MIT-ff69b4)

# Industrial IoT Simulator on Kathará

This project ports the original [Industrial IoT Simulator](https://github.com/fillol/IIoT-simulator) to run within the [Kathará](https://github.com/KatharaFramework/Kathara) network simulation environment. It allows simulating an Industrial IoT (IIoT) setup using Docker containers orchestrated by Kathará, providing a flexible platform for testing network interactions, security postures, and data flow patterns in complex IIoT scenarios.

## 📜 How it Works

This simulator emulates three production lines (pressing, welding, painting) with virtual sensors compliant with Industry 4.0 standards. It generates realistic data (vibration, temperature, quality) transmitted via **HTTP requests** over a **complex, multi-hop** Kathará-managed network.

The data flows through a pipeline of microservices: data is first sent to a **Dropper** service that simulates network unreliability and routes traffic. Secure payloads are sent to a dedicated **Decrypter** service, while standard data goes directly to a **Fault Detector**. The Fault Detector analyzes the data, and if an anomaly is found, it sends an alert to a **Digital Twin** service, which acts as the final logging endpoint.

### Key Features (Inherited from original):

*   **Realistic Sensor Data**: Vibration (ISO 10816 principles), Temperature (ISO 13732 principles), Quality Control metrics.
*   **Microservice Architecture**: Separate containers for production lines and each stage of the data processing pipeline.
*   **Dynamic Configuration**: Sensor behavior defined in JSON files, decoupled from Python logic.

### Kathará Adaptation:

*   Uses Kathará for network topology definition and container orchestration (`lab.conf`, `.startup` files).
*   Services communicate via HTTP requests using Flask, making the architecture robust and easily integrable.
*   Allows for complex network setups (with **multiple intermediate routers** and dedicated paths) managed by Kathará.
*   Provides interactive shells into each component via Kathará.

## 🚀 Usage

### Prerequisites

*   [Kathará](https://github.com/KatharaFramework/Kathara) installed.
*   Docker and Docker Compose (used for building images).
*   Python 3.10+ (Optional: for potential local script testing).

### Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/fillol/IIoT-sim-on-Kathara.git
    cd IIoT-sim-on-Kathara
    ```

2.  **Build the Docker Images:**
    The project uses Docker Compose to build the required service images. From the repository's root directory, run:
    ```bash
    # Build all service images needed for the simulation
    docker compose build
    ```

3.  **Launch the Kathará Lab:**
    Use the `lstart` command to start the network simulation environment defined in `lab.conf`.
    *Important:* This often requires `sudo` permissions.
    ```bash
    sudo kathara lstart
    ```
    This command will:
    *   Read `lab.conf` to understand the network topology and devices.
    *   Start Docker containers for each device using the pre-built images.
    *   Execute the corresponding `.startup` scripts within each container to configure networking.
    *   Open terminal windows connected to each running container.

4.  **Monitor the Simulation:**
    The primary way to see the simulator's output is by manually running the applications inside the Kathará terminals.
    *   **Manual Execution**: In the respective Kathará terminals:
        *   In the `p1`, `p2`, `p3` terminals: `python main.py`
        *   In the `dropper`, `decrypter`, `fault-detector`, and `digital-twin` terminals: `python main.py`

### Kathará Specific Notes:

*   **Entrypoint Workaround**: Each service uses an `entrypoint.sh` that launches `/bin/bash`. This keeps the container running and allows Kathará to attach a terminal. The actual application (`python main.py`) is intended to be launched manually or via custom startup scripts.
*   **Startup Reliability**: Script execution via `.startup` can sometimes be inconsistent. Manual execution or checking `docker logs` is often necessary.

## 📊 Performance and Resource Benchmark

This project includes a self-contained benchmark suite to measure the performance (requests/second, latency) and resource consumption (CPU, RAM) of the IIoT microservice pipeline. It runs in a simplified Docker Compose environment, separate from the complex Kathará network topology.

### How the Benchmark Works

The benchmark is orchestrated by a single script, `benchmark/run.sh`. This script automates the entire process:
1.  **Builds and starts** the required services (`dropper`, `decrypter`, etc.) using a dedicated `compose-benchmark.yml` file.
2.  **Starts a background monitoring process** that collects CPU and RAM statistics for all services using `docker stats`.
3.  **Runs the benchmark service**, which uses Apache Benchmark (`ab`) to send a high volume of HTTP requests (both standard and secure) to the `dropper` service.
4.  **Stops all services** and the monitoring process once the tests are complete.
5.  **Analyzes the collected data** and generates a consolidated report in the terminal, showing both performance metrics and resource usage.

### How to Run the Benchmark

All benchmark-related files are located in the `benchmark/` directory, making it completely modular.

1.  **Navigate to the benchmark directory:**
    ```bash
    cd benchmark
    ```

2.  **Run the experiment script:**
    ```bash
    ./run.sh
    ```

Upon completion, a summary report will be printed directly to your console, and raw data files will be saved in the `benchmark/results/` directory.

### Customizing the Benchmark

You can easily customize the benchmark parameters by editing the configuration section at the top of the `benchmark/run.sh` script:

```bash
TOTAL_LOOPS=5       # Number of times each test is repeated
REQUESTS=500        # Number of requests to send in each loop
CONCURRENCY=20      # Number of multiple requests to perform at a time
```

## 🏗️ Project Structure

```
.
├── lab.conf            # Kathará lab configuration (topology, devices)
├── *.startup           # Kathará startup scripts
├── readme.md           # This file
├── compose.yml         # Docker Compose file for building images and local dev
├── benchmark/          # Self-contained benchmark suite
│   ├── run.sh          # Main script to run the benchmark
│   └── ...             # Other benchmark-related files
└── src/                # Source code for the simulation components
    ├── publisher1/     # Production Line 1 simulator (REST client)
    ├── publisher2/     # Production Line 2 simulator
    ├── publisher3/     # Production Line 3 simulator
    ├── dropper/        # Simulates packet loss and routes traffic
    ├── decrypter/      # Decrypts secure payloads
    ├── fault-detector/ # Analyzes data and finds anomalies
    └── digital-twin/   # Logs alerts from the fault detector
```

## 🔍 Composition:

### 🐳 Key Actors:

#### 1. Production Lines (p1, p2, p3)

*   **Implementation:** Python scripts (`src/publisherX/main.py`) that act as **REST clients**.
*   **Function:** Simulates Vibration, Temperature, Quality, and Security sensors and sends all data via **HTTP POST requests** to the `Dropper` service.

#### 2. Dropper

*   **Implementation:** A Flask server that acts as the single entry point for all traffic.
*   **Function:** Simulates network unreliability by dropping packets based on a Poisson distribution. It then routes traffic based on the payload's content: secure data is sent to the `Decrypter`, while standard data is sent to the `Fault Detector`.

#### 3. Decrypter

*   **Implementation:** A Flask-based service.
*   **Function:** Receives encrypted payloads on its `/decrypt` endpoint, decrypts them, and forwards the clear-text data to the `Fault Detector`.

#### 4. Fault Detector

*   **Implementation:** A Flask server that exposes a `/data` endpoint.
*   **Function:** Receives clear-text data from both the `Dropper` and `Decrypter`. It processes the data and triggers alerts based on predefined rules. Alerts are forwarded to the `Digital Twin`.

#### 5. Digital Twin

*   **Implementation:** A Flask server.
*   **Function:** Exposes an `/update` endpoint that receives alerts from the `Fault Detector`. It simulates updating a digital twin's state by logging the alert to a file.

#### 6. Intermediate Routers (int1, int2, int3, int4)

*   A set of simple containers configured by Kathará (`.startup` files) to route traffic between different network segments.

### 📦 Payload Strategy

| Category | Size | Frequency | Use Case | Example Line |
| :--- | :--- | :--- | :--- | :--- |
| **Small** | 1-10 KB | 0.5-2 sec | Real-time monitoring | PRESS-LINE-1 |
| **Medium** | 10-100 KB | 2-5 sec | Historical trends | WELDING-LINE-2 |
| **Large** | 100 KB - 1 MB | 5-10 sec | Big Data/Analytics | PAINT-LINE-3 |

---

## 🔬 Realistic Industrial Metrics

This simulator aims to generate data reflecting real-world industrial conditions. The following sensor configurations provide a baseline.

#### 1. **VibrationSensor** (Predictive Maintenance)

*   **Reference Standard:** Based on principles similar to [ISO 10816-3](https://www.iso.org/standard/78311.html) (Vibrations in industrial machinery).
*   **Simulated Data Points:**
    ```python
    {
      "x": random.uniform(2.0, 15.0),  # Simulated RMS Velocity [mm/s] or Acceleration [m/s²]
      "fft": [random.random() for _ in range(100)],  # Simulated frequency components
      "metadata": {
         "samples": size//1000  # Abstract representation
      }
    }
    ```
*   **Simulator Default Configuration:** Examples use a **2 Hz** reporting frequency with a **"small" (1-10 KB)** payload, including FFT data.
*   **Real-World Context:** Industrial predictive maintenance often employs high sampling rates (e.g., kHz range, like 10-20 kHz) to capture detailed vibration signatures for effective FFT analysis, especially for bearing faults. The simulator's 2 Hz default frequency represents a reporting interval for processed data.
*   **Simulated Alarm Thresholds (Example logic):**
    *   Warning: >8 (unit depends on metric)
    *   Critical: >15 (unit depends on metric)

#### 2. **TemperatureSensor** (Thermal Management)

*   **Reference Standard:** Relevant to principles in [ISO 13732-1](https://www.iso.org/standard/43558.html) (Thermal contact safety).
*   **Simulated Data Points:**
    ```python
    {
      "motor_temp": random.uniform(30.0, 90.0),  # °C
      "bearing_temp": random.normalvariate(60.0, 5.0),  # °C
      "trend": [...]  # Simulated recent data points
    }
    ```
*   **Simulator Default Configuration:** Implied frequencies range from **0.1 Hz (10s interval) to 2 Hz (0.5s interval)**.
*   **Real-World Context:** Temperature reporting intervals vary by application, from seconds for critical processes to minutes for general monitoring. The simulator’s configuration is plausible and can be customized to reflect specific thermal dynamics.
*   **Simulated Critical Thresholds (Example logic):**
    *   Motor: >85°C
    *   Bearings: >70°C

#### 3. **QualitySensor** (Quality Control 4.0)

*   **AI-driven Metrics Concept:** Simulates output from an AI-based quality control system.
*   **Simulated Data Points:**
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
*   **Simulator Default Configuration:** Examples use a **0.1 Hz (10s interval)** frequency with a **"large" (100 KB - 1 MB)** payload.
*   **Real-World Context:** Visual inspection data volumes vary, and edge processing is used to reduce transmitted data. The simulator's configuration abstracts detailed image analysis by using a large payload for a processed "image hash."
*   **Simulated Alert (Example logic):** More than 3 defects per batch triggers an alert.

### 📚 Supporting Sources

To reinforce the design choices of the simulator, the following reputable sources provide validation for each sensor type:

#### 1. Vibration Sensors

*   **TE Connectivity – [Predictive Maintenance with Vibration Sensors](https://www.te.com/en/whitepapers/sensors/predictive-maintenance-with-vibration-sensors.html)**
    Demonstrates how high-frequency sensors can provide actionable data for predictive maintenance.

*   **CBM Connect – [Simplified Vibration Monitoring: ISO 10816‑3 Guidelines](https://www.cbmconnect.com/simplified-vibration-monitoring-iso-10816-3-guidelines/)**
    Offers guidelines on vibration monitoring based on ISO 10816‑3, reinforcing the importance of realistic sensor parameters.

*   **EEWeb – [Sensors in Industry 4.0: Vibration Monitoring](https://www.eeweb.com/sensors-in-industry-4-0-vibration-monitoring/)**
    Provides an extensive overview of the technologies behind industrial vibration sensors within the Industry 4.0 framework.

#### 2. Temperature Sensors

*   **Phase IV Engineering – [Wireless Motor Sensor for Predictive Maintenance](https://www.phaseivengr.com/product/sensors/temperature/wireless-motor-sensor-predictive-maintenance/)**
    Highlights the importance of thermal monitoring for preventive maintenance, even with adjustable reporting intervals.

*   **NCD Store – [Smart Industrial IoT Wireless Vibration Temperature Sensor](https://store.ncd.io/product/smart-industrial-iot-wireless-vibration-temperature-sensor/)**
    Demonstrates the integration of temperature measurement in multi-sensor IoT devices, supporting the simulator’s approach.

*   **Standard - [ISO 13732](https://www.iso.org/standard/43558.html)**
    This internationally recognized standard provides reliable criteria for thermal monitoring, supporting the sensor configuration.

#### 3. Quality Control Sensor

*   **IMechE – [How Condition Monitoring Led the Way to Industry 4.0](https://www.imeche.org/news/news-article/how-condition-monitoring-led-the-way-to-industry-4-0)**
    Discusses the evolution of monitoring systems in industrial settings, including AI-driven quality analysis.

*   **Maintenance and Engineering – [Vibration Monitoring: A Case Study](https://www.maintenanceandengineering.com/2014/01/01/vibration-monitoring-a-case-study/)**
    Presents case studies where advanced monitoring techniques, including image analysis, have improved process reliability.

*   **Analog Devices – [Choosing the Best Vibration Sensor for Wind Turbine Condition Monitoring](https://www.analog.com/en/resources/analog-dialogue/articles/choosing-the-best-vibration-sensor-for-wind-turbine-condition-monitoring.html)**
    Exemplifies the use of advanced sensor technologies and data processing, including image-based methods, in modern industrial applications.

---

## 🔐 Encryption Service

To handle sensitive data securely, the architecture implements an end-to-end encryption flow.

### SecuritySensor (in `publisher1`)

*   Generates security-related events (e.g., access attempts).
*   **Encrypts** the entire JSON payload at the source using the `cryptography` library (Fernet symmetric encryption).
*   Wraps the encrypted data in a new JSON object: `{"source": "secure", "encrypted_payload": "..."}`.
*   Data from this sensor is sent to the `Dropper` service.

### Decrypter Service

*   **Receives** data on its `/decrypt` endpoint from the `Dropper`.
*   **Decrypts** the `encrypted_payload` using the shared symmetric key.
*   **Forwards** the original, clear-text data to the `Fault Detector`'s `/data` endpoint for analysis.

### Fault Detector Updates

*   Detects standard and secure data (after decryption).
*   Applies specialized alert logic for security events (e.g., based on HTTP-style status codes 401, 403, 500).
*   Continues legacy alert processing for standard sensor data.

---

## 🛠️ Customization in Kathará Environment

### 🔧 Customizing Sensor Parameters

1.  Modify the desired JSON configuration file (e.g., `src/publisher1/line1.json`) within your project directory. Change intervals or payload sizes.
2.  Rebuild the specific Docker image if required (often JSON changes do not require a rebuild if mounted correctly, but check your `.startup` and `lab.conf`). If unsure, rebuild:
    ```bash
    docker compose -f local-test.yml build publisher1  # Or the specific service
    ```
3.  Restart the Kathará lab:
    ```bash
    sudo kathara lclean  # Stop the currently running lab
    sudo kathara lstart
    ```

### 🏭 Adding a New Production Line (e.g., Line 4)

1.  **Create Source Files:** Duplicate an existing publisher directory (e.g., copy `src/publisher1` to `src/publisher4`).
2.  **Configure Line 4:** Create/modify `src/publisher4/line4.json` with the desired `line_id` and sensor configuration.
3.  **Update Docker Build:** Add a service definition for `production-line-4` in `local-test.yml` pointing to the `src/publisher4` directory.
4.  **Update Kathará Config:**
    *   Add the new device (e.g., `p4`) to `lab.conf`, connecting it to the appropriate network(s).
    *   Specify the Docker image to use for `p4` (e.g., `src-production-line-4`).
    *   Create a `p4.startup` script to launch the application inside the container.
5.  **Build the New Image:**
    ```bash
    docker compose compose.yml build production-line-4  # Use the service name from compose.yml
    ```
6.  **Launch the Updated Lab:**
    ```bash
    sudo kathara lstart
    ```

### Other Modifications

*   **Custom Alert Rules:** Modify `src/fault-detector/main.py` and rebuild/restart.
*   **New Sensor Types:** Create new Python classes in `src/publisherX/sensors/`, register them, update JSON configs, rebuild images, and restart the lab.
*   **Network Topology:** Modify `lab.conf` to change connections, add routers, or introduce network impairments (using Kathará's advanced features).

---

## 🏭 Conclusion: IIoT Simulation in a Network Context

This Kathará-adapted simulator provides a powerful environment for:

*   Testing IIoT architectures with **RESTful services** within realistic or complex network topologies.
*   Analyzing the impact of network conditions (latency, packet loss—if simulated via Kathará) on **HTTP-based** communication.
*   Developing and validating network security policies for IIoT systems.
*   Training cybersecurity and network professionals on IIoT scenarios.