# IIoT Microservices Benchmark Suite

## Overview

This directory contains a comprehensive benchmark suite designed to profile the performance and resource consumption of the IIoT microservices architecture.
The primary script, `run.sh`, automates the entire testing lifecycle, enabling consistent and reproducible performance evaluation.


## Baseline Performance Results

**Test Parameters:**
-   **Requests per Profile:** 100
-   **Concurrent Users:** 2
-   **Test Loops:** 3 (metrics are averaged across all loops)

| Profile                  | Avg. CPU (%) | Avg. RAM (MiB) | Avg. Latency (ms) | Std. Dev (ms) | Variance (ms^2) |
| :----------------------- | :----------- | :------------- | :---------------- | :------------ | :-------------- |
| DigitalTwin              | 21.9633      | 26.1667        | 3.9133            | 1.4834        | 2.2889          |
| Decrypter                | 47.3067      | 348.0330       | 9.1067            | 2.1020        | 4.4858          |
| Dropper_StandardPath     | 42.6933      | 41.6633        | 8.4833            | 1.7417        | 3.0388          |
| Dropper_SecurePath       | 38.5167      | 35.0933        | 17.2267           | 3.6103        | 13.7011         |
| Dropper_SecureImagePath  | 15.9667      | 34.8767        | 35.7067           | 6.0277        | 36.6203         |
| FaultDetector_Standard   | 53.5433      | 1090.9000      | 11.2100           | 2.4627        | 6.1438          |
| FaultDetector_Image      | 91.3733      | 1097.3800      | 20.7267           | 3.6467        | 13.4279         |

---

## How to Run the Benchmark

### Prerequisites

Before running the benchmark, ensure the following are installed on your system:
-   Docker
-   Docker Compose
-   Python 3 (with the `numpy` and `cryptography` libraries)
-   The complete project repository must be cloned locally.

### Execution Steps

1.  **Navigate to the Directory:**
    Open your terminal and change into this directory:
    ```bash
    cd path/to/your/project/benchmark
    ```

2.  **Make the Script Executable (One-time setup):**
    ```bash
    chmod +x run.sh
    ```

3.  **Run the Full Benchmark Suite:**
    To execute all predefined test profiles with the default parameters, simply run the script:
    ```bash
    ./run.sh
    ```
    The script will perform all setup, run each test profile, and print a final summary table to the console. Raw data for each run will be saved in the `results/` directory for deeper analysis.
