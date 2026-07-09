const MAX_BYTES = 12 * 1024 * 1024;

function corsHeaders(env) {
  return {
    "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Vary": "Origin",
  };
}

function json(payload, status, env) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      ...corsHeaders(env),
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function cleanText(value, limit = 60000) {
  return String(value || "").replace(/\s+\n/g, "\n").trim().slice(0, limit);
}

async function sha256(input) {
  const data = new TextEncoder().encode(input);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map(item => item.toString(16).padStart(2, "0")).join("");
}

async function dispatchToGitHub(env, payload) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_REPO) return { dispatched: false };
  const res = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`, {
    method: "POST",
    headers: {
      "accept": "application/vnd.github+json",
      "authorization": `Bearer ${env.GITHUB_TOKEN}`,
      "content-type": "application/json",
      "user-agent": "MonitoringRakyat-PublicIntakeWorker/1.0",
      "x-github-api-version": "2022-11-28",
    },
    body: JSON.stringify({
      event_type: "public_submission",
      client_payload: payload,
    }),
  });
  if (!res.ok) return { dispatched: false, status: res.status };
  return { dispatched: true };
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(env) });
    }
    if (request.method !== "POST") {
      return json({ error: "Method not allowed" }, 405, env);
    }
    const length = Number(request.headers.get("content-length") || 0);
    if (length > MAX_BYTES) {
      return json({ error: "File terlalu besar. Maksimal 12 MB per submission." }, 413, env);
    }

    let form;
    try {
      form = await request.formData();
    } catch (error) {
      return json({ error: "Payload tidak bisa dibaca." }, 400, env);
    }

    const paste = cleanText(form.get("paste"));
    const module = cleanText(form.get("module"), 80) || "BELUM_DIPILIH";
    const period = cleanText(form.get("period"), 80) || "BELUM_DIPILIH";
    const files = form.getAll("files").filter(item => item && typeof item === "object" && "name" in item);
    if (!paste && files.length === 0) {
      return json({ error: "Paste data atau pilih file dulu." }, 400, env);
    }

    const submittedAt = new Date().toISOString();
    const id = "MR-PUBLIC-" + (await sha256(`${submittedAt}|${module}|${period}|${paste}|${files.map(file => file.name).join(",")}`)).slice(0, 16).toUpperCase();
    const fileMeta = files.map(file => ({
      name: cleanText(file.name, 180),
      type: cleanText(file.type, 120),
      size: Number(file.size || 0),
    }));
    const payload = {
      id,
      submitted_at: submittedAt,
      entry_status: "DRAFT_PUBLIC_SUBMISSION",
      module,
      period,
      paste_preview: paste.slice(0, 1200),
      file_count: fileMeta.length,
      files: fileMeta,
      audit_rule: ">=50 masuk audit queue Gudang DB; 40-49 source patrol; <40 audit ketat/fake/spam reject.",
    };

    if (env.PUBLIC_SUBMISSIONS) {
      await env.PUBLIC_SUBMISSIONS.put(`${id}.json`, JSON.stringify(payload, null, 2), {
        httpMetadata: { contentType: "application/json; charset=utf-8" },
      });
      for (const file of files) {
        await env.PUBLIC_SUBMISSIONS.put(`${id}/files/${file.name}`, file.stream(), {
          httpMetadata: { contentType: file.type || "application/octet-stream" },
        });
      }
    }

    ctx.waitUntil(dispatchToGitHub(env, payload));
    return json({ ok: true, id, status: "DRAFT_PUBLIC_SUBMISSION" }, 202, env);
  },
};
