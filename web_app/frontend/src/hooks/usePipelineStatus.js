import { useState, useEffect } from 'react';
import { getStatus } from '../services/api';

export function usePipelineStatus(intervalMs = 3000) {
  const [statusState, setStatusState] = useState({
    status: 'idle',
    current_step: null,
    progress_percent: 0,
    is_running: false,
    error_message: null,
  });

  useEffect(() => {
    let isMounted = true;

    async function fetchStatus() {
      try {
        const data = await getStatus();
        if (isMounted) {
          setStatusState(data);
        }
      } catch (e) {
        console.error('Failed to poll status', e);
      }
    }

    fetchStatus();
    const interval = setInterval(fetchStatus, intervalMs);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [intervalMs]);

  return statusState;
}
