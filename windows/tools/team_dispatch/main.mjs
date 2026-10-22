#!/usr/bin/env node
// ==============================================================================
// 🏛️ FLOWORK OS SOVEREIGN GUARDIAN ENGINE: team_dispatch
// Active Cable Gatekeeper for Inter-Agent Command & Pipeline Dispatch.
// Inspects payload against Sender's rules.md & task.md.
// Enforces 3-Strike Rule with Forced Stamped Advisory Pass on Attempt 3.
// Supports Cable Guardian Toggle (Enabled / Bypassed for Trial Mode).
// Co-authored-by: Flowork OS <agent@floworkos.com>
// ==============================================================================
import fs from 'fs';
import path from 'path';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try {
      params = JSON.parse(args[pIdx + 1]);
    } catch (_) {}
  }
  return params;
}

function resolveWorkspace() {
  return process.env.FLOWORK_WORKSPACE || process.env.FLOWORK_ENGINE_ROOT || process.cwd();
}

function resolveAgentId(rawId, defaultFallback = 'mr.flow') {
  if (!rawId) return defaultFallback;
  const s = String(rawId).toLowerCase().trim();
  if (s.includes('leader')) return 'leader';
  if (s.includes('mr.flow') || s.includes('mr_flow') || s.includes('flow')) return 'mr.flow';
  if (s.includes('coder')) return 'coder-specialist';
  if (s.includes('qa')) return 'qa-engineer';
  return s;
}

function readSenderDoc(ws, senderId, docName) {
  const candidatePaths = [
    path.join(ws, 'system', 'subagent', senderId, docName),
    path.join(ws, 'system', 'subagent', 'mr.flow', docName),
    path.join(ws, 'system', 'subagent', 'leader', docName),
    path.join(ws, 'system', 'subagent', 'default', docName)
  ];

  for (const cp of candidatePaths) {
    if (fs.existsSync(cp)) {
      try {
        return fs.readFileSync(cp, 'utf-8');
      } catch (_) {}
    }
  }
  return '';
}

function readPipelineDag(ws) {
  const dagPath = path.join(ws, 'system', 'pipeline_dag.json');
  if (fs.existsSync(dagPath)) {
    try {
      const content = fs.readFileSync(dagPath, 'utf-8');
      return JSON.parse(content);
    } catch (_) {}
  }
  return null;
}

function getStrikeFile(ws, senderId, targetId) {
  const flBin = path.join(ws, '.FL_BIN');
  if (!fs.existsSync(flBin)) {
    try { fs.mkdirSync(flBin, { recursive: true }); } catch (_) {}
  }
  const safeSender = senderId.replace(/[^a-zA-Z0-9_-]/g, '_');
  const safeTarget = targetId.replace(/[^a-zA-Z0-9_-]/g, '_');
  return path.join(flBin, `guardian_strike_${safeSender}_to_${safeTarget}.json`);
}

function getStrikeCount(strikeFile) {
  if (fs.existsSync(strikeFile)) {
    try {
      const data = JSON.parse(fs.readFileSync(strikeFile, 'utf-8'));
      return typeof data.strikes === 'number' ? data.strikes : 0;
    } catch (_) {}
  }
  return 0;
}

function setStrikeCount(strikeFile, count) {
  try {
    fs.writeFileSync(strikeFile, JSON.stringify({ strikes: count, updated_at: new Date().toISOString() }, null, 2));
  } catch (_) {}
}

