import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";


const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const legacySource = readFileSync(path.join(ROOT, "api", "legacy-app.js"), "utf8");
const researchSource = readFileSync(path.join(ROOT, "api", "routes", "research.js"), "utf8");
const expectedLegacyRoutes = ["/api/health", "/api/value-scores", "/api/stock/:code", "/api/phases"];
const expectedResearchRoutes = ["/api/dashboard", "/api/discoveries", "/api/news", "/api/news/:id"];

test("legacy GET route response contracts remain present after bootstrap split", () => {
  for (const route of expectedLegacyRoutes) {
    assert.match(legacySource, new RegExp(`app\\.get\\(["']${route.replaceAll("/", "\\/").replace(":", "\\:")}["']`));
  }
  for (const route of expectedResearchRoutes) {
    assert.match(researchSource, new RegExp(`router\\.get\\(["']${route.replaceAll("/", "\\/").replace(":", "\\:")}["']`));
  }
  assert.match(legacySource, /app\.use\(createResearchRouter\(\{ repository: researchRepository \}\)\)/);
  assert.doesNotMatch(legacySource, /app\.get\(["']\/api\/(?:dashboard|discoveries|news)/);
});

test("server bootstrap stays small and delegates application assembly", () => {
  const serverSource = readFileSync(path.join(ROOT, "api", "server.js"), "utf8");
  assert.ok(serverSource.split(/\r?\n/).length < 100);
  assert.match(serverSource, /import \{ app, DB_PATH \} from "\.\/app\.js"/);
});
