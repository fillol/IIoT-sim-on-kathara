# IIoT Microservices Benchmark Suite

## Performance Results

The following results were obtained using the default test parameters. For a detailed explanation of the test modes (`Isolated` vs. `Pipeline`) and metrics, please refer to the sections below.

**Default Parameters:**
*   **Requests per Profile:** 100
*   **Concurrent Users:** 2
*   **Test Loops:** 3 (metrics are the average of 3 runs)

### Idle State Consumption
Baseline resource consumption of each microservice at rest.

| Microservice    | Idle CPU (%) | Idle RAM (MiB) |
| :-------------- | :----------- | :------------- |
| DigitalTwin     | 0.0100       | 20.6300        |
| Decrypter       | 0.0100       | 334.1000       |
| Dropper         | 0.0100       | 32.1100        |
| FaultDetector   | 0.0100       | 1089.5360      |

### Isolated Performance (Raw Service Cost)
Performance of each service in **Isolated Mode**, measuring its intrinsic logic and network error handling cost.

| Profile                 | Avg. CPU (%) | Avg. RAM (MiB) | Avg. Latency (ms) | Std. Dev (ms) | Throughput (Mbps) |
| :---------------------- | :----------- | :------------- | :---------------- | :------------ | :---------------- |
| DigitalTwin             | 9.8500       | 20.7600        | 1.9033            | 0.3410        | 1.8734            |
| Decrypter               | 41.7167      | 336.4670       | 12.3900           | 4.5614        | 0.5916            |
| Dropper (Standard)      | 35.1200      | 32.8700        | 11.4600           | 3.9332        | 0.2246            |
| Dropper (Secure)        | 26.5233      | 33.3000        | 10.0000           | 4.5704        | 0.7204            |
| Dropper (Secure Image)  | 32.1733      | 33.4733        | 10.8667           | 4.4911        | 20.1074           |
| FaultDetector (Standard)| 31.1933      | 1090.5600      | 9.7267            | 3.7447        | 0.3636            |
| FaultDetector (Image)   | 81.2767      | 1096.0200      | 18.0067           | 5.7998        | 8.3473            |

### Pipeline Performance (End-to-End Behavior)
Performance of each service in **Pipeline Mode**, reflecting real-world behavior including interactions with dependencies.

| Profile                 | Avg. CPU (%) | Avg. RAM (MiB) | Avg. Latency (ms) | Std. Dev (ms) | Throughput (Mbps) |
| :---------------------- | :----------- | :------------- | :---------------- | :------------ | :---------------- |
| DigitalTwin*            | 9.8500       | 20.7600        | 1.9033            | 0.3410        | 1.8734            |
| Decrypter*              | 41.7167      | 336.4670       | 12.3900           | 4.5614        | 0.5916            |
| Dropper (Standard)      | 25.4800      | 33.2633        | 4.7700            | 2.5382        | 0.5248            |
| Dropper (Secure)        | 29.2100      | 32.8800        | 10.0067           | 2.0552        | 0.7129            |
| Dropper (Secure Image)  | 19.2700      | 34.0767        | 21.5433           | 4.4729        | 9.4209            |
| FaultDetector (Standard)| 30.9433      | 1090.5600      | 7.3000            | 1.0074        | 0.4779            |
| FaultDetector (Image)   | 100.5300     | 1095.0000      | 13.4333           | 1.6724        | 11.1815           |

<small>\* *Services that have no upstream dependencies are only tested in Isolated mode.*</small>


## Benchmark Design

### Overview
This directory contains a benchmark suite designed to profile the IIoT microservices architecture. The `run.sh` script automates the entire process, providing consistent and reproducible results.

### Rationale for Dual-Mode Testing
The suite introduces a dual-mode test for services with dependencies to distinguish between:
1.  **Isolated performance**: Measuring the pure response time of the service's logic.
2.  **Pipeline performance**: Measuring the service's behavior within the complete system.

This distinction is necessary because testing a service without its dependencies active can "dirty" the CPU and latency metrics with the overhead of network errors. The dual-mode approach provides a more complete and realistic view of performance.

### Test Modes Explained
*   **Isolated Mode (`--no-deps`)**: Starts only the container for the service under test. Outbound network calls fail, and the measured latency is the sum of `[Internal Processing Time] + [Network Exception Handling Time]`.
*   **Pipeline Mode**: Starts the service under test and all of its dependencies. Network calls succeed, and the measured latency is the sum of `[Internal Processing Time] + [Wait Time for Dependency Response]`.

---

## How to Run the Benchmark

### Prerequisites
The `run.sh` script relies on the following tools:
*   Docker & Docker Compose
*   Python 3
*   `awk`, `grep`, `curl`, `ab`, `bc`

The following Python libraries are used for payload generation and data analysis:
*   `numpy`
*   `cryptography`

### Execution
1.  **Navigate to the Directory:**
    ```bash
    cd path/to/project/benchmark
    ```

2.  **Make the Script Executable:**
    ```bash
    chmod +x run.sh
    ```

3.  **Run the Suite:**
    ```bash
    ./run.sh
    ```
    The script will execute all test profiles and print the final summary to the console. Raw data for each run is saved in the `results/` directory.