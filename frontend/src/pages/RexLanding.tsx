import { useLocation } from "wouter";
import {
  ArrowRight,
  ChevronRight,
  CloudOff,
  Cpu,
  Database,
  Radio,
  ShieldCheck,
  Activity,
  Waves,
} from "lucide-react";

const flow = [
  { label: "Field event", detail: "Captured at the edge", icon: Radio },
  { label: "Local store", detail: "Works without signal", icon: Database },
  { label: "Sync engine", detail: "Validate · send · ack", icon: Waves },
  { label: "Operations", detail: "Evidence you can inspect", icon: Activity },
];

export default function RexLanding() {
  const [, setLocation] = useLocation();

  return (
    <main className="min-h-screen overflow-hidden bg-[#06111f] text-slate-100">
      <div className="pointer-events-none fixed inset-0 opacity-60">
        <div className="absolute left-[-12rem] top-[-10rem] h-[32rem] w-[32rem] rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute right-[-10rem] top-[18rem] h-[28rem] w-[28rem] rounded-full bg-amber-400/10 blur-3xl" />
        <div className="absolute bottom-[-16rem] left-1/3 h-[34rem] w-[34rem] rounded-full bg-blue-600/10 blur-3xl" />
      </div>

      <nav className="relative z-10 border-b border-white/10 bg-[#06111f]/75 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 lg:px-8">
          <button type="button" onClick={() => setLocation("/")} className="flex items-center gap-3 text-left">
            <span className="grid h-10 w-10 place-items-center rounded-xl border border-cyan-300/30 bg-cyan-300/10 text-cyan-200"><Cpu className="h-5 w-5" /></span>
            <span><span className="block text-sm font-semibold tracking-[0.3em] text-cyan-200">REX</span><span className="block text-[10px] uppercase tracking-[0.2em] text-slate-500">Mine Intelligence</span></span>
          </button>
          <div className="flex items-center gap-3">
            <a href="https://github.com/fernandolukoki94-beep/rex-os-observability" target="_blank" rel="noreferrer" className="hidden text-sm text-slate-400 transition hover:text-white sm:block">GitHub</a>
            <button type="button" onClick={() => setLocation("/rex")} className="inline-flex items-center gap-2 rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200"><span>Open Operations</span><ArrowRight className="h-4 w-4" /></button>
          </div>
        </div>
      </nav>

      <section className="relative z-10 mx-auto grid max-w-7xl gap-14 px-5 pb-20 pt-20 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:pb-28 lg:pt-28">
        <div className="flex flex-col justify-center">
          <div className="mb-7 inline-flex w-fit items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-xs font-medium text-emerald-200"><span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_#6ee7b7]" /> v1 · Industrial POC · Pilot-ready architecture</div>
          <h1 className="max-w-3xl text-5xl font-semibold leading-[1.03] tracking-[-0.04em] text-white sm:text-6xl lg:text-7xl">Keep operations visible when the network cannot be trusted.</h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-400">REX Mine Intelligence is an offline-first operational observability platform for industrial and mining environments. Capture offline. Recover after failure. Sync deliberately. Inspect the evidence chain.</p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row"><button type="button" onClick={() => setLocation("/rex")} className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-300 px-5 py-3.5 font-semibold text-slate-950 transition hover:bg-cyan-200">Explore the operations centre <ArrowRight className="h-4 w-4" /></button><button type="button" onClick={() => document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })} className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 px-5 py-3.5 font-semibold text-slate-200 transition hover:bg-white/5">See the architecture <ChevronRight className="h-4 w-4" /></button></div>
          <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-xs text-slate-500"><span className="flex items-center gap-2"><CloudOff className="h-4 w-4 text-cyan-300" /> Offline-first</span><span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-emerald-300" /> Evidence-aware</span><span className="flex items-center gap-2"><Activity className="h-4 w-4 text-amber-300" /> Synthetic telemetry</span></div>
        </div>

        <div className="relative flex items-center justify-center">
          <div className="absolute h-[24rem] w-[24rem] rounded-full border border-cyan-300/10" />
          <div className="absolute h-[19rem] w-[19rem] rounded-full border border-dashed border-cyan-300/20" />
          <div className="relative w-full max-w-md rounded-2xl border border-white/15 bg-white/[0.06] p-4 shadow-2xl shadow-cyan-950/40 backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-white/10 px-2 pb-4"><div><p className="text-[10px] uppercase tracking-[0.25em] text-slate-500">REX Operations</p><h2 className="mt-1 text-lg font-semibold text-white">Field signal overview</h2></div><span className="rounded-full bg-emerald-300/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-200">ONLINE</span></div>
            <div className="grid grid-cols-3 gap-2 py-4"><div className="rounded-xl bg-slate-950/40 p-3"><p className="text-[10px] uppercase text-slate-500">Events</p><p className="mt-1 text-2xl font-semibold text-white">184</p><p className="text-[10px] text-emerald-300">+12 today</p></div><div className="rounded-xl bg-slate-950/40 p-3"><p className="text-[10px] uppercase text-slate-500">Nodes</p><p className="mt-1 text-2xl font-semibold text-white">07</p><p className="text-[10px] text-cyan-300">Connected</p></div><div className="rounded-xl bg-slate-950/40 p-3"><p className="text-[10px] uppercase text-slate-500">Queue</p><p className="mt-1 text-2xl font-semibold text-white">02</p><p className="text-[10px] text-amber-300">Pending sync</p></div></div>
            <div className="rounded-xl border border-amber-300/20 bg-amber-300/[0.06] p-4"><div className="flex items-start justify-between"><div><p className="text-[10px] uppercase tracking-[0.2em] text-amber-200/70">Anomaly detected</p><p className="mt-1 font-semibold text-white">PUMP-017 · vibration 6.2</p></div><span className="rounded-lg bg-amber-300/10 p-2 text-amber-200"><Waves className="h-4 w-4" /></span></div><div className="mt-4 flex items-end gap-1.5"><span className="h-5 w-2 rounded-full bg-cyan-300/30" /><span className="h-7 w-2 rounded-full bg-cyan-300/40" /><span className="h-10 w-2 rounded-full bg-cyan-300/50" /><span className="h-12 w-2 rounded-full bg-amber-300/60" /><span className="h-16 w-2 rounded-full bg-amber-300" /><span className="h-20 w-2 rounded-full bg-rose-300" /></div></div>
            <div className="mt-3 rounded-xl border border-cyan-300/15 bg-cyan-300/[0.04] p-3"><div className="flex items-center justify-between text-[10px] text-slate-500"><span>Evidence Chain</span><span className="font-mono text-cyan-200/80">REX-EVT-000181</span></div><div className="mt-3 flex items-center gap-1.5 text-[9px] text-slate-400"><span className="rounded bg-emerald-300/10 px-2 py-1 text-emerald-200">CREATED</span><span>→</span><span className="rounded bg-cyan-300/10 px-2 py-1 text-cyan-200">STORED</span><span>→</span><span className="rounded bg-cyan-300/10 px-2 py-1 text-cyan-200">SYNCED</span></div></div>
          </div>
        </div>
      </section>

      <section id="architecture" className="relative z-10 border-y border-white/10 bg-white/[0.02] px-5 py-16 lg:px-8"><div className="mx-auto max-w-7xl"><div className="max-w-2xl"><p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-200">The operating model</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">From edge signal to inspectable decision.</h2><p className="mt-4 leading-7 text-slate-400">The first REX vertical slice is intentionally narrow: one operational event, one resilient queue and one chain of evidence that survives the loss of connectivity.</p></div><div className="mt-10 grid gap-3 md:grid-cols-4">{flow.map(({ label, detail, icon: Icon }, index) => <div key={label} className="relative rounded-2xl border border-white/10 bg-[#081727] p-5"><div className="flex items-center justify-between"><span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-300/10 text-cyan-200"><Icon className="h-5 w-5" /></span><span className="font-mono text-xs text-slate-600">0{index + 1}</span></div><h3 className="mt-6 font-semibold text-white">{label}</h3><p className="mt-1 text-sm text-slate-500">{detail}</p>{index < flow.length - 1 && <span className="absolute -right-3 top-10 z-10 hidden text-cyan-300/50 md:block"><ChevronRight className="h-5 w-5" /></span>}</div>)}</div></div></section>

      <section className="relative z-10 border-y border-white/10 bg-[#071422] px-5 py-16 lg:px-8"><div className="mx-auto max-w-7xl"><div className="max-w-2xl"><p className="text-xs font-semibold uppercase tracking-[0.25em] text-amber-200">Proof, not promises</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">A resilient vertical slice you can inspect.</h2><p className="mt-4 leading-7 text-slate-400">The current release is an industrial POC with synthetic telemetry. Its value is the evidence: the edge queue survives offline operation and restart, while the backend preserves traceability and audit context.</p></div><div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"><p className="text-3xl font-semibold text-white">36</p><p className="mt-1 text-sm text-slate-400">backend tests passing</p></div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"><p className="text-3xl font-semibold text-white">10k</p><p className="mt-1 text-sm text-slate-400">offline samples recovered</p></div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"><p className="text-3xl font-semibold text-white">SQLite</p><p className="mt-1 text-sm text-slate-400">transactional Edge queue</p></div><div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"><p className="text-3xl font-semibold text-white">ACK → retry</p><p className="mt-1 text-sm text-slate-400">idempotent recovery path</p></div></div></div></section>

      <section className="relative z-10 mx-auto max-w-7xl px-5 py-16 lg:px-8"><div className="rounded-3xl border border-cyan-300/15 bg-gradient-to-br from-cyan-300/[0.12] via-slate-900/60 to-amber-300/[0.08] p-8 sm:p-12"><div className="flex flex-col justify-between gap-8 md:flex-row md:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-200">Ready for the field</p><h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">See the complete offline-to-sync demonstration.</h2><p className="mt-4 max-w-xl leading-7 text-slate-400">Create an event without connectivity, restart the Edge queue, restore the link and watch the Sync Engine acknowledge it without duplicating the operational effect.</p></div><button type="button" onClick={() => setLocation("/rex")} className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3.5 font-semibold text-slate-950 transition hover:bg-cyan-100">Open REX Operations <ArrowRight className="h-4 w-4" /></button></div></div></section>
      <footer className="relative z-10 border-t border-white/10 px-5 py-7 text-center text-xs text-slate-600 lg:px-8">REX Mine Intelligence · Industrial POC by Fernando Lucoco · Synthetic telemetry, real resilience tests</footer>
    </main>
  );
}
