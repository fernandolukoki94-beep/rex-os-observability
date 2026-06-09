# REX-OS Architecture Guide

## System Overview

REX-OS v3.0 is a distributed infrastructure observability platform composed of three main components that work together seamlessly to provide real-time monitoring across multiple nodes.

```
┌─────────────────────────────────────────────────────────────┐
│                      REX-OS v3.0                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  REX Core    │◄───┤  REX Agent   │    │  REX Agent   │ │
│  │  (API)       │    │  (Node 1)    │    │  (Node 2)    │ │
│  │              │    │              │    │              │ │
│  │ - Receives   │    │ - Collects   │    │ - Collects   │ │
│  │ - Processes  │    │ - Sends data │    │ - Sends data │ │
│  │ - Stores     │    │   to Core    │    │   to Core    │ │
│  │ - Serves API │    │              │    │              │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         ▲                                                   │
│         │                                                   │
│         └─────────────────────────────────────────────────┐ │
│                                                           │ │
│                                                    ┌──────▼─┐
│                                                    │ REX TUI│
│                                                    │ (Dash) │
│                                                    │        │
│                                                    │ - View │
│                                                    │ - Real │
│                                                    │ - Time │
│                                                    └────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. REX Core (Central API Service)

**Location:** `/core/rex_core.py`

**Responsibilities:**
- Acts as the central hub for all telemetry data
- Receives metrics from distributed agents
- Processes and aggregates data
- Manages application state
- Provides REST API endpoints
- Handles inter-node communication

**Key Features:**
- Flask-based REST API
- Stateful node management
- Real-time data aggregation
- Concurrent request handling
- Error logging and reporting

**Dependencies:**
- Flask 2.3+
- Werkzeug 2.3+
- Python 3.9+

### 2. REX Agent (Telemetry Collector)

**Location:** `/agent/rex_agent.py`

**Responsibilities:**
- Deployed on each monitored node
- Collects system metrics (CPU, Memory, Disk, Network)
- Sends telemetry to Core via HTTP
- Handles configuration locally
- Manages collection intervals
- Implements graceful shutdown

**Key Features:**
- Lightweight footprint
- Configurable collection intervals
- Fault-tolerant communication
- Local error handling
- Secure HTTP communication

**Dependencies:**
- requests 2.31+
- psutil 5.9+ (for system metrics)
- Python 3.9+

### 3. Rich TUI Dashboard (Terminal UI)

**Location:** `/tui/rex_dashboard.py`

**Responsibilities:**
- Provides real-time terminal interface
- Queries Core API for metrics
- Renders interactive dashboard
- Handles user input
- Updates metrics in real-time
- Displays node status and alerts

**Key Features:**
- Rich library for beautiful rendering
- Real-time metrics updates
- Interactive navigation
- Color-coded status indicators
- Responsive layout

**Dependencies:**
- Rich 13.6+
- requests 2.31+
- Python 3.9+

## Data Flow

### 1. Metric Collection Flow

```
Agent Node 1          Agent Node 2          Agent Node N
    │                     │                      │
    ├─ Collect CPU        ├─ Collect CPU        ├─ Collect CPU
    ├─ Collect Memory     ├─ Collect Memory     ├─ Collect Memory
    ├─ Collect Disk       ├─ Collect Disk       ├─ Collect Disk
    └─ Collect Network    └─ Collect Network    └─ Collect Network
    │                     │                      │
    └─────────────────────┼──────────────────────┘
                          │
                    HTTP POST /api/telemetry
                          │
                          ▼
                    REX Core API
                    (Processing)
                          │
                    Store in Memory
                          │
                    Available via API
```

### 2. Query Flow

```
REX Dashboard
    │
    ├─ Queries /api/nodes
    ├─ Queries /api/nodes/<id>/metrics
    ├─ Queries /api/health
    │
    ▼
REX Core API (Request Handler)
    │
    ├─ Retrieve data from state
    ├─ Format response (JSON)
    │
    ▼
Return to Dashboard
    │
    └─ Render in Terminal UI
