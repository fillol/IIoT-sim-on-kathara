![Industry 4.0](https://img.shields.io/badge/-Industry%204.0-4CAF50?logo=industry&logoColor=FFFF00)
![Kathará](https://img.shields.io/badge/-Kathara-blue?logo=linux&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)
![GitHub License](https://img.shields.io/badge/License-MIT-ff69b4)

# Industrial IoT Simulator on Kathará (Light Version)

This is the **lightweight** version of the IIoT Simulator. It does not contain the source code and relies entirely on pre-built Docker images hosted on Docker Hub. It is designed for researchers who want to quickly test the network topology and interactions without managing the build process.

## 📜 How it Works

This simulator emulates an Industrial IoT setup with three production lines. The logic is identical to the full version, but images are pulled directly from Docker Hub (`fillol/iiot-kathara-*`).

The data flows through:
`Publisher` → `Dropper` → `Decrypter` (if secure) → `Fault Detector` → `Digital Twin`.

## 🚀 Usage

### Prerequisites

*   [Kathará](https://github.com/KatharaFramework/Kathara) installed.
*   Docker (to run the images).

### ⚡ Quick Start

1.  **Clone this branch:**
    ```bash
    git clone -b light https://github.com/fillol/IIoT-sim-on-Kathara.git
    cd IIoT-sim-on-Kathara
    ```

2.  **Launch the Lab:**
    ```bash
    sudo kathara lstart --noterminals
    ```

3.  **Monitor Logs:**
    To see the production line 1 in action:
    ```bash
    sudo kathara connect --logs p1
    ```

4.  **Clean up:**
    ```bash
    sudo kathara lclean
    ```

---

### 🛠️ Manual Execution

If you want to interact with the containers:

1.  **Start Kathará with terminals:**
    ```bash
    sudo kathara lstart
    ```

2.  **Start Producers:**
    In the `p1`, `p2`, or `p3` terminals, run:
    ```bash
    python main.py
    ```
    *(The core services like Dropper and Fault Detector start automatically).*

## 🏗️ Project Structure

```
.
├── lab.conf            # Kathará lab configuration (points to Docker Hub images)
├── *.startup           # Kathará startup scripts
└── README.md           # This file
```

---
*For the full source code and benchmarking tools, please refer to the `main` branch.*
