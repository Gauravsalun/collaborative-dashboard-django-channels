# System Architecture

## Overview

This document describes the complete architecture of the Real-Time Collaborative Dashboard.

## Components

### Backend Stack
- **Django 4.2** — Web framework
- **Django Channels** — WebSocket support
- **ASGI (Daphne)** — Async application server
- **Redis** — Message broker & presence tracking
- **PostgreSQL** — Primary database

### Frontend Stack
- **React.js** — UI framework
- **WebSocket API** — Real-time communication
- **Canvas API** — Cursor rendering

## Data Flow

### 1. Cursor Tracking Flow

User moves mouse
↓
CursorTracker throttles (33ms)
↓
WebSocket sends cursor_move message
↓
Django Consumer receives message
↓
group_send() broadcasts to all clients
↓
Canvas renders remote cursors


### 2. Task Update Flow (Optimistic)
User drags task
↓
UI updates immediately (optimistic)
↓
WebSocket sends task_move
↓
Django Consumer validates + updates DB
↓
Broadcasts new state to all clients
↓
Clients confirm (or revert on conflict)


### 3. Chat Message Flow

User sends message
↓
WebSocket sends chat_message
↓
Django Consumer saves to DB
↓
group_send() broadcasts to room
↓
All clients receive message
↓
Chat widget appends to message list


## Scaling Considerations

- **Redis Cluster** for horizontal scaling
- **Sticky sessions** with load balancer
- **Message expiry** to prevent memory bloat
- **Room partitioning** for large deployments

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production setup.
