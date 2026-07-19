#!/usr/bin/env node
// Compares the key sets of messages/de.json and messages/en.json (including
// nested namespaces) and fails with a non-zero exit code if they don't match
// exactly. Run via `npm run check:i18n`.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const messagesDir = path.join(__dirname, "..", "messages");

const LOCALES = ["de", "en"];

function loadMessages(locale) {
  const filePath = path.join(messagesDir, `${locale}.json`);
  const raw = readFileSync(filePath, "utf-8");
  return JSON.parse(raw);
}

/** Recursively collects dotted key paths for every leaf value in an object. */
function collectKeyPaths(obj, prefix = "") {
  const keys = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      keys.push(...collectKeyPaths(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

const messagesByLocale = Object.fromEntries(
  LOCALES.map((locale) => [locale, loadMessages(locale)])
);

const keySetsByLocale = Object.fromEntries(
  LOCALES.map((locale) => [locale, new Set(collectKeyPaths(messagesByLocale[locale]))])
);

const [baseLocale, ...otherLocales] = LOCALES;
const baseKeys = keySetsByLocale[baseLocale];

let hasMismatch = false;

for (const locale of otherLocales) {
  const compareKeys = keySetsByLocale[locale];

  const missingInCompare = [...baseKeys].filter((k) => !compareKeys.has(k));
  const extraInCompare = [...compareKeys].filter((k) => !baseKeys.has(k));

  if (missingInCompare.length > 0 || extraInCompare.length > 0) {
    hasMismatch = true;
    console.error(`i18n key mismatch between "${baseLocale}" and "${locale}":`);
    if (missingInCompare.length > 0) {
      console.error(`  Missing in ${locale}.json (present in ${baseLocale}.json):`);
      for (const key of missingInCompare) {
        console.error(`    - ${key}`);
      }
    }
    if (extraInCompare.length > 0) {
      console.error(`  Extra in ${locale}.json (not present in ${baseLocale}.json):`);
      for (const key of extraInCompare) {
        console.error(`    - ${key}`);
      }
    }
  }
}

if (hasMismatch) {
  console.error("\ncheck:i18n failed - fix messages/de.json / messages/en.json so their key sets match exactly.");
  process.exit(1);
}

console.log(`check:i18n OK - ${LOCALES.join(", ")} message key sets match (${baseKeys.size} keys).`);
