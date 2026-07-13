const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled", "waiting_review"]);


export function streamWorkflowEvents(req, res, repository) {
  const runId = req.params.id;
  if (!repository.getRun(runId)) {
    res.status(404).json({ error: "workflow run not found" });
    return;
  }
  let after = Math.max(0, Number(req.query.after) || 0);
  let heartbeatAt = Date.now();
  res.status(200);
  res.setHeader("Content-Type", "text/event-stream; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();

  const flush = () => {
    const events = repository.listEvents(runId, after);
    for (const event of events) {
      after = event.sequence;
      res.write(`id: ${event.sequence}\n`);
      res.write(`event: ${event.event_type}\n`);
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    }
    const run = repository.getRun(runId);
    if (run && TERMINAL_STATUSES.has(run.status) && events.length === 0) {
      clearInterval(timer);
      res.end();
      return;
    }
    if (Date.now() - heartbeatAt >= 15000) {
      res.write(": heartbeat\n\n");
      heartbeatAt = Date.now();
    }
  };
  const timer = setInterval(flush, 500);
  req.on("close", () => clearInterval(timer));
  flush();
}
