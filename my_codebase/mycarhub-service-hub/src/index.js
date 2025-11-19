#!/usr/bin/env node
import { composeServicePackages, writeServicePackages } from "./serviceComposer.js";

async function main() {
  console.log("🔧 MyCarHub Service Hub: composing service packages...");
  const payload = composeServicePackages();
  writeServicePackages(payload);
  console.log(
    `Linked ${payload.packages.length} service packages to namespace ${payload.upstream.analyticsGraphNamespace}.`
  );
}

main().catch((err) => {
  console.error("Service hub generation failed:", err);
  process.exit(1);
});