```

## API Endpoints

### Core Health
- **Endpoint:** `GET /api/health`
- **Response:** System health status
- **Example:**
  ```json
  {
    "status": "healthy",
    "uptime": 3600,
    "nodes_connected": 3
  }
  ```

### Node Management
- **Endpoint:** `GET /api/nodes`
- **Response:** List of all registered nodes
- **Example:**
  ```json
  {
    "nodes": [
      {
        "id": "node-001",
        "name": "server-1",
        "status": "online"
      }
    ]
  }
  ```

### Metrics Retrieval
- **Endpoint:** `GET /api/nodes/<node_id>/metrics`
- **Response:** Current metrics for specific node
- **Example:**
  ```json
  {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "disk_percent": 78.5,
    "network_in": 1024000,
    "network_out": 512000
  }
  ```

### Telemetry Ingestion
- **Endpoint:** `POST /api/telemetry`
- **Body:** Metric data from agents
- **Example:**
  ```json
  {
    "node_id": "node-001",
    "timestamp": 1623456789,
    "metrics": {
      "cpu_percent": 45.2,
      "memory_percent": 62.8
    }
  }
  ```

## Data Models

### Node Model
```python
{
  "id": "string",           # Unique node identifier
  "name": "string",         # Human-readable name
  "status": "online|offline", # Current status
  "last_seen": "timestamp", # Last telemetry timestamp
  "region": "string",       # Geographic/logical region
  "tags": ["string"]        # Custom tags
}
```

### Metrics Model
```python
{
  "node_id": "string",
  "timestamp": "timestamp",
  "cpu_percent": "float",      # 0-100
  "memory_percent": "float",   # 0-100
  "disk_percent": "float",     # 0-100
  "network_in": "integer",     # bytes/s
  "network_out": "integer",    # bytes/s
  "process_count": "integer",
  "load_average": "float"
}
```

## Communication Protocol

### Agent → Core Communication
- **Protocol:** HTTP/HTTPS
- **Method:** POST
- **Endpoint:** `/api/telemetry`
- **Interval:** Configurable (default: 5 seconds)
- **Timeout:** 30 seconds
- **Retry:** 3 attempts with exponential backoff

### Dashboard → Core Communication
- **Protocol:** HTTP/HTTPS
- **Method:** GET
- **Endpoints:** `/api/*`
- **Polling Interval:** 1-2 seconds (configurable)
- **Timeout:** 10 seconds

## Scalability Considerations

### Horizontal Scaling
- **Agent Deployment:** Each node runs one agent instance
- **Multiple Cores:** Can deploy multiple Core instances with load balancer
- **Database Layer:** Should be added for persistence in production

### Performance
- **Metric Collection:** ~50-100ms per agent
- **API Response:** <100ms for typical queries
- **Dashboard Update:** 1-2 second refresh cycle
- **Memory Usage:** ~100MB base + 1MB per 100 nodes

## Security Considerations

### Authentication
- Implement JWT tokens for API access
- Use environment variables for API keys
- Support mutual TLS for agent-to-core communication

### Network
- HTTPS should be enforced in production
- Network segmentation for agent communication
- Firewall rules to restrict API access

### Data Protection
- Encrypt sensitive configuration
- Sanitize metrics data in logs
- Regular security audits recommended

## Deployment Architecture

### Single Node Deployment
```
Node 1
├── REX Core
├── REX Agent
└── REX Dashboard
```

### Multi-Node Deployment
```
Core Server
├── REX Core (primary)
└── Load Balancer

Agent Nodes
├── Node 1: REX Agent
├── Node 2: REX Agent
├── Node N: REX Agent

Dashboard Server
└── REX Dashboard
```

### Production Deployment
```
Load Balancer
├── Core Instance 1
├── Core Instance 2
└── Core Instance 3
    │
    ├─ Database (PostgreSQL/MongoDB)
    ├─ Cache Layer (Redis)
    └─ Message Queue (RabbitMQ/Kafka)

Agent Nodes (100+)
└─ REX Agent instances

Dashboard Servers
├── Dashboard Instance 1
├── Dashboard Instance 2
└── Monitoring Dashboard
```

## Development Workflow

### Setting Up Development Environment
1. Clone repository
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables from `.env.example`
5. Run individual components:
   - Core: `python core/rex_core.py`
   - Agent: `python agent/rex_agent.py`
   - Dashboard: `python tui/rex_dashboard.py`

### Testing Architecture
- Unit tests for each component
- Integration tests for API communication
- Performance tests for metrics collection
- Load tests for multi-node scenarios

---

For implementation details, see the individual component documentation.
