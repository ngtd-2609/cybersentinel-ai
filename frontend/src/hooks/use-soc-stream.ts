"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

export function useSocStream() {
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const source = new EventSource("/api/realtime");
    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    source.addEventListener("soc-update", () => {
      void queryClient.invalidateQueries({ queryKey: ["detection-events"] });
      void queryClient.invalidateQueries({ queryKey: ["incidents"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    });
    return () => source.close();
  }, [queryClient]);

  return connected;
}
