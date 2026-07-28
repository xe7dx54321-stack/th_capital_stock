const endpoint = process.env.SMR_CHAT_STREAM_URL
  || "http://127.0.0.1:3000/api/chat/workflow/stream";
const message = process.argv.slice(2).join(" ").trim()
  || "请对德科立做一个深度分析";
const timeoutMs = Math.max(30_000, Number(process.env.SMR_CHAT_STREAM_TIMEOUT_MS) || 600_000);
const startedAt = Date.now();

const response = await fetch(endpoint, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  },
  body: JSON.stringify({ message }),
  signal: AbortSignal.timeout(timeoutMs),
});

console.log("HEADERS", response.status, `${Date.now() - startedAt}ms`, response.headers.get("content-type"));
if (!response.ok || !response.body) {
  console.error(await response.text());
  process.exitCode = 1;
} else {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let lastCompleted = -1;
  let finalSeen = false;

  const consumeFrame = (frame) => {
    let eventName = "message";
    const dataLines = [];
    for (const line of frame.split(/\r?\n/)) {
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
    }
    if (dataLines.length === 0) return;
    const payload = JSON.parse(dataLines.join("\n"));
    if (eventName === "research_progress") {
      const execution = payload.researchExecution;
      if (execution.completedStages === lastCompleted) return;
      lastCompleted = execution.completedStages;
      const activeStage = execution.groups
        .flatMap((group) => group.stages)
        .find((stage) => stage.status === "running");
      console.log(
        "PROGRESS",
        `${Date.now() - startedAt}ms`,
        `${execution.completedStages}/${execution.totalStages}`,
        activeStage?.label || execution.status,
        payload.run_id,
      );
    }
    if (eventName === "error") {
      console.error("ERROR", payload.error, payload.run_id || "");
      process.exitCode = 1;
    }
    if (eventName === "result") {
      finalSeen = true;
      console.log(
        "RESULT",
        `${Date.now() - startedAt}ms`,
        payload.status,
        payload.taskType,
        `report_chars=${String(payload.response || "").length}`,
        payload.run_id || "",
        payload.governed_run_id || "",
        payload.data?.reportQualityGate?.synthesis_mode || "",
      );
    }
  };

  while (true) {
    const part = await reader.read();
    buffer += decoder.decode(part.value, { stream: !part.done });
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() || "";
    for (const frame of frames) {
      if (frame.trim()) consumeFrame(frame);
    }
    if (part.done) break;
  }
  if (buffer.trim()) consumeFrame(buffer);

  console.log("DONE", `final=${finalSeen}`, `completed=${lastCompleted}`);
  if (!finalSeen || lastCompleted !== 30) process.exitCode = 1;
}
