# REX-OS v3.0 - Distributed Infrastructure Observability System

REX-OS is a lightweight, distributed monitoring and telemetry platform designed to monitor server health across multiple nodes in real-time. Built specifically for Linux environments, it showcases architectural principles of microservices, asynchronous data processing, and smart threshold alerting.

## 🏗️ System Architecture

The platform is split into decoupled components to ensure scalability and fault tolerance:

1. **REX Core (API Service):** A Flask-based RESTful API that acts as the central command center, receiving telemetry data from multiple nodes, processing logs, and managing live server states.
2. **REX Agent:** A lightweight telemetry collector deployed on target machines that gathers local hardware metrics and dispatches them via secure HTTP payloads to the Core.
3. **Rich TUI Operations (Terminal UI):** A real-time, terminal-based dashboard built with Python's Rich library, providing system administrators with immediate infrastructure visibility without overhead.

## 🛠️ Tech Stack
- **Backend:** Python, Flask
- **Data Transport:** REST APIs (JSON payloads)
- **Environment:** Linux / Termux

## 🚀 How to Run Locally

### 1. Start the Core Engine
```bash
cd core
python rex_core.py

