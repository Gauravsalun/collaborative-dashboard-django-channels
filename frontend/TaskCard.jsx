// TaskCard.jsx
import React, { useState } from "react";

const TaskCard = ({ task, socket, onLocalUpdate }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [optimisticTask, setOptimisticTask] = useState(task);
  const [isLoading, setIsLoading] = useState(false);

  const handleDragStart = (e) => {
    setIsDragging(true);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDrop = (newStatus) => {
    setIsDragging(false);

    // 1. OPTIMISTIC UPDATE: Update UI immediately
    const updatedTask = { ...optimisticTask, status: newStatus };
    setOptimisticTask(updatedTask);
    onLocalUpdate(updatedTask);

    // 2. ASYNC DB SYNC: Send to backend
    setIsLoading(true);
    socket.send({
      type: "task_move",
      task_id: task.id,
      new_status: newStatus,
      position: { x: task.x, y: task.y },
    });

    // After response, loading clears automatically via message handler
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      style={{
        padding: "12px",
        backgroundColor: optimisticTask.status === "completed" ? "#e8f5e9" : "#fff",
        border: "1px solid #ddd",
        borderRadius: "4px",
        opacity: isLoading ? 0.6 : 1,
        transition: "opacity 0.2s",
      }}
    >
      <h4>{optimisticTask.title}</h4>
      <p>Status: {optimisticTask.status}</p>
      {isLoading && <span style={{ fontSize: "12px", color: "#666" }}>Syncing...</span>}
    </div>
  );
};

export default TaskCard;
