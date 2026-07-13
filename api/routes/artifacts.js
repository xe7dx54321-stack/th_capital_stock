import { existsSync } from "fs";
import path from "path";
import express from "express";


const ALLOWED_MIME_TYPES = new Set([
  "text/markdown",
  "application/json",
  "text/html",
  "text/plain",
]);

function resolveArtifactPath(artifact, allowedRoots) {
  if (!artifact || path.isAbsolute(artifact.relative_path)) return null;
  const rootIndex = Number(artifact.metadata?.artifact_root_index ?? 0);
  const root = allowedRoots[rootIndex];
  if (!root) return null;
  const resolvedRoot = path.resolve(root);
  const candidate = path.resolve(resolvedRoot, artifact.relative_path);
  if (candidate !== resolvedRoot && !candidate.startsWith(`${resolvedRoot}${path.sep}`)) return null;
  return candidate;
}

export function createArtifactRouter({ repository, allowedRoots }) {
  const router = express.Router();
  const roots = allowedRoots.map((root) => path.resolve(root));
  router.get("/api/artifacts/:id", (req, res) => {
    const artifact = repository.getArtifact(req.params.id);
    if (!artifact) {
      res.status(404).json({ error: "artifact not found" });
      return;
    }
    const artifactPath = resolveArtifactPath(artifact, roots);
    if (!artifactPath || !existsSync(artifactPath)) {
      res.status(404).json({ error: "artifact file not found" });
      return;
    }
    if (!ALLOWED_MIME_TYPES.has(artifact.mime_type)) {
      res.status(415).json({ error: "artifact MIME type is not allowed" });
      return;
    }
    res.type(artifact.mime_type);
    res.sendFile(artifactPath);
  });
  return router;
}

export { resolveArtifactPath };
