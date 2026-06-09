# Installation Guide

## Prerequisites

### System Requirements
- **OS:** Linux (Ubuntu, Debian, CentOS, RHEL) or Termux
- **Python:** 3.9 or higher
- **RAM:** Minimum 512MB (1GB+ recommended)
- **Disk:** 500MB free space
- **Network:** TCP ports 5000 (Core), configurable for agents

### Supported Platforms

| Platform | Version | Support |
|----------|---------|---------|
| Ubuntu | 18.04+ | ✅ Fully Supported |
| Debian | 10+ | ✅ Fully Supported |
| CentOS | 7+ | ✅ Fully Supported |
| RHEL | 7+ | ✅ Fully Supported |
| Termux | Latest | ✅ Supported |
| macOS | 10.14+ | ⚠️ Partial |
| Windows | 10/11 | ⚠️ WSL2 Required |

## Step 1: Clone Repository

```bash
git clone https://github.com/fernandolukoki94-beep/rex-os-observability.git
cd rex-os-observability
```

## Step 2: Create Python Virtual Environment

### On Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

### On Windows (WSL2)
```bash
python3 -m venv venv
source venv/Scripts/activate
```

### On Termux
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import flask; import rich; print('✅ All dependencies installed')"
```

## Step 4: Environment Configuration

### Create .env file from template
```bash
cp .env.example .env
```

### Edit .env with your settings
```bash
nano .env
```

**Example .env for Development:**
```ini
FLASK_ENV=development
FLASK_DEBUG=True
API_PORT=5000
LOG_LEVEL=DEBUG
```

**Example .env for Production:**
```ini
FLASK_ENV=production
FLASK_DEBUG=False
API_PORT=5000
LOG_LEVEL=INFO
```

## Step 5: Create Required Directories

```bash
mkdir -p logs
mkdir -p data
mkdir -p config
chmod 755 logs data config
```

## Installation Variants

### Variant A: Full Stack (Core + Agent + Dashboard)

**Single Machine Development Setup:**

```bash
# Terminal 1: Start Core
cd core
python rex_core.py

# Terminal 2: Start Agent
cd agent
python rex_agent.py --core-url http://localhost:5000

# Terminal 3: Start Dashboard
cd tui
python rex_dashboard.py --api-url http://localhost:5000
```

### Variant B: Core Only

**For Central Monitoring Server:**

```bash
cd core
python rex_core.py
```

### Variant C: Agent Only

**For Individual Node Monitoring:**

```bash
cd agent
python rex_agent.py \
  --core-url http://<core-server>:5000 \
  --agent-name node-01
```

### Variant D: Dashboard Only

**For Remote Dashboard:**

```bash
cd tui
python rex_dashboard.py --api-url http://<core-server>:5000
```

## Verification

### Test Core API

```bash
curl http://localhost:5000/api/health
```

### Test Agent Connection

```bash
curl http://localhost:5000/api/nodes
```

## Troubleshooting

### Port Already in Use

```bash
lsof -i :5000
kill -9 <PID>
```

### Python Version Issues

```bash
python3 -m venv venv
python3 -m pip install -r requirements.txt
```

### Missing Dependencies

```bash
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

## Next Steps

1. Configure monitoring
2. Launch dashboard
3. Set up agents
4. Run tests

---

**Last Updated:** 2026-06-09
**Version:** 3.0.0
