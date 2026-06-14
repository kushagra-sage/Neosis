"use client";
import { useCallback, useEffect, useRef } from "react";
import { buildWsUrl, getAccessToken } from "@/lib/api/client";
import { useInquiryStream } from "@/stores/inquiry";
import type { WsEvent } from "@/types/api";

/**
 * Drives the streaming inquiry over WS /ws/inquiry.
 *
 * Protocol (mirrors the backend docstring exactly):
 *   client → {"question": "..."}
 *   server → {"type":"stage","stage":...} | {"type":"token","content":...}
 *          | {"type":"dossier","items":[...]} | {"type":"critic","scores":{...}}
 *          | {"type":"done","inquiry_id":...} | {"type":"error","message":...}
 */
export function useInquirySocket(workspaceId?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const stream = useInquiryStream();

  const submit = useCallback(
    (question: string) => {
      const q = question.trim();
      if (!q || stream.isStreaming) return;

      const token = getAccessToken();
      if (!token) {
        stream.fail("Not authenticated — please sign in again.");
        return;
      }

      stream.begin(q);

      const params = new URLSearchParams({ token });
      if (workspaceId) params.set("workspace_id", workspaceId);

      const ws = new WebSocket(buildWsUrl(`/ws/inquiry?${params.toString()}`));
      wsRef.current = ws;

      ws.onopen = () => ws.send(JSON.stringify({ question: q }));

      ws.onmessage = (evt: MessageEvent<string>) => {
        let msg: WsEvent;
        try {
          msg = JSON.parse(evt.data) as WsEvent;
        } catch {
          return;
        }
        switch (msg.type) {
          case "stage":
            stream.pushStage(msg.stage);
            break;
          case "token":
            stream.pushToken(msg.content);
            break;
          case "dossier":
            stream.setDossier(msg.items);
            break;
          case "critic":
            stream.setCritic(msg.scores);
            break;
          case "done":
            stream.finish(msg.inquiry_id);
            ws.close();
            break;
          case "error":
            stream.fail(
              typeof msg.message === "string"
                ? msg.message
                : JSON.stringify(msg.message),
            );
            ws.close();
            break;
        }
      };

      ws.onerror = () => {
        stream.fail("Connection error — check that the backend is running.");
      };

      ws.onclose = () => {
        if (useInquiryStream.getState().isStreaming) stream.stop();
      };
    },
    [workspaceId, stream],
  );

  const cancel = useCallback(() => {
    wsRef.current?.close();
    stream.stop();
  }, [stream]);

  // Close any live socket on unmount.
  useEffect(() => () => wsRef.current?.close(), []);

  return { submit, cancel };
}
