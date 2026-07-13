import { app, DB_PATH } from "./app.js";


const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;
const HOST = process.env.HOST || "127.0.0.1";

const server = app.listen(PORT, HOST, () => {
  console.log("============================================================");
  console.log("  SMR local research workbench started");
  console.log(`  Database: ${DB_PATH}`);
  console.log(`  Local URL: http://${HOST}:${PORT}`);
  console.log("============================================================");
});

server.on("error", (error) => {
  console.error(`API server failed: ${error.message}`);
  process.exitCode = 1;
});

export * from "./legacy-app.js";
