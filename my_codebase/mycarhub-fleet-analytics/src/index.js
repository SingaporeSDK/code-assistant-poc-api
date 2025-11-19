import Fastify from "fastify";
import cors from "@fastify/cors";
import chalk from "chalk";
import { buildFleetGraph, summarizeVehicles } from "./fleetAggregator.js";
import { loadInventory } from "./carhubClient.js";

const PORT = Number(process.env.PORT || 5001);
const fastify = Fastify({ logger: false });

await fastify.register(cors, {
  origin: true,
});

fastify.get("/health", async () => {
  const { vehicles } = loadInventory();
  return {
    status: "ok",
    inventoryCount: vehicles.length,
  };
});

fastify.get("/graph/nodes", async () => {
  const graph = buildFleetGraph();
  return graph;
});

fastify.get("/insights/range", async () => {
  const { vehicles } = loadInventory();
  return summarizeVehicles(vehicles);
});

fastify.post("/telemetry", async (request, reply) => {
  const event = {
    id: request.body?.eventId ?? crypto.randomUUID(),
    occurredAt: new Date().toISOString(),
    payload: request.body || {},
  };
  fastify.log.info({ event }, "Received telemetry");
  return reply.code(202).send({ accepted: true, event });
});

fastify.listen({ port: PORT, host: "0.0.0.0" }).then(() => {
  console.log(
    chalk.greenBright(
      `MyCarHub Fleet Analytics listening on http://localhost:${PORT}`
    )
  );
  console.log(
    chalk.blue(
      "Graph endpoint ready at /graph/nodes (combine with MyCarHub embeddings for GraphRAG experiments)."
    )
  );
});

