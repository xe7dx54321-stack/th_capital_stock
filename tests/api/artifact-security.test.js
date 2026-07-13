import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";

import { resolveArtifactPath } from "../../api/routes/artifacts.js";


test("artifact resolver rejects absolute and traversal paths", () => {
  const root = path.resolve("safe-artifacts");
  assert.equal(
    resolveArtifactPath({ relative_path: "../secret.txt", metadata: { artifact_root_index: 0 } }, [root]),
    null,
  );
  assert.equal(
    resolveArtifactPath({ relative_path: path.resolve("secret.txt"), metadata: { artifact_root_index: 0 } }, [root]),
    null,
  );
  assert.equal(
    resolveArtifactPath({ relative_path: "run/report.md", metadata: { artifact_root_index: 99 } }, [root]),
    null,
  );
  assert.equal(
    resolveArtifactPath({ relative_path: "run/report.md", metadata: { artifact_root_index: 0 } }, [root]),
    path.join(root, "run", "report.md"),
  );
});
