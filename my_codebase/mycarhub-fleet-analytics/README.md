# MyCarHub Fleet Analytics

This folder represents a **second codebase** that depends on the original `mycarhub` React application. It simulates a lightweight Fastify service that:

1. Reads UI configuration artifacts (e.g., `db.json`, `Cars.js`) from the primary repo.
2. Builds derived fleet insights (average range, battery health, trim distribution).
3. Exposes a telemetry ingestion endpoint that the UI could call.
4. Emits graph-friendly metadata describing cross-repo relationships you can later feed into a GraphRAG pipeline.

```
my_codebase/
├── mycarhub/                # Existing React UI
└── mycarhub-fleet-analytics/ # New dependency-aware analytics service
```

## Key Cross-Repo Touchpoints

- `src/carhubClient.js` imports JSON/config files directly from `../mycarhub/src` and auto-builds a synthetic dataset by scanning `../mycarhub/src/assets/cars` when `db.json` is empty. This ensures the analytics API always has demo data.
- `src/fleetAggregator.js` annotates each insight node with `upstream.file` so you can stitch a graph of dependencies between repos.
- The Fastify API (`src/index.js`) exposes `/graph/nodes` to retrieve the cross-repo entities.

## Usage

```bash
cd my_codebase/mycarhub-fleet-analytics
npm install
npm run dev
```

Environment variables:

| Name | Default | Purpose |
|------|---------|---------|
| `CARHUB_ROOT` | `../mycarhub/src` | Resolves shared source assets |
| `PORT` | `5001` | Port for the Fastify server |
| `GRAPH_NAMESPACE` | `carhub` | Namespace prefix when emitting graph nodes |

With both repos indexed, you can:

1. Embed each codebase separately (`--collection carhub_ui`, `--collection carhub_fleet`).
2. Generate metadata edges from `/graph/nodes`.
3. Feed nodes + embeddings into your GraphRAG experiment to answer questions spanning both repos.

