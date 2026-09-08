# Real-Time Collaborative Dashboard

A production-grade architecture for building real-time collaborative applications using Django Channels, WebSockets, React, and Redis.

**Features:**
- 🎯 **Live Cursor Tracking** — High-frequency, throttled cursor position broadcasting
- 📋 **Instant Task Management** — Drag-and-drop with optimistic UI updates + DB sync
- 💬 **Real-Time Chat** — Persistent messaging with presence tracking
- 🔐 **Authentication** — JWT/Session-based with Django AuthMiddlewareStack
- ⚡ **High Performance** — Redis message broker, connection pooling, message throttling

---

## 🏗️ Quick Architecture Overview


---

## 📚 Documentation

- **[Architecture & Design](./docs/ARCHITECTURE.md)** — System overview, data flow, sequence diagrams
- **[Setup Guide](./docs/SETUP.md)** — Local development environment
- **[WebSocket Protocol](./docs/API_PROTOCOL.md)** — Message types, event format
- **[Deployment](./docs/DEPLOYMENT.md)** — Production setup with Kubernetes/Docker

---

## 🚀 Quick Start

### Backend Setup

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
python manage.py migrate

# Start ASGI server
daphne -b 0.0.0.0 -p 8000 myproject.asgi:application
```

### Frontend Setup

```bash
# Install React dependencies
npm install

# Start dev server
npm start
```

---

## 📋 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React.js, WebSocket API |
| **Backend** | Django, Django Channels, ASGI |
| **Real-Time** | WebSockets, Redis (`channels-redis`) |
| **Database** | PostgreSQL/MySQL |
| **Message Broker** | Redis |
| **Deployment** | Docker, Docker Compose, Kubernetes |

---

## 🔧 Key Components

### Backend
- `consumers.py` — AsyncWebsocketConsumer with cursor, task, chat handlers
- `models.py` — Room, Task, ChatMessage models
- `asgi.py` — ASGI application with Channels routing
- `settings.py` — Django + Channels configuration

### Frontend
- `websocketManager.js` — WebSocket abstraction with reconnection logic
- `CursorTracker.jsx` — Live cursor rendering component
- `TaskCard.jsx` — Optimistic UI updates for drag-and-drop
- `ChatWidget.jsx` — Real-time messaging interface

---

## 📊 Performance Features

✅ **Cursor Throttling** — 33ms interval (~30 FPS)
✅ **No Cursor Persistence** — Ephemeral Redis broadcast only
✅ **Optimistic Updates** — Instant UI feedback for tasks
✅ **Select-for-Update Locking** — Prevents concurrent edit conflicts
✅ **Indexed Queries** — Fast chat message retrieval
✅ **Presence Tracking** — Redis TTL auto-cleanup
✅ **Message Queueing** — Handles offline reconnects gracefully

---

## 🛠️ Customization

### Throttle Cursor Frequency
Edit `CursorTracker.jsx`:
```javascript
const THROTTLE_MS = 33; // Change to 50, 100, etc.
```

### Change Chat Message Limit
Edit `consumers.py`:
```python
if not message_text or len(message_text) > 2000:  # Change 2000
```

### Adjust Reconnection Strategy
Edit `websocketManager.js`:
```javascript
this.maxReconnectAttempts = 5;      // Max retry count
this.reconnectDelay = 1000;         // Initial delay (ms)
```

---

## 🚀 Scaling Strategies

1. **Horizontal Scaling** — Use Redis Cluster for channel layer
2. **Load Balancing** — Sticky sessions with Nginx
3. **Message Batching** — Bundle cursor events if needed
4. **Room Partitioning** — Separate Redis databases per region

---

## 📝 License

MIT License — Feel free to use in personal & commercial projects

---

## 💡 Contributing

Pull requests welcome! Please open an issue first to discuss changes.

---

## 📧 Questions?

Create an issue in the repository for architecture questions, bugs, or feature requests.
