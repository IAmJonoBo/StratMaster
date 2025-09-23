# Real-time Collaboration Service

Phase 2 implementation of real-time collaboration on debate outcomes.

## Features

- WebSocket-based real-time communication
- Session management for collaborative reviews
- Role-based permissions
- Consensus mechanisms
- Integration with constitutional debate system

## Usage

```bash
# Start collaboration service
uvicorn collaboration.main:app --host 0.0.0.0 --port 8084

# Connect via WebSocket
ws://localhost:8084/ws/collaboration
```

## Configuration

Configuration is loaded from `configs/collaboration/real_time.yaml`.

## API Endpoints

- `GET /health` - Health check
- `GET /sessions` - List active sessions  
- `POST /sessions` - Create new collaboration session
- `WebSocket /ws/collaboration` - Real-time collaboration

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/
```