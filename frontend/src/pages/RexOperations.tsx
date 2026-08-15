import { useEffect, useMemo, useState } from "react";
import { nextDurableEventId, persistDurableEvents, readDurableEvents } from "../lib/rexOfflineStore";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Cloud,
  CloudOff,
  Cpu,
  Gauge,
  MapPin,
  RefreshCw,
  Signal,
  Thermometer,
  Wifi,
  WifiOff,
  Wrench,
  X,
} from "lucide-react";

type IncidentStatus = "open" | "investigating" | "maintenance" | "resolved";
type Priority = "low" | "medium" | "high" | "critical";
type SyncStatus = "local" | "pending" | "syncing" | "synced" | "failed";
type ConnectivityState = "online" | "offline";

type EvidenceEntry = { at: string; event: string; detail: string };

type Incident = {
  id: string;
  eventId?: string;
  serverAck?: boolean;
  eventType?: "EQUIPMENT_INCIDENT";
  equipment: string;
  area: string;
  category: string;
  description: string;
  priority: Priority;
  status: IncidentStatus;
  syncStatus: SyncStatus;
  createdAt: string;
  createdAtISO?: string;
  deviceId?: string;
  operatorId?: string;
  location?: string;
  connectivityState?: ConnectivityState;
  integrityHash?: string;
  evidence?: EvidenceEntry[];
  history?: EvidenceEntry[];
};

async function makeIntegrityHash(value: string) {
  if (!window.crypto?.subtle) return "demo-integrity-unavailable";
  const bytes = new TextEncoder().encode(value);
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join("").slice(0, 16);
}

const seedIncidents: Incident[] = [
  {
    id: "INC-0042",
    eventId: "REX-EVT-2026-000181",
    eventType: "EQUIPMENT_INCIDENT",
    deviceId: "field-device-07",
    integrityHash: "a81c2e7d9b31f004",
    history: [{ at: "14:32:18", event: "EVENT CREATED", detail: "Campo · Field Device 07" }, { at: "14:32:19", event: "LOCAL STORAGE", detail: "Integridade verificada" }],
    equipment: "Bomba 17",
    area: "Área B · Britagem",
    category: "Vibração",
    description: "Vibração acima do padrão durante o arranque da linha.",
    priority: "high",
    status: "investigating",
    syncStatus: "synced",
    createdAt: "Hoje, 14:32",
  },
  {
    id: "INC-0041",
    eventId: "REX-EVT-2026-000180",
    eventType: "EQUIPMENT_INCIDENT",
    deviceId: "field-device-03",
    integrityHash: "c312d8f0a6e89122",
    history: [{ at: "12:08:03", event: "EVENT SYNCHRONIZED", detail: "Server acknowledged" }],
    equipment: "Transportador 03",
    area: "Pátio Norte",
    category: "Temperatura",
    description: "Rolamento aquece mais do que o valor de referência.",
    priority: "medium",
    status: "maintenance",
    syncStatus: "synced",
    createdAt: "Hoje, 12:08",
  },
  {
    id: "INC-0040",
    eventId: "REX-EVT-2026-000179",
    eventType: "EQUIPMENT_INCIDENT",
    deviceId: "field-device-07",
    integrityHash: "f0ab771ca2490e91",
    history: [{ at: "10:46:11", event: "EVENT CREATED", detail: "Campo · Field Device 07" }],
    equipment: "Gerador 02",
    area: "Subestação",
    category: "Energia",
    description: "Queda momentânea de tensão registada pelo operador.",
    priority: "critical",
    status: "open",
    syncStatus: "pending",
    createdAt: "Hoje, 10:46",
  },
];

const priorityLabel: Record<Priority, string> = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
  critical: "Crítica",
};

const statusLabel: Record<IncidentStatus, string> = {
  open: "Aberto",
  investigating: "Em análise",
  maintenance: "Em intervenção",
  resolved: "Resolvido",
};

