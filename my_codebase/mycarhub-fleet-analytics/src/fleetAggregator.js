import fs from "fs";
import path from "path";
import url from "url";
import { nanoid } from "nanoid";
import {
  loadInventory,
  loadPersonaMetadata,
  listReferencedComponents,
  getCarhubRoot,
} from "./carhubClient.js";

const GRAPH_NAMESPACE = process.env.GRAPH_NAMESPACE || "carhub";
const SERVICE_HUB_DATA = path.resolve(
  path.dirname(url.fileURLToPath(import.meta.url)),
  "../../mycarhub-service-hub/data/service_packages.json"
);

export function buildFleetGraph() {
  const graph = {
    nodes: [],
    edges: [],
    metadata: {
      namespace: GRAPH_NAMESPACE,
      carhubRoot: getCarhubRoot(),
      generatedAt: new Date().toISOString(),
    },
  };

  const inventory = loadInventory();
  const persona = loadPersonaMetadata();
  const components = listReferencedComponents();

  const fleetNodeId = `${GRAPH_NAMESPACE}:fleet:${nanoid(6)}`;
  graph.nodes.push({
    id: fleetNodeId,
    type: "FleetInventory",
    label: "MyCarHub Inventory",
    source: inventory.source,
    stats: summarizeVehicles(inventory.vehicles),
  });

  const vehicleNodeMap = new Map();

  inventory.vehicles.forEach((vehicle) => {
    const vehicleNodeId = `${GRAPH_NAMESPACE}:vehicle:${vehicle.id || nanoid(4)}`;
    graph.nodes.push({
      id: vehicleNodeId,
      type: "Vehicle",
      label: `${vehicle.make} ${vehicle.model}`,
      payload: pickVehicleFields(vehicle),
      source: inventory.source,
    });

    if (vehicle.id) {
      vehicleNodeMap.set(vehicle.id, vehicleNodeId);
    }

    graph.edges.push({
      id: `${vehicleNodeId}->inventory`,
      from: vehicleNodeId,
      to: fleetNodeId,
      relation: "PART_OF",
    });
  });

  if (persona.persona) {
    const personaNodeId = `${GRAPH_NAMESPACE}:persona:${nanoid(5)}`;
    graph.nodes.push({
      id: personaNodeId,
      type: "Persona",
      label: "Default User Persona",
      source: persona.source,
      personaSnippet: persona.persona,
    });
    graph.edges.push({
      id: `${personaNodeId}->fleet`,
      from: personaNodeId,
      to: fleetNodeId,
      relation: "TARGETS",
    });
  }

  let uiNodeId = null;
  if (components.components.length > 0) {
    uiNodeId = `${GRAPH_NAMESPACE}:ui:${nanoid(5)}`;
    graph.nodes.push({
      id: uiNodeId,
      type: "UIComponentSet",
      label: "Cars.js Component Tree",
      components: components.components,
      source: components.source,
    });
    graph.edges.push({
      id: `${uiNodeId}->fleet`,
      from: uiNodeId,
      to: fleetNodeId,
      relation: "VISUALIZES",
    });
  }

  integrateServicePackages(graph, {
    fleetNodeId,
    uiNodeId,
    vehicleNodeMap,
  });

  return graph;
}

export function summarizeVehicles(vehicles) {
  if (!vehicles.length) {
    return { total: 0, avgRange: 0, trims: [] };
  }

  const totalRange = vehicles.reduce(
    (sum, car) => sum + (Number(car.range) || 0),
    0
  );
  const trims = Array.from(
    vehicles.reduce((set, car) => set.add(car.trim || "standard"), new Set())
  );

  return {
    total: vehicles.length,
    avgRange: Math.round(totalRange / vehicles.length),
    trims,
  };
}

function pickVehicleFields(vehicle) {
  const allowed = [
    "id",
    "make",
    "model",
    "trim",
    "range",
    "price",
    "battery",
    "image",
  ];
  return allowed.reduce((acc, field) => {
    if (vehicle[field] !== undefined) {
      acc[field] = vehicle[field];
    }
    return acc;
  }, {});
}

function integrateServicePackages(graph, context) {
  const packages = loadServicePackages();
  packages.forEach((pkg) => {
    const nodeId = `${GRAPH_NAMESPACE}:service:${pkg.id}`;
    graph.nodes.push({
      id: nodeId,
      type: "ServicePackage",
      label: `${pkg.package} (${pkg.vehicleId})`,
      price: pkg.price,
      cadence: pkg.cadence,
      workshop: pkg.workshop,
      dependencies: pkg.dependencies,
      source: pkg.source,
    });

    const vehicleNodeId = context.vehicleNodeMap.get(pkg.vehicleId);
    if (vehicleNodeId) {
      graph.edges.push({
        id: `${nodeId}->${vehicleNodeId}`,
        from: nodeId,
        to: vehicleNodeId,
        relation: "SERVICES",
      });
    }

    if (context.uiNodeId) {
      graph.edges.push({
        id: `${nodeId}->ui`,
        from: nodeId,
        to: context.uiNodeId,
        relation: "SURFACES_IN",
      });
    }

    graph.edges.push({
      id: `${nodeId}->fleet`,
      from: nodeId,
      to: context.fleetNodeId,
      relation: "ALIGN_WITH",
    });
  });
}

function loadServicePackages() {
  if (!fs.existsSync(SERVICE_HUB_DATA)) {
    return [];
  }

  try {
    const payload = JSON.parse(fs.readFileSync(SERVICE_HUB_DATA, "utf-8"));
    return Array.isArray(payload?.packages) ? payload.packages : [];
  } catch (err) {
    console.warn(`[fleetAggregator] Failed to load service packages: ${err.message}`);
    return [];
  }
}

