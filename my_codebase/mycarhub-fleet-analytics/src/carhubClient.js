import fs from "fs";
import path from "path";
import url from "url";

const DEFAULT_ROOT = path.resolve(
  path.dirname(url.fileURLToPath(import.meta.url)),
  "../../mycarhub/src"
);

const CARHUB_ROOT = process.env.CARHUB_ROOT
  ? path.resolve(process.env.CARHUB_ROOT)
  : DEFAULT_ROOT;

const SOURCE_FILES = {
  db: path.join(CARHUB_ROOT, "db.json"),
  carsPage: path.join(CARHUB_ROOT, "Cars.js"),
  context: path.join(CARHUB_ROOT, "UserInformationContext.js"),
};
const ASSETS_DIR = path.join(CARHUB_ROOT, "assets", "cars");

function readFileSafe(target) {
  try {
    return fs.readFileSync(target, "utf-8");
  } catch (err) {
    console.warn(`[carhubClient] Failed to read ${target}: ${err.message}`);
    return null;
  }
}

export function loadInventory() {
  const payload = readFileSafe(SOURCE_FILES.db);
  let vehicles = [];
  let source = SOURCE_FILES.db;

  if (payload) {
    try {
      const json = JSON.parse(payload);
      vehicles = Array.isArray(json?.cars)
        ? json.cars
        : Array.isArray(json)
        ? json
        : [];
    } catch (err) {
      console.warn(`[carhubClient] Invalid JSON in db.json: ${err.message}`);
    }
  }

  if (!vehicles.length) {
    vehicles = loadAssetsInventory();
    source = ASSETS_DIR;
  }

  return { vehicles, source };
}

export function loadPersonaMetadata() {
  const content = readFileSafe(SOURCE_FILES.context);
  if (!content) {
    return { persona: null, source: SOURCE_FILES.context };
  }

  const personaMatch = content.match(/const\\s+defaultUser\\s*=\\s*({[\\s\\S]+?});/);
  const persona = personaMatch ? personaMatch[1].trim() : null;

  return {
    persona,
    source: SOURCE_FILES.context,
  };
}

export function listReferencedComponents() {
  const content = readFileSafe(SOURCE_FILES.carsPage);
  if (!content) {
    return { components: [], source: SOURCE_FILES.carsPage };
  }

  const matches = content.match(/<([A-Z][A-Za-z0-9]+)/g) || [];
  const components = [...new Set(matches.map((m) => m.replace("<", "")))];
  return { components, source: SOURCE_FILES.carsPage };
}

export function getCarhubRoot() {
  return CARHUB_ROOT;
}

function loadAssetsInventory() {
  if (!fs.existsSync(ASSETS_DIR)) {
    return [];
  }

  const files = fs.readdirSync(ASSETS_DIR).filter((file) => {
    const ext = path.extname(file).toLowerCase();
    return [".png", ".jpg", ".jpeg", ".avif", ".webp"].includes(ext);
  });

  return files.map((file) => {
    const { make, model, variant } = parseAssetName(file);
    return {
      id: `${make}-${model}-${variant}`,
      make: toTitle(make),
      model: toTitle(model),
      trim: toTitle(variant),
      image: `assets/cars/${file}`,
      range: mockRangeFor(make, model),
      price: mockPrice(make),
      battery: mockBattery(variant),
    };
  });
}

function parseAssetName(filename) {
  const base = path.basename(filename, path.extname(filename));
  const segments = base.split("-");
  const make = segments[0] || "unknown";
  const model = segments[1] || "vehicle";
  const variant = segments.slice(2).join("-") || "base";
  return { make, model, variant };
}

function toTitle(value) {
  return value
    .split(/[-_ ]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function mockRangeFor(make, model) {
  const seed = (make.charCodeAt(0) + model.charCodeAt(0)) % 100;
  return 250 + seed;
}

function mockPrice(make) {
  const base = 30000 + make.charCodeAt(0) * 500;
  return Math.round(base / 100) * 100;
}

function mockBattery(variant) {
  if (variant.includes("sport") || variant.includes("performance")) {
    return "95 kWh";
  }
  if (variant.includes("camry") || variant.includes("accord")) {
    return "70 kWh";
  }
  return "80 kWh";
}

