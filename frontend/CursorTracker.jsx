// CursorTracker.jsx
import React, { useEffect, useRef, useState } from "react";

const CursorTracker = ({ socket }) => {
  const canvasRef = useRef(null);
  const [cursors, setCursors] = useState({});
  const throttleTimeoutRef = useRef(null);
  const THROTTLE_MS = 33; // ~30 FPS

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleMouseMove = (e) => {
      if (throttleTimeoutRef.current) return;

      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Send cursor position to server (throttled)
      socket.send({
        type: "cursor_move",
        x,
        y,
      });

      // Set throttle timer
      throttleTimeoutRef.current = setTimeout(() => {
        throttleTimeoutRef.current = null;
      }, THROTTLE_MS);
    };

    canvas.addEventListener("mousemove", handleMouseMove);

    return () => {
      canvas.removeEventListener("mousemove", handleMouseMove);
      if (throttleTimeoutRef.current) {
        clearTimeout(throttleTimeoutRef.current);
      }
    };
  }, [socket]);

  // Listen for cursor updates from other users
  const handleWebSocketMessage = (message) => {
    if (message.type === "cursor_update") {
      const { user_id, user_color, x, y } = message.data;
      setCursors((prev) => ({
        ...prev,
        [user_id]: { x, y, color: user_color },
      }));
    }
  };

  useEffect(() => {
    socket.onMessage = handleWebSocketMessage;
  }, [socket]);

  // Render remote cursors on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    Object.entries(cursors).forEach(([userId, { x, y, color }]) => {
      // Draw cursor pointer
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fill();

      // Draw outline
      ctx.strokeStyle = "#000";
      ctx.lineWidth = 1;
      ctx.stroke();
    });
  }, [cursors]);

  return (
    <canvas
      ref={canvasRef}
      width={window.innerWidth}
      height={window.innerHeight}
      style={{ position: "fixed", top: 0, left: 0, pointerEvents: "none" }}
    />
  );
};

export default CursorTracker;
