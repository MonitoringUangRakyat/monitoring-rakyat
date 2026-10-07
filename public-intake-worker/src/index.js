const MAX_TOTAL_BYTES = 12 * 1024 * 1024;
const MAX_FILE_BYTES = 8 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set(["pdf", "csv", "txt", "docx", "xlsx"]);
const ALLOWED_MIME = new Set([
  "application/pdf",
  "text/csv",
  "text/plain",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/octet-stream",
]);

function corsHeaders(env, request) {
  const configured = String(env.ALLOWED_ORIGIN || "").trim();
  const origin = request.headers.get("origin") || "";
  const allowed = configured && origin === configured ? configured : configured || "null";
  return {"Access-Control-Allow-Origin": allowed,"Access-Control-Allow-Methods": "POST, OPTIONS","Access-Control-Allow-Headers": "content-type","Vary": "Origin"};
}
function json(payload, status, env, request) {
  return new Response(JSON.stringify(payload), {status,headers:{...corsHeaders(env, request),"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}});
}
function cleanText(value, limit = 60000) { return String(value || "").replace(/\s+\n/g, "\n").trim().slice(0, limit); }
function safeFilename(name) {
  const base=String(name||"upload").replace(/\\/g,"/").split("/").pop().replace(/[^a-zA-Z0-9._ -]/g,"_").replace(/\.+/g,".").slice(0,160);
  return base && base !== "." && base !== ".." ? base : "upload";
}
function extension(name){ const p=String(name||"").toLowerCase().split("."); return p.length>1?p.pop():""; }
async function sha256(input){ const data=new TextEncoder().encode(input); const hash=await crypto.subtle.digest("SHA-256",data); return Array.from(new Uint8Array(hash)).map(x=>x.toString(16).padStart(2,"0")).join(""); }
async function verifyTurnstile(request, env, token){
  if(!env.TURNSTILE_SECRET_KEY) return env.REQUIRE_TURNSTILE === "true" ? {success:false} : {success:true,bypassed:true};
  if(!token) return {success:false};
  const body=new FormData(); body.set("secret",env.TURNSTILE_SECRET_KEY); body.set("response",token);
  const ip=request.headers.get("CF-Connecting-IP"); if(ip) body.set("remoteip",ip);
  const res=await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify",{method:"POST",body});
  return await res.json();
}
function validateFileMeta(file){
  const name=safeFilename(file.name), ext=extension(name), type=String(file.type||"application/octet-stream").toLowerCase();
  if(!ALLOWED_EXTENSIONS.has(ext)) return {ok:false,error:`Extension .${ext||"?"} tidak diizinkan`};
  if(!ALLOWED_MIME.has(type)) return {ok:false,error:`MIME ${type} tidak diizinkan`};
  if(Number(file.size||0)>MAX_FILE_BYTES) return {ok:false,error:"File melebihi batas per-file 8 MB"};
  return {ok:true,name,ext,type,size:Number(file.size||0)};
}
async function magicLooksValid(file, meta){
  const head=new Uint8Array(await file.slice(0,8).arrayBuffer());
  if(meta.ext==="pdf") return head.length>=4&&head[0]===0x25&&head[1]===0x50&&head[2]===0x44&&head[3]===0x46;
  if(meta.ext==="docx"||meta.ext==="xlsx") return head.length>=4&&head[0]===0x50&&head[1]===0x4b;
  return true;
}
async function dispatchToGitHub(env,payload){
  if(!env.GITHUB_TOKEN||!env.GITHUB_REPO) return {dispatched:false,reason:"NOT_CONFIGURED"};
  const res=await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`,{method:"POST",headers:{"accept":"application/vnd.github+json","authorization":`Bearer ${env.GITHUB_TOKEN}`,"content-type":"application/json","user-agent":"MonitoringRakyat-PublicIntakeWorker/2.0","x-github-api-version":"2022-11-28"},body:JSON.stringify({event_type:"public_submission",client_payload:payload})});
  return res.ok?{dispatched:true}:{dispatched:false,status:res.status};
}
export default {
  async fetch(request, env, ctx){
    if(request.method==="OPTIONS") return new Response(null,{status:204,headers:corsHeaders(env,request)});
    if(request.method!=="POST") return json({error:"Method not allowed"},405,env,request);
    const configured=String(env.ALLOWED_ORIGIN||"").trim(), origin=request.headers.get("origin")||"";
    if(!configured||origin!==configured) return json({error:"Origin not allowed"},403,env,request);
    const declared=Number(request.headers.get("content-length")||0); if(declared>MAX_TOTAL_BYTES) return json({error:"Submission melebihi 12 MB."},413,env,request);
    let form; try{form=await request.formData();}catch{return json({error:"Payload tidak bisa dibaca."},400,env,request);}
    const turnstile=await verifyTurnstile(request,env,cleanText(form.get("cf-turnstile-response"),4096)); if(!turnstile.success) return json({error:"Anti-bot verification failed."},403,env,request);
    const paste=cleanText(form.get("paste")), module=cleanText(form.get("module"),80)||"BELUM_DIPILIH", period=cleanText(form.get("period"),80)||"BELUM_DIPILIH";
    const files=form.getAll("files").filter(x=>x&&typeof x==="object"&&"name" in x); if(!paste&&files.length===0) return json({error:"Paste data atau pilih file dulu."},400,env,request);
    let actualTotal=new TextEncoder().encode(paste).byteLength; const accepted=[];
    for(const file of files){ const meta=validateFileMeta(file); if(!meta.ok) return json({error:meta.error},415,env,request); if(!(await magicLooksValid(file,meta))) return json({error:`Signature file ${meta.name} tidak cocok.`},415,env,request); actualTotal+=meta.size; accepted.push({file,meta}); }
    if(actualTotal>MAX_TOTAL_BYTES) return json({error:"Actual submission size melebihi 12 MB."},413,env,request);
    const submittedAt=new Date().toISOString(); const id="MR-PUBLIC-"+(await sha256(`${submittedAt}|${module}|${period}|${paste}|${accepted.map(x=>x.meta.name).join(",")}`)).slice(0,16).toUpperCase();
    const payload={id,submitted_at:submittedAt,entry_status:"DRAFT_PUBLIC_SUBMISSION",quarantine_status:"PENDING_SECURITY_AND_EVIDENCE_AUDIT",module,period,paste_preview:paste.slice(0,1200),file_count:accepted.length,files:accepted.map(x=>({name:x.meta.name,type:x.meta.type,size:x.meta.size})),audit_rule:"Public input is a claim, not a fact. Never promote without evidence gate."};
    if(env.PUBLIC_SUBMISSIONS){ const prefix=`quarantine/${id}`; await env.PUBLIC_SUBMISSIONS.put(`${prefix}/metadata.json`,JSON.stringify(payload,null,2),{httpMetadata:{contentType:"application/json; charset=utf-8"}}); for(const {file,meta} of accepted){ await env.PUBLIC_SUBMISSIONS.put(`${prefix}/files/${meta.name}`,file.stream(),{httpMetadata:{contentType:meta.type}}); } }
    ctx.waitUntil(dispatchToGitHub(env,payload)); return json({ok:true,id,status:"DRAFT_PUBLIC_SUBMISSION",quarantine:true},202,env,request);
  }
};
