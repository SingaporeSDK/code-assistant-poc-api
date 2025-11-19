import rawData from "../db.json";

let assetContext;
try {
  assetContext = require.context("../assets/cars", false, /\.(png|jpe?g|avif|webp)$/);
} catch (err) {
  assetContext = null;
}

const jsonCars = normalizeFromJson(rawData);
const assetCars = jsonCars.length ? [] : buildFromAssets();
const initialCars = jsonCars.length ? jsonCars : assetCars;

export function getInitialCars() {
  return initialCars;
}

export function normalizeNewCar(input) {
  return enrichCar(
    {
      ...input,
      images: typeof input.images === "string" ? input.images.split(",").map((img) => img.trim()) : input.images,
      features: typeof input.features === "string" ? input.features.split(",").map((f) => f.trim()) : input.features,
    },
    input.id || `custom-${Date.now()}`
  );
}

export function stripAssetPrefix(filename) {
  if (!filename) return null;
  return filename.replace(/^\.?\/?(assets\/cars\/)?/, "");
}

function normalizeFromJson(data) {
  const entries = Array.isArray(data?.cars) ? data.cars : Array.isArray(data) ? data : [];
  return entries.map((car, idx) => enrichCar(car, car.id || `seed-${idx}`));
}

function buildFromAssets() {
  if (!assetContext) return [];
  return assetContext.keys().map((key, idx) => {
    const fileName = key.replace("./", "");
    const meta = parseAssetMeta(fileName);
    return enrichCar(
      {
        id: `asset-${idx}`,
        modelNumber: meta.code,
        productName: meta.title,
        make: meta.make,
        category: meta.category,
        description: `Showroom photo for ${meta.title}.`,
        price: meta.price,
        milesRun: meta.miles,
        year: meta.year,
        images: [fileName],
        features: meta.features,
        status: idx % 4 === 0 ? "sold" : "available",
      },
      `asset-${idx}`
    );
  });
}

function enrichCar(car, fallbackId) {
  const sanitizedImages = (car.images || [])
    .map(stripAssetPrefix)
    .filter(Boolean);

  const features = Array.isArray(car.features)
    ? car.features
    : typeof car.features === "string"
    ? car.features.split(",").map((f) => f.trim())
    : ["Feature details coming soon"];

  return {
    ...car,
    id: fallbackId,
    productName: car.productName || `${car.make || "Vehicle"} ${car.modelNumber || ""}`.trim(),
    make: car.make || "Unknown",
    category: car.category || "Sedans",
    description: car.description || "Additional details coming soon.",
    price: Number(car.price) || 0,
    year: car.year || new Date().getFullYear(),
    milesRun: car.milesRun || 0,
    features,
    images: sanitizedImages,
    status: car.status || "available",
    review: car.review,
  };
}

function parseAssetMeta(fileName) {
  const base = fileName.replace(/\.[^.]+$/, "");
  const [make = "brand", model = "model", ...rest] = base.split("-");
  const variant = rest.join(" ") || "Edition";
  const makeTitle = toTitle(make);
  const modelTitle = toTitle(model);
  const title = `${makeTitle} ${modelTitle}`;
  const seed = make.charCodeAt(0) + model.charCodeAt(0);

  return {
    code: `${make}-${model}`.toUpperCase(),
    title,
    make: makeTitle,
    category: inferCategory(makeTitle),
    price: 25000 + (seed % 8) * 5000,
    miles: 5000 + (seed % 12) * 1200,
    year: 2018 + (seed % 7),
    features: [`${variant} trim`, "Autonomous Ready", "Connected Infotainment"],
  };
}

function toTitle(value) {
  return value
    .split(/[-_]/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function inferCategory(make) {
  const sportsMakes = ["Ferrari", "Audi", "Nissan", "Lamborghini"];
  const suvMakes = ["Honda", "Toyota", "Ford"];
  if (sportsMakes.includes(make)) return "Sports";
  if (suvMakes.includes(make)) return "SUVs";
  return "Sedans";
}

