const MAX_BODY_BYTES = 2048;
const ALLOWED_EVENTS = new Set(["page_view", "cta_click"]);
const ALLOWED_PATHS = new Set(["/", "/#features", "/#audience", "/#about", "/#contact"]);
const ALLOWED_CTA = new Set(["hero_launch", "hero_features", "nav_contact", "footer_top"]);
const ALLOWED_SOURCE = new Set(["direct", "search", "social", "referral", "campaign", "other"]);
const ALLOWED_DEVICE = new Set(["mobile", "desktop", "tablet", "unknown"]);

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

function cleanString(value, maxLength) {
  if (typeof value !== "string") return "";
  return value.replace(/[\u0000-\u001f\u007f]/g, "").trim().slice(0, maxLength);
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get("Origin");
  const requestUrl = new URL(request.url);
  if (origin) {
    try {
      if (new URL(origin).origin !== requestUrl.origin) {
        return json({ ok: false, error: "origin_not_allowed" }, 403);
      }
    } catch {
      return json({ ok: false, error: "invalid_origin" }, 400);
    }
  }

  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    return json({ ok: false, error: "json_required" }, 415);
  }

  const declaredLength = Number(request.headers.get("content-length") || "0");
  if (declaredLength > MAX_BODY_BYTES) {
    return json({ ok: false, error: "payload_too_large" }, 413);
  }

  if (!env.ANALYTICS_DB) {
    return json({ ok: false, error: "analytics_not_configured" }, 503);
  }

  let raw;
  try {
    raw = await request.text();
    if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
      return json({ ok: false, error: "payload_too_large" }, 413);
    }
  } catch {
    return json({ ok: false, error: "invalid_body" }, 400);
  }

  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    return json({ ok: false, error: "invalid_json" }, 400);
  }

  if (!input || typeof input !== "object" || Array.isArray(input)) {
    return json({ ok: false, error: "invalid_payload" }, 400);
  }

  const event = cleanString(input.event, 32);
  if (!ALLOWED_EVENTS.has(event)) {
    return json({ ok: false, error: "event_not_allowed" }, 400);
  }

  let path = cleanString(input.path, 64);
  // Never accept query strings, full URLs or arbitrary paths.
  if (path.includes("?") || path.includes("://") || path.includes("..")) path = "/";
  if (!ALLOWED_PATHS.has(path)) path = "/";

  const sourceInput = cleanString(input.source, 24);
  const source = ALLOWED_SOURCE.has(sourceInput) ? sourceInput : "other";
  const deviceInput = cleanString(input.device, 16);
  const device = ALLOWED_DEVICE.has(deviceInput) ? deviceInput : "unknown";
  const ctaInput = cleanString(input.cta, 32);
  const cta = ALLOWED_CTA.has(ctaInput) ? ctaInput : null;

  if (event === "cta_click" && !cta) {
    return json({ ok: false, error: "cta_not_allowed" }, 400);
  }

  try {
    await env.ANALYTICS_DB.prepare(
      "INSERT INTO analytics_events (event_name, page_path, source, device_class, cta_id, created_at) VALUES (?, ?, ?, ?, ?, ?)"
    ).bind(event, path, source, device, cta, new Date().toISOString()).run();
  } catch {
    // Do not log request body, headers, IP address, or User-Agent.
    return json({ ok: false, error: "storage_unavailable" }, 503);
  }

  return json({ ok: true }, 202);
}

export async function onRequestGet() {
  return json({ ok: false, error: "method_not_allowed" }, 405);
}