function auditPayloadCompliance(payload, summary, rulesText, taskText) {
  const combinedMsg = `${summary || ''} ${payload || ''}`.trim();
  const lowerMsg = combinedMsg.toLowerCase();
  const deficiencies = [];

  // 1. Clarity & Specificity Test
  if (combinedMsg.length < 20) {
    deficiencies.push("Pesan terlalu singkat atau ambigu. Minimal sertakan 20 karakter dengan spesifikasi tugas yang jelas.");
  }

  const vagueKeywords = ['tolong kerjain ya', 'gitu aja', 'sesuaikan saja', 'bebas aja', 'terserah'];
  for (const vk of vagueKeywords) {
    if (lowerMsg.includes(vk)) {
      deficiencies.push(`Instruksi memuat frasa ambigu ('${vk}'). Wajib jelaskan batasan dan target yang konkret.`);
    }
  }

  // 2. Rules Compliance Test
  if (rulesText) {
    const lowerRules = rulesText.toLowerCase();
    
    // Anti-Overclaim / QC bypass check
    if (lowerRules.includes('exit code 0') || lowerRules.includes('qc') || lowerRules.includes('verifikasi')) {
      if (lowerMsg.includes('lewati tes') || lowerMsg.includes('skip test') || lowerMsg.includes('jangan diverifikasi') || lowerMsg.includes('tanpa verifikasi')) {
        deficiencies.push("Perintah meminta melewati pengujian/QC, menabrak aturan Exit Code 0 pada rules.md pengirim.");
      }
    }

    // Anti-Trash / Scratch discipline
    if (lowerRules.includes('.fl_bin') || lowerRules.includes('sampah') || lowerRules.includes('anti-trash')) {
      if (lowerMsg.includes('tinggalkan file sementara') || lowerMsg.includes('biarkan file sampah')) {
        deficiencies.push("Perintah melanggar disiplin kebersihan workspace / anti-sampah pada rules.md.");
      }
    }

    // Lock Sanctity
    if (lowerRules.includes('@lock') || lowerRules.includes('gembok')) {
      if (lowerMsg.includes('ubah baris lock') || lowerMsg.includes('hapus gembok') || lowerMsg.includes('bypass @lock')) {
        deficiencies.push("Perintah meminta modifikasi pada baris yang terproteksi @lock.");
      }
    }
  }

  // 3. Task Scope Test
  if (taskText) {
    // If task has specific domain constraints
    if (taskText.includes('SOLO MISSION') && lowerMsg.includes('abaikan mandat utama')) {
      deficiencies.push("Perintah bertentangan dengan mandat tugas aktif pada task.md pengirim.");
    }
  }

  return deficiencies;
}

