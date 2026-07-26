import { useState, useEffect } from 'react';

export function useSSELogs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const eventSource = new EventSource('/api/stream_logs');

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((prev) => [...prev, data.message]);
      } catch (e) {
        setLogs((prev) => [...prev, event.data]);
      }
    };

    eventSource.onerror = () => {
      // EventSource auto-reconnects
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const clearLogs = () => setLogs([]);

  return { logs, clearLogs };
}
