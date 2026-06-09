# REX-OS API Documentation

## Overview

REX-OS provides a comprehensive REST API for managing nodes and retrieving real-time telemetry data. This guide covers all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://<core-host>:5000/api
```

## Authentication

Currently, no authentication is required. In production, implement:
- API Key authentication
- JWT Bearer tokens
- OAuth 2.0

## Response Format

All responses are in JSON format with consistent structure:

### Success Response (2xx)
```json
{
  "status": "success",
  "data": {},
  "message": "Operation completed successfully"
}
```

### Error Response (4xx, 5xx)
```json
{
  "status": "error",
  "error": "ERROR_CODE",
  "message": "Human-readable error message"
}
```

## Endpoints

### 1. Health Check

**Endpoint:** `GET /api/health`

**Description:** Check Core service health and connectivity status.

**Example:**
```bash
curl -X GET "http://localhost:5000/api/health"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "service": "healthy",
    "uptime_seconds": 3600,
    "nodes_connected": 5,
    "agents_active": 5
  }
}
```

---

### 2. List All Nodes

**Endpoint:** `GET /api/nodes`

**Query Parameters:**
- `status` - Filter: `online`, `offline`, `degraded`
- `limit` - Results per page (default: 100)
- `offset` - Pagination offset

**Example:**
```bash
curl "http://localhost:5000/api/nodes?status=online&limit=50"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "nodes": [
      {
        "id": "node-001",
        "name": "server-1",
        "status": "online",
        "last_seen": 1623456789
      }
    ],
    "total": 2
  }
}
```

---

### 3. Get Node Details

**Endpoint:** `GET /api/nodes/<node_id>`

**Example:**
```bash
curl "http://localhost:5000/api/nodes/node-001"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "node-001",
    "name": "server-1",
    "status": "online",
    "agent_version": "3.0.0",
    "os": "Linux"
  }
}
```

---

### 4. Get Node Metrics

**Endpoint:** `GET /api/nodes/<node_id>/metrics`

**Example:**
```bash
curl "http://localhost:5000/api/nodes/node-001/metrics"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "node_id": "node-001",
    "timestamp": 1623456789,
    "metrics": {
      "cpu_percent": 45.2,
      "memory_percent": 62.8,
      "disk_percent": 78.5
    }
  }
}
```

---

### 5. Receive Telemetry

**Endpoint:** `POST /api/telemetry`

**Description:** Agents push metrics to Core.

**Example:**
```bash
curl -X POST "http://localhost:5000/api/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node-001",
    "agent_version": "3.0.0",
    "timestamp": 1623456789,
    "metrics": {
      "cpu_percent": 45.2,
      "memory_percent": 62.8
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "node_id": "node-001",
    "accepted": true
  }
}
```

---

### 6. Get Logs

**Endpoint:** `GET /api/logs`

**Query Parameters:**
- `level` - `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `limit` - Max results (default: 100)

**Example:**
```bash
curl "http://localhost:5000/api/logs?level=ERROR"
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_REQUEST` | 400 | Invalid parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Temporarily unavailable |

## Rate Limiting

Recommended limits (not enforced by default):
- 1000 requests/min per client
- Implement via API Gateway in production

## Examples

### Monitor Node CPU
```bash
#!/bin/bash
NODE_ID="node-001"
while true; do
  curl -s "http://localhost:5000/api/nodes/$NODE_ID/metrics" | \
    jq '.data.metrics.cpu_percent'
  sleep 5
done
```

### Export Nodes
```bash
curl -s "http://localhost:5000/api/nodes" | \
  jq '.data.nodes' > nodes.json
```

---

**For more info, see [ARCHITECTURE.md](ARCHITECTURE.md)**