function formatTime() {
  return new Intl.DateTimeFormat("pt-PT", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

type ApiEvent = { event_id: string; sync_status: string; integrity_hash?: string; evidence?: { at: string; event: string; detail: string }[] };

async function postOperationalEvent(incident: Incident): Promise<ApiEvent> {
  const response = await fetch("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_id: incident.eventId,
      event_type: incident.eventType || "EQUIPMENT_INCIDENT",
      description: incident.description,
      source_device: incident.deviceId || "field-device-07",
      operator: incident.operatorId || "operator-demo-01",
      location: incident.location || incident.area,
      created_at: incident.createdAtISO,
      payload: { equipment: incident.equipment, category: incident.category, priority: incident.priority },
    }),
  });
  if (!response.ok) throw new Error(`API /events respondeu ${response.status}`);
  const payload = (await response.json()) as { data: ApiEvent };
  return payload.data;
}

async function syncServerEvents(): Promise<ApiEvent[]> {
  const response = await fetch("/api/events/sync", { method: "POST" });
  if (!response.ok) throw new Error(`API /events/sync respondeu ${response.status}`);
  const payload = (await response.json()) as { synced: ApiEvent[] };
  return payload.synced || [];
}

export default function RexOperations() {
  const [incidents, setIncidents] = useState<Incident[]>(seedIncidents);
  const [isHydrated, setIsHydrated] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [apiState, setApiState] = useState<"checking" | "connected" | "unavailable">("checking");
  const [showForm, setShowForm] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showSyncPanel, setShowSyncPanel] = useState(false);
  const [syncSteps, setSyncSteps] = useState<string[]>([]);
  const [form, setForm] = useState({
    equipment: "Bomba 17",
    area: "Área B · Britagem",
    category: "Vibração",
    priority: "high" as Priority,
    description: "",
  });

  useEffect(() => {
    void readDurableEvents<Incident>(seedIncidents).then((stored) => {
      setIncidents(stored);
      setIsHydrated(true);
    });
  }, []);

  useEffect(() => {
    if (isHydrated) void persistDurableEvents(incidents);
  }, [incidents, isHydrated]);

  useEffect(() => {
    fetch("/api/telemetry/mine")
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        setApiState("connected");
      })
      .catch(() => setApiState("unavailable"));
  }, []);

  const pendingCount = incidents.filter((incident) => incident.syncStatus !== "synced").length;
  const openCount = incidents.filter((incident) => incident.status !== "resolved").length;
  const criticalCount = incidents.filter((incident) => incident.priority === "critical").length;

  const telemetry = useMemo(
    () => [
      { label: "Vibração · Bomba 17", value: "7.8", unit: "mm/s", level: "Alerta", icon: Activity, tone: "amber" },
      { label: "Temperatura · Motor 04", value: "68", unit: "°C", level: "Normal", icon: Thermometer, tone: "cyan" },
      { label: "Pressão · Linha 02", value: "4.2", unit: "bar", level: "Normal", icon: Gauge, tone: "emerald" },
    ],
    [],
  );

  const syncIncidents = async (additionalIncident?: Incident) => {
    const candidates = [...incidents.filter((incident) => incident.syncStatus !== "synced"), ...(additionalIncident ? [additionalIncident] : [])].filter((incident, index, items) => items.findIndex((item) => item.eventId === incident.eventId) === index);
    if (!isOnline || candidates.length === 0 || isSyncing) return;
    const total = candidates.length;
    setIsSyncing(true);
    setShowSyncPanel(true);
    setSyncSteps([`${total} eventos encontrados`]);
    setIncidents((current) => current.map((incident) => (incident.syncStatus !== "synced" ? { ...incident, syncStatus: "syncing", history: [...(incident.history || []), { at: formatTime(), event: "SYNC STARTED", detail: "Connectivity available" }] } : incident)));
    try {
      setSyncSteps([`${total} eventos encontrados`, `${total} eventos validados`]);
      for (const incident of candidates) {
        if (incident.serverAck) continue;
        const ack = await postOperationalEvent(incident);
        setApiState("connected");
        setIncidents((current) => current.map((item) => item.eventId === incident.eventId ? { ...item, syncStatus: "synced", serverAck: true, integrityHash: ack.integrity_hash || item.integrityHash, history: [...(item.history || []), { at: formatTime(), event: "ACKNOWLEDGED", detail: "Flask API accepted event" }, ...(ack.evidence || []).map((entry) => ({ at: entry.at, event: entry.event, detail: entry.detail }))] } : item));
      }
      const synced = await syncServerEvents();
      setSyncSteps([`${total} eventos encontrados`, `${total} eventos validados`, `${total} eventos enviados`, `${synced.length || total} eventos confirmados`, "0 pendentes"]);
    } catch (error) {
      setApiState("unavailable");
      setIncidents((current) => current.map((incident) => incident.syncStatus === "syncing" ? { ...incident, syncStatus: "failed", history: [...(incident.history || []), { at: formatTime(), event: "SYNC FAILED", detail: error instanceof Error ? error.message : "Transport unavailable" }] } : incident));
      setSyncSteps([`${total} eventos encontrados`, `${total} eventos validados`, "Falha no transporte", "Retry disponível"]);
    } finally {
      setIsSyncing(false);
    }
  };

  const updateStatus = (id: string, status: IncidentStatus) => {
    setIncidents((current) => current.map((incident) => (incident.id === id ? { ...incident, status, syncStatus: isOnline ? "synced" : "pending" } : incident)));
  };

  const createIncident = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const createdAt = new Date();
    const eventId = await nextDurableEventId();
    const description = form.description.trim() || "Ocorrência registada pelo operador em campo.";
    const incident: Incident = {
      id: `INC-${String(43 + incidents.length).padStart(4, "0")}`,
      eventId,
      equipment: form.equipment,
      area: form.area,
      category: form.category,
      description,
      priority: form.priority,
      status: "open",
      eventType: "EQUIPMENT_INCIDENT",
      syncStatus: "pending",
      createdAt: `Hoje, ${formatTime()}`,
      createdAtISO: createdAt.toISOString(),
      deviceId: "field-device-07",
      operatorId: "operator-demo-01",
      location: form.area,
      connectivityState: isOnline ? "online" : "offline",
      integrityHash: await makeIntegrityHash(`${eventId}|field-device-07|operator-demo-01|${form.area}|${createdAt.toISOString()}|${description}`),
      history: [
        { at: formatTime(), event: "EVENT CREATED", detail: `EQUIPMENT_INCIDENT · ${eventId}` },
        { at: formatTime(), event: isOnline ? "LOCAL STORAGE" : "LOCAL STORAGE", detail: `Connectivity ${isOnline ? "ONLINE" : "OFFLINE"}` },
        { at: formatTime(), event: "HASH GENERATED", detail: "Integrity fingerprint · alteração detectável" },
        { at: formatTime(), event: "SYNC_PENDING", detail: isOnline ? "A aguardar confirmação Flask" : "Connectivity OFFLINE" },
      ],
    };
    setIncidents((current) => [incident, ...current]);
    if (isOnline) {
      window.setTimeout(() => { void syncIncidents(incident); }, 0);
    }
    setForm((current) => ({ ...current, description: "" }));
    setShowForm(false);
  };

  return (
    <main className="min-h-screen bg-[#07111f] text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/15 ring-1 ring-cyan-300/30">
                <Cpu className="h-5 w-5 text-cyan-300" />
              </div>
              <span className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-300">REX Mine Intelligence</span>
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Centro de Operações</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">Visibilidade operacional para equipas de campo, mesmo quando a rede não acompanha a operação.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => setIsOnline((value) => !value)}
              className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition ${isOnline ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300" : "border-amber-400/30 bg-amber-400/10 text-amber-300"}`}
            >
              {isOnline ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
              <span><span className="block text-[10px] uppercase tracking-widest opacity-60">Connectivity</span>{isOnline ? "ONLINE" : "OFFLINE"}</span>
            </button>
            <button type="button" onClick={() => { void syncIncidents(); }} disabled={!isOnline || pendingCount === 0 || isSyncing} className="flex items-center gap-2 rounded-lg bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-40">
              <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
              {isSyncing ? "A sincronizar…" : `Sincronizar${pendingCount ? ` (${pendingCount})` : ""}`}
            </button>
          </div>
        </header>

        <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            { label: "Incidentes activos", value: openCount, detail: "na operação", icon: ClipboardList, color: "text-cyan-300" },
            { label: "Prioridade crítica", value: criticalCount, detail: "requer atenção", icon: AlertTriangle, color: "text-amber-300" },
            { label: "A sincronizar", value: pendingCount, detail: isOnline ? "rede disponível" : "guardado no dispositivo", icon: isOnline ? Cloud : CloudOff, color: "text-violet-300" },
            { label: "Saúde operacional", value: "94%", detail: "últimos 30 minutos", icon: CheckCircle2, color: "text-emerald-300" },
          ].map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/10">
              <div className="mb-4 flex items-center justify-between"><span className="text-sm text-slate-400">{metric.label}</span><metric.icon className={`h-5 w-5 ${metric.color}`} /></div>
              <div className="text-3xl font-semibold text-white">{metric.value}</div>
              <div className="mt-1 text-xs text-slate-500">{metric.detail}</div>
            </div>
          ))}
        </section>

        <section className="mb-6 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
            <div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold text-white">Telemetria sintética</h2><p className="mt-1 text-xs text-slate-500">Dados de demonstração · actualização em tempo real</p></div><Signal className="h-5 w-5 text-cyan-300" /></div>
            <div className="grid gap-4 md:grid-cols-3">
              {telemetry.map((item) => (
                <div key={item.label} className="rounded-xl border border-white/10 bg-slate-950/30 p-4">
                  <div className="mb-5 flex items-start justify-between"><item.icon className={`h-5 w-5 ${item.tone === "amber" ? "text-amber-300" : item.tone === "cyan" ? "text-cyan-300" : "text-emerald-300"}`} /><span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ${item.tone === "amber" ? "bg-amber-400/10 text-amber-300" : "bg-emerald-400/10 text-emerald-300"}`}>{item.level}</span></div>
                  <div className="text-2xl font-semibold text-white">{item.value}<span className="ml-1 text-xs font-normal text-slate-500">{item.unit}</span></div>
                  <div className="mt-2 text-xs text-slate-400">{item.label}</div>
                  <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10"><div className={`h-full rounded-full ${item.tone === "amber" ? "w-[78%] bg-amber-300" : item.tone === "cyan" ? "w-[52%] bg-cyan-300" : "w-[43%] bg-emerald-300"}`} /></div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-amber-300/20 bg-amber-300/[0.06] p-5"><div className="mb-4 flex items-center gap-3"><div className="rounded-lg bg-amber-300/15 p-2"><AlertTriangle className="h-5 w-5 text-amber-300" /></div><div><h2 className="font-semibold text-white">Alerta inteligente</h2><p className="text-xs text-amber-200/60">Padrão detectado nos dados de demonstração</p></div></div><p className="text-sm leading-6 text-slate-300">A Bomba 17 apresentou <strong className="text-amber-200">4 ocorrências de vibração</strong> nas últimas três semanas. O intervalo entre incidentes está a diminuir.</p><div className="mt-5 flex items-center justify-between border-t border-amber-200/10 pt-4"><span className="text-xs text-slate-400">Recomendação</span><span className="text-xs font-semibold text-amber-200">Inspecção preventiva</span></div></div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white/[0.04]">
          <div className="flex flex-col gap-4 border-b border-white/10 p-5 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="font-semibold text-white">Incidentes operacionais</h2><p className="mt-1 text-xs text-slate-500">Registos de campo e tarefas de manutenção</p></div><button type="button" onClick={() => setShowForm(true)} className="flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100"><Wrench className="h-4 w-4" /> Registar incidente</button></div>
          <div className="divide-y divide-white/10">
            {incidents.map((incident) => (
              <button key={incident.id} type="button" onClick={() => setSelectedIncident(incident)} className="grid w-full gap-4 p-5 text-left transition hover:bg-white/[0.04] md:grid-cols-[1.3fr_1fr_0.8fr_0.7fr] md:items-center">
                <div><div className="mb-1 flex items-center gap-2"><span className="font-medium text-white">{incident.equipment}</span><span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">{incident.id}</span>{incident.eventId && <span className="text-[10px] font-mono text-cyan-300/70">{incident.eventId}</span>}</div><p className="line-clamp-1 text-sm text-slate-400">{incident.description}</p></div>
                <div className="flex items-center gap-2 text-xs text-slate-400"><MapPin className="h-4 w-4 text-slate-500" />{incident.area}</div>
                <div><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${incident.priority === "critical" ? "bg-red-400/10 text-red-300" : incident.priority === "high" ? "bg-amber-400/10 text-amber-300" : "bg-cyan-400/10 text-cyan-300"}`}>{priorityLabel[incident.priority]}</span><div className="mt-2 text-xs text-slate-500">{statusLabel[incident.status]}</div></div>
                <div className="flex items-center justify-between gap-3 md:justify-end"><span className={`flex items-center gap-1.5 text-xs ${incident.syncStatus === "synced" ? "text-emerald-300" : "text-amber-300"}`}>{incident.syncStatus === "synced" ? <Cloud className="h-4 w-4" /> : <CloudOff className="h-4 w-4" />}{incident.syncStatus === "synced" ? "Sincronizado" : incident.syncStatus === "syncing" ? "A sincronizar" : incident.syncStatus === "failed" ? "Falhou · pendente" : "Pendente · local"}</span><span className="text-xs text-slate-600">{incident.createdAt}</span></div>
              </button>
            ))}
          </div>
        </section>

        {showSyncPanel && <section className="mt-6 rounded-2xl border border-cyan-300/20 bg-cyan-300/[0.05] p-5"><div className="mb-4 flex items-center justify-between"><div><h2 className="font-semibold text-white">SYNC ENGINE</h2><p className="mt-1 text-xs text-slate-500">Validação local · demonstração sem servidor industrial</p></div><button type="button" onClick={() => setShowSyncPanel(false)} className="text-xs text-slate-500 hover:text-white">Fechar</button></div><div className="grid gap-2 sm:grid-cols-5">{["encontrados", "validados", "enviados", "confirmados", "pendentes"].map((label, index) => <div key={label} className="rounded-lg border border-white/10 bg-slate-950/30 p-3"><div className="text-lg font-semibold text-cyan-200">{syncSteps[index]?.split(" ")[0] || "—"}</div><div className="mt-1 text-[10px] uppercase tracking-wider text-slate-500">{label}</div></div>)}</div>{!isSyncing && syncSteps.length === 5 && <p className="mt-4 flex items-center gap-2 text-sm font-medium text-emerald-300"><CheckCircle2 className="h-4 w-4" /> Synchronization complete</p>}</section>}
      </div>

      {showForm && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 backdrop-blur-sm sm:items-center"><form onSubmit={createIncident} className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#0d1a2b] p-6 shadow-2xl"><div className="mb-6 flex items-center justify-between"><div><h2 className="text-xl font-semibold text-white">Novo incidente</h2><p className="mt-1 text-xs text-slate-500">O registo será guardado localmente se estiveres offline.</p></div><button type="button" onClick={() => setShowForm(false)} className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"><X className="h-5 w-5" /></button></div><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm text-slate-400">Equipamento<select value={form.equipment} onChange={(event) => setForm({ ...form, equipment: event.target.value })} className="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-300"><option>Bomba 17</option><option>Transportador 03</option><option>Gerador 02</option><option>Escavadora 08</option></select></label><label className="text-sm text-slate-400">Categoria<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} className="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-300"><option>Vibração</option><option>Temperatura</option><option>Pressão</option><option>Segurança</option><option>Energia</option><option>Outro</option></select></label></div><label className="mt-4 block text-sm text-slate-400">Área<input value={form.area} onChange={(event) => setForm({ ...form, area: event.target.value })} className="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-300" /></label><label className="mt-4 block text-sm text-slate-400">Prioridade<select value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value as Priority })} className="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-300"><option value="low">Baixa</option><option value="medium">Média</option><option value="high">Alta</option><option value="critical">Crítica</option></select></label><label className="mt-4 block text-sm text-slate-400">Descrição<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} rows={3} placeholder="Descreve o que observaste no local…" className="mt-2 w-full resize-none rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-300" /></label><button type="submit" className="mt-6 w-full rounded-lg bg-cyan-300 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">Guardar incidente</button></form></div>}

      {selectedIncident && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"><div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0d1a2b] p-6 shadow-2xl"><div className="mb-5 flex items-start justify-between"><div><span className="text-xs font-semibold uppercase tracking-widest text-cyan-300">{selectedIncident.id}</span><p className="mt-1 font-mono text-[10px] text-cyan-200/70">{selectedIncident.eventId || "REX-EVT-LEGACY"}</p><h2 className="mt-2 text-xl font-semibold text-white">{selectedIncident.equipment}</h2></div><button type="button" onClick={() => setSelectedIncident(null)} className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"><X className="h-5 w-5" /></button></div><div className="space-y-4 text-sm"><div><span className="text-xs text-slate-500">Descrição</span><p className="mt-1 text-slate-300">{selectedIncident.description}</p></div><div className="grid grid-cols-2 gap-4"><div><span className="text-xs text-slate-500">Categoria</span><p className="mt-1 text-slate-300">{selectedIncident.category}</p></div><div><span className="text-xs text-slate-500">Prioridade</span><p className="mt-1 text-slate-300">{priorityLabel[selectedIncident.priority]}</p></div></div><div className="rounded-xl border border-cyan-300/10 bg-cyan-300/[0.04] p-3"><div className="mb-2 flex items-center justify-between"><span className="text-xs font-semibold uppercase tracking-wider text-cyan-200">Evidence Chain</span><span className="text-[10px] text-slate-500">{selectedIncident.deviceId || "legacy-device"}</span></div><div className="mb-3 grid grid-cols-2 gap-2 text-[10px] text-slate-500"><span>Type: <strong className="text-slate-300">{selectedIncident.eventType || "EQUIPMENT_INCIDENT"}</strong></span><span>Status: <strong className="text-slate-300">{selectedIncident.syncStatus.toUpperCase()}</strong></span><span>Operator: <strong className="text-slate-300">{selectedIncident.operatorId || "operator-legacy"}</strong></span><span>Origin: <strong className="text-slate-300">{selectedIncident.connectivityState || "unknown"}</strong></span></div><div className="space-y-2">{(selectedIncident.history || []).map((entry) => <div key={`${entry.at}-${entry.event}`} className="flex gap-3 text-[11px]"><span className="font-mono text-slate-500">{entry.at}</span><span><strong className="text-slate-300">{entry.event}</strong><span className="ml-2 text-slate-500">{entry.detail}</span></span></div>)}</div><p className="mt-3 border-t border-white/10 pt-2 font-mono text-[10px] text-slate-500">Integrity fingerprint: {selectedIncident.integrityHash || "legacy-event"} · alteração detectável, não prova de segurança absoluta</p></div><label className="block text-xs text-slate-500">Actualizar estado<select value={selectedIncident.status} onChange={(event) => { updateStatus(selectedIncident.id, event.target.value as IncidentStatus); setSelectedIncident({ ...selectedIncident, status: event.target.value as IncidentStatus }); }} className="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-300"><option value="open">Aberto</option><option value="investigating">Em análise</option><option value="maintenance">Em intervenção</option><option value="resolved">Resolvido</option></select></label></div></div></div>}
    </main>
  );
}
