import fs from "fs";
import path from "path";
import url from "url";

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const CARHUB_ROOT = path.resolve(__dirname, "../../mycarhub/src");
const OUTPUT_DIR = path.resolve(__dirname, "../data");

const DB_PATH = path.join(CARHUB_ROOT, "db.json");
const DEFAULT_UI_COMPONENT = "src/Cars.js";
const DEFAULT_CARD_COMPONENT = "src/CarCard.js";

function loadCars() {
  const data = JSON.parse(fs.readFileSync(DB_PATH, "utf-8"));
  return Array.isArray(data?.cars) ? data.cars : [];
}

export function composeServicePackages() {
  const vehicles = loadCars();

  const packages = vehicles.map((vehicle, idx) =>
    buildPackage(vehicle, idx)
  );

  return {
    generatedAt: new Date().toISOString(),
    upstream: {
      carhubDb: DB_PATH,
      analyticsGraphNamespace: "carhub",
    },
    packages,
  };
}

function buildPackage(vehicle, idx) {
  const tiers = ["Hybrid Essentials", "Performance Max", "Battery Guardian"];
  const cadence = ["quarterly", "biannual", "annual"];
  const workshop = ["North Loop Service Center", "Downtown EV Lab", "Mobile Crew"];

  const tier = tiers[idx % tiers.length];
  const planCadence = cadence[idx % cadence.length];
  const facility = workshop[idx % workshop.length];

  return {
    id: `svc-${vehicle.id || idx}`,
    vehicleId: vehicle.id,
    package: tier,
    price: estimatePrice(vehicle, tier),
    cadence: planCadence,
    workshop: facility,
    dependencies: {
      uiComponent: DEFAULT_UI_COMPONENT,
      cardComponent: DEFAULT_CARD_COMPONENT,
      personaFile: "src/UserInformationContext.js",
    },
    serviceTasks: buildTasks(vehicle),
    source: path.join("data", "service_packages.json"),
  };
}

function estimatePrice(vehicle, tier) {
  const base = Number(vehicle.price) || 20000;
  const multiplier =
    tier === "Performance Max" ? 0.06 : tier === "Battery Guardian" ? 0.08 : 0.04;
  return Math.round(base * multiplier);
}

function buildTasks(vehicle) {
  return [
    `Inspect ${vehicle.make} ${vehicle.modelNumber} battery health`,
    "Update telematics firmware",
    "Run ADAS calibration",
    "Generate report for MyCarHub dashboard",
  ];
}

export function writeServicePackages(payload) {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  const target = path.join(OUTPUT_DIR, "service_packages.json");
  fs.writeFileSync(target, JSON.stringify(payload, null, 2));
  console.log(`✓ Service packages written to ${target}`);
}