function main() {
  const params = parseArgs();
  const ws = resolveWorkspace();

  const rawSender = params.sender_id || params.from_agent || params.sender || 'leader';
  const rawTarget = params.to_agent || params.to_role || params.target || 'mr.flow';
  const senderId = resolveAgentId(rawSender, 'leader');
  const targetId = resolveAgentId(rawTarget, 'mr.flow');

  const action = params.action || 'HANDOFF';
  const summary = params.summary || '';
  const payload = params.payload || params.message || params.instruction || '';

  // ---------------------------------------------------------------------------
  // 1. Cable Connection & Permission Topology Verification
  // ---------------------------------------------------------------------------
  const dag = readPipelineDag(ws);
  let matchingConn = null;

  if (dag && Array.isArray(dag.connections) && dag.connections.length > 0) {
    const nodeAgentMap = {};
    if (Array.isArray(dag.nodes)) {
      dag.nodes.forEach(n => {
        const agId = (n.agentId || n.id || '').toLowerCase();
        nodeAgentMap[n.id] = agId;
      });
    }

    matchingConn = dag.connections.find(c => {
      const fromAgent = (nodeAgentMap[c.from] || c.from || '').toLowerCase();
      const toAgent = (nodeAgentMap[c.to] || c.to || '').toLowerCase();
      const fromId = senderId.toLowerCase();
      const toId = targetId.toLowerCase();

      const fromMatch = fromAgent.includes(fromId) || c.from.toLowerCase().includes(fromId) || (fromId === 'leader' && (fromAgent.includes('leader') || c.from.includes('leader')));
      const toMatch = toAgent.includes(toId) || c.to.toLowerCase().includes(toId) || (toId.includes('flow') && (toAgent.includes('specialist') || c.to.includes('specialist') || toAgent.includes('flow')));
      return fromMatch && toMatch;
    });

    // If topological cable is missing on the canvas DAG
    if (!matchingConn) {
      const anyOutwardCable = dag.connections.some(c => {
        const fromAgent = (nodeAgentMap[c.from] || c.from || '').toLowerCase();
        return fromAgent.includes(senderId.toLowerCase());
      });
      if (anyOutwardCable) {
        const connectedNodes = dag.connections
          .filter(c => (nodeAgentMap[c.from] || c.from || '').toLowerCase().includes(senderId.toLowerCase()))
          .map(c => nodeAgentMap[c.to] || c.to)
          .join(', ');
        const blockedResponse = {
          status: 'BLOCKED_BY_GUARDIAN',
          exit_code: 1,
          tool: 'team_dispatch',
          cable_guardian: 'TOPOLOGY_RESTRICTION',
          reason: `Kabel penghubung tidak ditemukan! Agen '${senderId}' hanya terhubung ke: [${connectedNodes}]. Hubungan langsung ke '${targetId}' tidak diizinkan tanpa menyambungkan kabel di Swarm Pipeline Canvas.`,
          action_required: `Buka Swarm Pipeline Canvas UI dan sambungkan kabel dari node '${senderId}' ke node '${targetId}'.`
        };
        console.log(JSON.stringify(blockedResponse, null, 2));
        process.exit(0);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 2. Guardian Toggle Switch (Trial Mode Check)
  // ---------------------------------------------------------------------------
  const isGuardianEnabled = matchingConn ? (matchingConn.guardianEnabled !== false) : true;

  if (!isGuardianEnabled) {
    // Guardian is toggled OFF on this cable
    const bypassResponse = {
      status: 'SUCCESS',
      exit_code: 0,
      tool: 'team_dispatch',
      cable_guardian: 'BYPASSED_TRIAL',
      message: `Pesan berhasil dikirim langsung ke '${targetId}'. Filter Guardian dinonaktifkan pada kabel ini (Mode Uji Coba).`,
      delivered_to: targetId,
      action: action,
      summary: summary,
      payload: payload,
      executed_at: new Date().toISOString()
    };
    console.log(JSON.stringify(bypassResponse, null, 2));
    process.exit(0);
  }

  // ---------------------------------------------------------------------------
  // 3. Active Guardian Inspection (rules.md & task.md Audit + 3-Strike Rule)
  // ---------------------------------------------------------------------------
  const rulesText = readSenderDoc(ws, senderId, 'rules.md');
  const taskText = readSenderDoc(ws, senderId, 'task.md');

  const strikeFile = getStrikeFile(ws, senderId, targetId);
  const currentStrikes = getStrikeCount(strikeFile);

  const deficiencies = auditPayloadCompliance(payload, summary, rulesText, taskText);

  if (deficiencies.length === 0) {
    // 100% COMPLIANT - PASS DIRECTLY (STRIKE 0)
    setStrikeCount(strikeFile, 0);
    const passResponse = {
      status: 'SUCCESS',
      exit_code: 0,
      tool: 'team_dispatch',
      cable_guardian: 'PASSED_COMPLIANT',
      message: `Certified by Cable Guardian (Exit Code 0). Perintah dinyatakan matang, mematuhi rules.md, dan selaras dengan task.md pengirim.`,
      delivered_to: targetId,
      action: action,
      summary: summary,
      payload: payload,
      executed_at: new Date().toISOString()
    };
    console.log(JSON.stringify(passResponse, null, 2));
    process.exit(0);
  }

  // Deficiencies detected
  const nextStrike = currentStrikes + 1;

  if (nextStrike < 3) {
    // STRIKE 1 & STRIKE 2: REJECT BACK TO SENDER FOR AUTONOMOUS REVISION
    setStrikeCount(strikeFile, nextStrike);
    const rejectResponse = {
      status: 'BLOCKED_BY_GUARDIAN',
      exit_code: 1,
      tool: 'team_dispatch',
      cable_guardian: 'REJECTED_AUDIT_DEFICIT',
      strike: nextStrike,
      reason: `Guardian Kabel Menolak Transmisi (Percobaan ${nextStrike}/2 Gagal): ${deficiencies.join(' | ')}`,
      sender_rules_reference: rulesText ? rulesText.slice(0, 320) + '...' : '(rules.md tidak ditemukan)',
      sender_task_reference: taskText ? taskText.slice(0, 200) + '...' : '(task.md tidak ditemukan)',
      action_required: 'Koreksi Mandiri Otonom: Perbaiki dan lengkapi instruksi tugas kamu agar mematuhi rules.md dan selaras dengan task.md sebelum melakukan dispatch ulang.'
    };
    console.log(JSON.stringify(rejectResponse, null, 2));
    process.exit(0);
  }

  // STRIKE 3: MAXIMUM DEFICIT REACHED — ESCALATE & BLOCK
  // Zero-Trust Enforcement: Non-compliant instructions are NEVER delivered!
  setStrikeCount(strikeFile, 0); // Reset strike tracker

  const escalationReport = {
    status: 'BLOCKED_ESCALATED',
    exit_code: 1,
    tool: 'team_dispatch',
    cable_guardian: 'ESCALATED_STRIKE_3_BREACH',
    strike: 3,
    error: `Cable Guardian: Pengiriman diblokir permanen setelah 3 kali gagal audit kepatuhan. Mandat dialihkan ke Leader untuk penanganan eksekutif.`,
    sender: senderId,
    target: targetId,
    deficiencies: deficiencies,
    remedy: `Hubungi koordinator/leader atau selaraskan parameter tugas di rules.md sebelum mencoba kembali.`
  };
  console.log(JSON.stringify(escalationReport, null, 2));
  process.exit(1);
}

main();
