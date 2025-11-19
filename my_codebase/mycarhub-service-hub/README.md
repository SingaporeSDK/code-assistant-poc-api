# MyCarHub Service Hub

A third repository that simulates **service plans, pricing rules, and workshop dependencies** tying together:

- The **MyCarHub UI** (`../mycarhub`), where vehicle metadata originates.
- The **Fleet Analytics** service (`../mycarhub-fleet-analytics`), which exposes graph-ready insights.

This hub ingests data from both repos and emits `data/service_packages.json`, which is then consumed by `mycarhub-fleet-analytics` to enrich the global dependency graph with **ServicePackage** nodes.

## Folder Layout

```
my_codebase/
├── mycarhub/
├── mycarhub-fleet-analytics/
└── mycarhub-service-hub/   <-- this repo
    ├── data/
    │   └── service_packages.json   # generated artifact
    └── src/
        ├── serviceComposer.js      # business logic
        └── index.js                # CLI/runner
```

## Usage

```bash
cd my_codebase/mycarhub-service-hub
npm install
npm run build:data
```

This will:

1. Load `../mycarhub/src/db.json` to inspect the inventory.
2. Import `buildFleetGraph()` from `../mycarhub-fleet-analytics/src/fleetAggregator.js` to capture graph node IDs.
3. Generate realistic service bundles (pricing tiers, maintenance windows) that reference:
   - Vehicle IDs and UI components (Cars.js, CarCard).
   - Analytics node IDs (e.g., `carhub:vehicle:5b2a`).
4. Emit `data/service_packages.json`, which is automatically read by the analytics service to add `ServicePackage` nodes and edges (`SERVICES`, `SURFACES_IN`, `ALIGN_WITH`).

## Data Contract

Each service package contains:

```jsonc
{
  "id": "svc-5b2a",
  "vehicleId": "5b2a",
  "package": "Hybrid Essentials",
  "price": 899,
  "cadence": "biannual",
  "workshop": "North Loop Service Center",
  "dependencies": {
    "vehicleNode": "carhub:vehicle:5b2a",
    "uiComponent": "src/CarCard.js",
    "analyticsSource": "carhub:fleet:XXXXXX"
  }
}
```

Downstream consumers (e.g., GraphRAG pipelines) can now reason about connections between **UI components**, **analytics insights**, and **service operations**.

## Ideas for Extension

- Add pricing history or telemetry costs and surface them as separate node types.
- Derive service demand forecasts from fleet stats (avg range, persona data).
- Feed the manifest into Neo4j/Neptune to run multi-hop reasoning (“Which UI elements depend on a package that targets fleet trims with low battery health?”).

