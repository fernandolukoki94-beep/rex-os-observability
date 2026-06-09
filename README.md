# REX-OS v3.0 - Distributed Infrastructure Observability System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

REX-OS is a lightweight, distributed monitoring and telemetry platform designed to monitor server health across multiple nodes in real-time. Built specifically for Linux environments, it provides system administrators with immediate infrastructure visibility through a modern terminal-based dashboard.

## 🎯 Key Features

- **Real-time Monitoring**: Live infrastructure visibility across multiple nodes
- **Lightweight Agent**: Minimal resource footprint for distributed deployment
- **RESTful API**: Centralized Flask-based command center
- **Rich Terminal UI**: Beautiful, interactive dashboard for system administrators
- **Linux Native**: Optimized for Linux and Termux environments
- **Scalable Architecture**: Decoupled components for fault tolerance

## 🏗️ System Architecture

The platform is split into decoupled components to ensure scalability and fault tolerance:

### 1. **REX Core (API Service)**
A Flask-based RESTful API that acts as the central command center:
- Receives telemetry data from multiple nodes
- Processes logs and events
- Manages live server states
- Exposes REST endpoints for data querying

### 2. **REX Agent**
A lightweight telemetry collector deployed on target machines:
- Gathers local hardware metrics (CPU, Memory, Disk, Network)
- Dispatches data via secure HTTP payloads to Core
- Minimal resource consumption
- Configurable collection intervals

### 3. **Rich TUI Operations (Terminal UI)**
A real-time, terminal-based dashboard built with Python's Rich library:
- System administrator visibility without external tools
- Interactive navigation and drill-down capabilities
- Responsive and performant display updates

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.9+, Flask 2.3+ |
| Data Transport | REST APIs (JSON payloads) |
| Terminal UI | Rich 13.6+ |
| Environment | Linux, Termux |
| Testing | pytest, pytest-cov |
| Code Quality | black, flake8, mypy |

## 📋 Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Linux or Termux environment
- Network connectivity between nodes (for distributed setup)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/fernandolukoki94-beep/rex-os-observability.git
cd rex-os-observability
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Core Engine
```bash
cd core
python rex_core.py
```

The API will be available at `http://localhost:5000`

### 5. Start the Agent (on target machines)
```bash
cd agent
python rex_agent.py --core-url http://<core-host>:5000
```

### 6. Launch the Terminal UI
```bash
cd tui
python rex_dashboard.py --api-url http://localhost:5000
```

## 📚 Project Structure

```
rex-os-observability/
├── core/                    # Central API service (Flask)
│   └── rex_core.py         # Core application
├── agent/                   # Lightweight telemetry agent
│   └── rex_agent.py        # Agent application
├── tui/                     # Terminal UI dashboard
│   └── rex_dashboard.py    # Dashboard application
├── tests/                   # Unit tests
│   ├── test_core.py
│   ├── test_agent.py
│   └── test_tui.py
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── INSTALLATION.md
│   └── CONTRIBUTING.md
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License
└── README.md               # This file
```

## 🔧 Configuration

### Core Configuration
Set environment variables or create a `config.yaml`:
```python
FLASK_ENV=production
FLASK_DEBUG=False
API_PORT=5000
LOG_LEVEL=INFO
```

### Agent Configuration
```python
CORE_URL=http://localhost:5000
AGENT_NAME=node-01
COLLECTION_INTERVAL=5  # seconds
LOG_LEVEL=INFO
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/nodes` | List all monitored nodes |
| GET | `/api/nodes/<node_id>/metrics` | Get node metrics |
| POST | `/api/telemetry` | Receive telemetry data (Agent → Core) |
| GET | `/api/logs` | Retrieve system logs |

*For detailed API documentation, see [docs/API.md](docs/API.md)*

## 🧪 Testing

Run all tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_core.py -v
```

Run with detailed output:
```bash
pytest -vv --tb=short
```

## 💻 Development

### Code Style
We use `black` for code formatting:
```bash
black .
```

### Linting
Check code with `flake8`:
```bash
flake8 . --max-line-length=100
```

### Type Checking
Run `mypy` for type checking:
```bash
mypy . --ignore-missing-imports
```

### Pre-commit Checks
```bash
black . && flake8 . && mypy . && pytest
```

## 📖 Documentation

For more detailed documentation, see:
- [Architecture Guide](docs/ARCHITECTURE.md) - System design and component interaction
- [API Documentation](docs/API.md) - Complete API reference
- [Installation Guide](docs/INSTALLATION.md) - Detailed installation steps
- [Contributing Guide](docs/CONTRIBUTING.md) - Development guidelines

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For detailed contributing guidelines, see [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 📊 Monitoring Examples

### Single Node Monitoring
```python
from rex_agent import REXAgent

agent = REXAgent(core_url="http://localhost:5000")
agent.start()
```

### Multi-Node Dashboard
```bash
python rex_dashboard.py --api-url http://localhost:5000
```

The dashboard will display all connected nodes with real-time metrics updates.

## 🐛 Troubleshooting

**Agent cannot connect to Core:**
- Verify Core is running: `curl http://localhost:5000/api/health`
- Check network connectivity between machines
- Ensure firewall allows port 5000

**High CPU usage from Agent:**
- Increase `COLLECTION_INTERVAL` in agent config
- Check for large log files being processed

**Dashboard not updating:**
- Verify Core API is responding
- Check agent connectivity status in Core logs
- Restart both Core and Agent

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Fernando Lukoki** - [GitHub Profile](https://github.com/fernandolukoki94-beep)

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) for the API
- [Rich](https://rich.readthedocs.io/) for beautiful terminal UI
- [pytest](https://pytest.org/) for testing framework

## 📞 Support

For issues, questions, or suggestions:
- Open an [GitHub Issue](https://github.com/fernandolukoki94-beep/rex-os-observability/issues)
- Check existing [Discussions](https://github.com/fernandolukoki94-beep/rex-os-observability/discussions)

---

**Status**: Active Development 🚀

Made with ❤️ by Fernando Lukoki
