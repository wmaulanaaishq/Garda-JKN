'use client';

import { useState } from 'react';

type Decision = 'APPROVED' | 'DOWNGRADED' | 'ESCALATED' | 'REJECTED';
type Panel = 'console' | 'audit' | 'rag' | 'metrics' | 'reference' | 'master';
type VClaimTab = 'Referensi' | 'Peserta' | 'SEP' | 'Rujukan' | 'Monitoring' | 'Rencana Kontrol';

type ClaimDraft = {
  id_kunjungan: string;
  nama_pasien: string;
  nik: string;
  usia: string;
  diag_awal: string;
  diag_sekunder_1: string;
  diag_sekunder_2: string;
  tindakan_1: string;
  tindakan_2: string;
  icu_days: string;
  severity_level: string;
  biaya_tagih: string;
  durasi_rawat: string;
  catatan_klinis: string;
  kreatinin: string;
  troponin: string;
  tipe_faskes: string;
  eeg_attached: boolean;
};

type AuditTrail = {
  ml_risk_assessment?: string;
  pnpk_reference_rule?: string;
  clinical_inconsistency?: string;
  action_recommendation?: string;
};

type EvaluationDetail = {
  decision: Decision;
  adjudication_result: Decision;
  severity_level: number;
  confidence_score: number;
  ml_risk_score: number;
  is_anomalous: boolean;
  reason_codes: string[];
  data_quality_flags?: string[];
  adjudication_reason: string;
  rag_context: string;
  audit_trail?: AuditTrail;
};

type EvaluationResponse = {
  success: boolean;
  metadata: { code: number; message: string };
  response: EvaluationDetail;
  adjudication_result?: Decision;
  severity_level?: number;
  confidence_score?: number;
};

type AgentEvent = {
  type: 'run_started' | 'node_completed' | 'result' | 'run_error';
  status: string;
  node?: string;
  label?: string;
  duration_ms?: number;
  summary?: Record<string, unknown>;
  response?: EvaluationDetail;
  error?: string;
};

const defaultDraft: ClaimDraft = {
  id_kunjungan: 'K-11201',
  nama_pasien: 'Agus Pratama',
  nik: '3201012345678903',
  usia: '55',
  diag_awal: 'Pneumonia Berat',
  diag_sekunder_1: 'Gagal Napas',
  diag_sekunder_2: '',
  tindakan_1: 'Pemasangan Ventilator',
  tindakan_2: '',
  icu_days: '6',
  severity_level: '3',
  biaya_tagih: '28000000',
  durasi_rawat: '12',
  catatan_klinis: '',
  kreatinin: '',
  troponin: '',
  tipe_faskes: 'RSUP Dr. Wahidin Sudirohusodo',
  eeg_attached: false,
};

const statusStyles: Record<Decision, { label: string; mark: string; banner: string; markBox: string; text: string }> = {
  APPROVED: {
    label: 'APPROVED',
    mark: 'OK',
    banner: 'border-green-200 bg-green-50',
    markBox: 'bg-green-100 text-green-700',
    text: 'text-green-700',
  },
  DOWNGRADED: {
    label: 'DOWNGRADED',
    mark: 'DOWN',
    banner: 'border-amber-200 bg-amber-50',
    markBox: 'bg-amber-100 text-amber-700',
    text: 'text-amber-700',
  },
  ESCALATED: {
    label: 'ESCALATED',
    mark: '!',
    banner: 'border-red-200 bg-red-50',
    markBox: 'bg-red-100 text-red-700',
    text: 'text-red-700',
  },
  REJECTED: {
    label: 'REJECTED',
    mark: 'NO',
    banner: 'border-red-200 bg-red-50',
    markBox: 'bg-red-100 text-red-700',
    text: 'text-red-700',
  },
};

const auditItems: Array<{ key: keyof AuditTrail; label: string }> = [
  { key: 'ml_risk_assessment', label: 'ML Risk Assessment' },
  { key: 'pnpk_reference_rule', label: 'Referensi PNPK' },
  { key: 'clinical_inconsistency', label: 'Inkonsistensi Klinis' },
  { key: 'action_recommendation', label: 'Rekomendasi Tindakan' },
];

const masterItems = ['Diagnosa', 'Poli', 'Fasilitas Kesehatan', 'Procedure', 'Kelas Rawat', 'DPJP', 'Dokter', 'Spesialistik'];

function numericValue(value: string, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toClaimRequest(draft: ClaimDraft) {
  return {
    id_kunjungan: draft.id_kunjungan,
    nama_pasien: draft.nama_pasien,
    nik: draft.nik,
    usia: numericValue(draft.usia, 0),
    diag_awal: draft.diag_awal,
    diag_sekunder_1: draft.diag_sekunder_1 || null,
    diag_sekunder_2: draft.diag_sekunder_2 || null,
    tindakan_1: draft.tindakan_1 || null,
    tindakan_2: draft.tindakan_2 || null,
    icu_days: numericValue(draft.icu_days, 0),
    severity_level: numericValue(draft.severity_level, 1),
    biaya_tagih: numericValue(draft.biaya_tagih, 0),
    durasi_rawat: numericValue(draft.durasi_rawat, 1),
    catatan_klinis: draft.catatan_klinis || null,
    kreatinin: draft.kreatinin ? numericValue(draft.kreatinin) : null,
    troponin: draft.troponin ? numericValue(draft.troponin) : null,
    tipe_faskes: draft.tipe_faskes || null,
    eeg_attached: draft.eeg_attached,
  };
}

function readValue(source: Record<string, unknown>, key: string, fallback: string) {
  const value = source[key];
  return value === null || value === undefined ? fallback : String(value);
}

function readBoolean(source: Record<string, unknown>, key: string, fallback: boolean) {
  const value = source[key];
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') return value.toLowerCase() === 'true';
  return fallback;
}

function apiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  return configured.replace(/\/api\/v1\/adjudicate\/?$/, '').replace(/\/$/, '');
}

function MetricCard({ label, value, valueClass = 'text-gray-800' }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="border border-[#dfe5e5] bg-[#f8faf9] px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">{label}</div>
      <div className={`mt-1 text-sm font-semibold ${valueClass}`}>{value}</div>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', placeholder }: { label: string; value: string; onChange: (value: string) => void; type?: string; placeholder?: string }) {
  return (
    <label className="block text-xs text-gray-600">
      <span className="mb-1 block font-medium">{label}</span>
      <input type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} className="h-9 w-full border border-[#d8dddd] bg-white px-2 text-sm text-gray-700 outline-none focus:border-[#28b8b5] focus:ring-1 focus:ring-[#b9e7e5]" />
    </label>
  );
}

export default function VClaimPage() {
  const [draft, setDraft] = useState<ClaimDraft>(defaultDraft);
  const [payloadText, setPayloadText] = useState(JSON.stringify(toClaimRequest(defaultDraft), null, 2));
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<Panel>('console');
  const [activeVClaimTab, setActiveVClaimTab] = useState<VClaimTab>('Monitoring');
  const [activeMasterItem, setActiveMasterItem] = useState('Fasilitas Kesehatan');
  const [providerSearch, setProviderSearch] = useState('Wahidin');
  const [hitlDecision, setHitlDecision] = useState<Decision | null>(null);
  const [hitlNote, setHitlNote] = useState('');
  const [manualSeverity, setManualSeverity] = useState<'1' | '2'>('2');
  const [showDowngradeForm, setShowDowngradeForm] = useState(false);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);
  const [ragFile, setRagFile] = useState<File | null>(null);
  const [ragAuthority, setRagAuthority] = useState('');
  const [ragEffectiveDate, setRagEffectiveDate] = useState('');
  const [ragDisease, setRagDisease] = useState('');
  const [ragIcd10, setRagIcd10] = useState('');
  const [ragRuleType, setRagRuleType] = useState('');
  const [ragDocuments, setRagDocuments] = useState<Array<Record<string, unknown>>>([]);
  const [ragStatus, setRagStatus] = useState<string | null>(null);

  const updateDraft = <K extends keyof ClaimDraft>(key: K, value: ClaimDraft[K]) => {
    setDraft((current) => {
      const next = { ...current, [key]: value };
      setPayloadText(JSON.stringify(toClaimRequest(next), null, 2));
      return next;
    });
  };

  const applyJsonPayload = () => {
    try {
      const parsed: unknown = JSON.parse(payloadText);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('Payload harus berupa object JSON.');
      }
      const source = parsed as Record<string, unknown>;
      setDraft((current) => ({
        ...current,
        id_kunjungan: readValue(source, 'id_kunjungan', current.id_kunjungan),
        nama_pasien: readValue(source, 'nama_pasien', current.nama_pasien),
        nik: readValue(source, 'nik', current.nik),
        usia: readValue(source, 'usia', current.usia),
        diag_awal: readValue(source, 'diag_awal', current.diag_awal),
        diag_sekunder_1: readValue(source, 'diag_sekunder_1', current.diag_sekunder_1),
        diag_sekunder_2: readValue(source, 'diag_sekunder_2', current.diag_sekunder_2),
        tindakan_1: readValue(source, 'tindakan_1', current.tindakan_1),
        tindakan_2: readValue(source, 'tindakan_2', current.tindakan_2),
        icu_days: readValue(source, 'icu_days', current.icu_days),
        severity_level: readValue(source, 'severity_level', current.severity_level),
        biaya_tagih: readValue(source, 'biaya_tagih', current.biaya_tagih),
        durasi_rawat: readValue(source, 'durasi_rawat', current.durasi_rawat),
        catatan_klinis: readValue(source, 'catatan_klinis', current.catatan_klinis),
        kreatinin: readValue(source, 'kreatinin', current.kreatinin),
        troponin: readValue(source, 'troponin', current.troponin),
        tipe_faskes: readValue(source, 'tipe_faskes', current.tipe_faskes),
        eeg_attached: readBoolean(source, 'eeg_attached', current.eeg_attached),
      }));
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Payload JSON tidak valid.');
    }
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);
    setHitlDecision(null);
    setHitlNote('');
    setShowDowngradeForm(false);
    setAgentEvents([]);
    const request = toClaimRequest(draft);
    setPayloadText(JSON.stringify(request, null, 2));

    try {
      const result = await fetch(`${apiBaseUrl()}/api/v1/adjudicate/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!result.ok) throw new Error(`API Error: ${result.status}`);
      if (!result.body) throw new Error('API tidak mengembalikan execution stream.');
      const reader = result.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop() ?? '';
        for (const chunk of chunks) {
          const dataLine = chunk.split('\n').find((line) => line.startsWith('data: '));
          if (!dataLine) continue;
          const event = JSON.parse(dataLine.slice(6)) as AgentEvent;
          setAgentEvents((current) => [...current, event]);
          if (event.type === 'result' && event.response) setResponse({ success: true, metadata: { code: 200, message: 'Evaluasi Selesai' }, response: event.response });
          if (event.type === 'run_error') throw new Error(event.error || 'Workflow gagal.');
        }
        if (done) {
          if (buffer.trim()) {
            const dataLine = buffer.split('\n').find((line) => line.startsWith('data: '));
            if (dataLine) {
              const event = JSON.parse(dataLine.slice(6)) as AgentEvent;
              setAgentEvents((current) => [...current, event]);
              if (event.type === 'result' && event.response) setResponse({ success: true, metadata: { code: 200, message: 'Evaluasi Selesai' }, response: event.response });
            }
          }
          break;
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Gagal mengevaluasi klaim.');
    } finally {
      setLoading(false);
    }
  };

  const loadRagDocuments = async () => {
    try {
      const result = await fetch(`${apiBaseUrl()}/api/v1/rag/documents`);
      if (!result.ok) throw new Error(`API Error: ${result.status}`);
      const data = await result.json() as { documents?: Array<Record<string, unknown>> };
      setRagDocuments(data.documents ?? []);
    } catch (err: unknown) {
      setRagStatus(err instanceof Error ? err.message : 'Gagal memuat manifest RAG.');
    }
  };

  const uploadRagDocument = async () => {
    if (!ragFile) return setRagStatus('Pilih dokumen terlebih dahulu.');
    setRagStatus('Mengindeks dokumen lokal...');
    const form = new FormData();
    form.append('file', ragFile);
    form.append('authority', ragAuthority);
    form.append('effective_date', ragEffectiveDate);
    form.append('disease', ragDisease);
    form.append('icd10', ragIcd10);
    form.append('rule_type', ragRuleType);
    try {
      const result = await fetch(`${apiBaseUrl()}/api/v1/rag/documents`, { method: 'POST', body: form });
      const data = await result.json() as { detail?: string; document?: { duplicate?: boolean; chunk_count?: number } };
      if (!result.ok) throw new Error(data.detail || `API Error: ${result.status}`);
      setRagStatus(data.document?.duplicate ? 'Dokumen sudah pernah diindeks.' : `Dokumen berhasil diindeks (${data.document?.chunk_count ?? 0} chunk).`);
      setRagFile(null);
      await loadRagDocuments();
    } catch (err: unknown) {
      setRagStatus(err instanceof Error ? err.message : 'Gagal mengunggah dokumen RAG.');
    }
  };

  const aiDecision = response?.response.decision;
  const displayedDecision = hitlDecision ?? aiDecision;
  const status = displayedDecision ? statusStyles[displayedDecision] : null;
  const isManual = hitlDecision !== null;

  const selectPanel = (panel: Panel) => setActivePanel(panel);

  const selectVClaimTab = (tab: VClaimTab) => {
    setActiveVClaimTab(tab);
    if (tab === 'Monitoring') setActivePanel('console');
    else if (tab === 'Referensi') setActivePanel('reference');
    else {
      setActiveMasterItem(tab);
      setActivePanel('master');
    }
  };

  const selectMasterItem = (item: string) => {
    setActiveMasterItem(item);
    setActivePanel('master');
  };

  const applyManualDecision = (decision: Decision) => {
    setHitlDecision(decision);
    setShowDowngradeForm(false);
  };

  const renderResponse = () => {
    if (error) return <div className="border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">ERROR: {error}</div>;
    if (!response || !status || !displayedDecision) {
      return <div className="flex min-h-32 items-center justify-center border border-dashed border-[#cfd8d8] bg-white text-sm text-gray-400">Klik &quot;Jalankan Evaluasi GARDA&quot; untuk melihat hasil adjudikasi.</div>;
    }

    return (
      <div className="space-y-3">
        <div className={`flex items-start gap-3 border px-4 py-3 ${status.banner}`}>
          <span className={`flex h-8 min-w-8 items-center justify-center rounded-full text-[9px] font-bold ${status.markBox}`}>{status.mark}</span>
          <div>
            <div className={`text-sm font-bold ${status.text}`}>STATUS: {status.label}{isManual ? ' (MANUAL)' : ''}</div>
            <div className={`mt-1 text-xs ${status.text}`}>{displayedDecision === 'ESCALATED' ? 'Membutuhkan keputusan verifikator medis.' : isManual ? 'Keputusan akhir ditetapkan verifikator medis.' : 'Keputusan otomatis dari GARDA-JKN.'}</div>
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-3">
          <MetricCard label="Keputusan" value={displayedDecision} valueClass={status.text} />
          <MetricCard label="Severity Level" value={String(hitlDecision === 'DOWNGRADED' ? manualSeverity : response.response.severity_level)} />
          <MetricCard label="Confidence" value={`${(response.response.confidence_score * 100).toFixed(1)}%`} valueClass="text-blue-600" />
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <MetricCard label="ML Risk Score" value={`${(response.response.ml_risk_score * 100).toFixed(2)}%`} valueClass="text-orange-600" />
          <MetricCard label="Anomali" value={response.response.is_anomalous ? 'YA' : 'TIDAK'} valueClass={response.response.is_anomalous ? 'text-red-600' : 'text-green-600'} />
        </div>

        {aiDecision === 'ESCALATED' && !hitlDecision ? (
          <div className="border border-red-200 bg-red-50 p-4">
            <h3 className="text-sm font-bold text-red-800">ESCALATED - Membutuhkan Keputusan Verifikator</h3>
            <p className="mt-1 text-sm leading-relaxed text-red-700">AI tidak dapat menetapkan keputusan otomatis. Tinjau alasan, referensi PNPK, dan audit trail sebelum memilih tindakan.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" onClick={() => applyManualDecision('APPROVED')} className="border border-green-700 bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">Setujui Klaim</button>
              <button type="button" onClick={() => setShowDowngradeForm((current) => !current)} className="border border-amber-700 bg-amber-500 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-600">Turunkan Severity</button>
              <button type="button" onClick={() => applyManualDecision('REJECTED')} className="border border-red-700 bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700">Tolak Klaim</button>
            </div>
            {showDowngradeForm ? (
              <div className="mt-3 flex flex-col gap-2 border border-amber-200 bg-amber-50 p-3 sm:flex-row sm:items-end">
                <label className="text-sm font-medium text-amber-900">Severity baru<select value={manualSeverity} onChange={(event) => setManualSeverity(event.target.value as '1' | '2')} className="mt-1 block h-9 border border-amber-300 bg-white px-2 text-sm text-gray-800"><option value="1">Severity Level 1</option><option value="2">Severity Level 2</option></select></label>
                <button type="button" onClick={() => applyManualDecision('DOWNGRADED')} className="h-9 border border-amber-700 bg-amber-600 px-3 text-sm font-semibold text-white hover:bg-amber-700">Konfirmasi Penurunan</button>
              </div>
            ) : null}
            <label className="mt-3 block text-sm font-medium text-red-900">Catatan Verifikator<textarea value={hitlNote} onChange={(event) => setHitlNote(event.target.value)} rows={3} placeholder="Tambahkan alasan keputusan manual..." className="mt-1 w-full resize-y border border-red-200 bg-white p-3 text-sm text-gray-700 outline-none focus:border-red-400 focus:ring-1 focus:ring-red-200" /></label>
          </div>
        ) : null}

        {isManual ? <div className="border border-[#b9e1de] bg-[#effaf9] p-3 text-sm text-[#126f69]"><span className="font-semibold">Keputusan verifikator:</span> {displayedDecision} pada state lokal demo.{hitlNote ? ` Catatan: ${hitlNote}` : ''}</div> : null}
        {response.response.adjudication_reason ? <div className="border border-blue-200 bg-blue-50 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-blue-600">Alasan Adjudikasi</div><div className="mt-1 text-sm leading-relaxed text-gray-700">{response.response.adjudication_reason}</div></div> : null}
        {response.response.data_quality_flags?.length ? <div className="border border-amber-300 bg-amber-50 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-amber-700">Data Quality Hold</div><ul className="mt-1 list-disc pl-5 text-sm leading-relaxed text-amber-900">{response.response.data_quality_flags.map((flag, index) => <li key={`${flag}-${index}`}>{flag}</li>)}</ul><p className="mt-2 text-xs text-amber-800">Nominal biaya perlu dikonfirmasi sebelum klaim dapat disetujui. Ini bukan kesimpulan fraud.</p></div> : null}
        <details className="border border-[#dfe5e5] bg-white"><summary className="cursor-pointer px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500 hover:bg-gray-50">Raw JSON Response</summary><pre className="json-area max-h-64 overflow-auto border-t border-[#dfe5e5] bg-gray-50 p-3 text-xs text-gray-600">{JSON.stringify(response, null, 2)}</pre></details>
      </div>
    );
  };

  const renderConsole = () => (
    <div className="space-y-3">
      <div className="flex items-center justify-between border-b border-[#dfe5e5] pb-2">
        <div><h1 className="text-base font-medium text-gray-800">Console Evaluasi GARDA-JKN</h1><p className="mt-1 text-xs text-gray-500">High-speed screening, clinical RAG, validator, dan keputusan adjudikasi.</p></div>
        <span className="hidden border border-[#b8dfdd] bg-[#effaf9] px-2 py-1 text-[10px] font-semibold uppercase text-[#168f86] sm:inline-block">Human-in-the-loop ready</span>
      </div>

      <section className="border border-[#dfe5e5] bg-white">
        <div className="flex flex-col gap-2 border-b border-[#dfe5e5] bg-[#f2f6f5] px-3 py-2 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-sm font-semibold text-gray-700">Data Klaim</h2><p className="text-[11px] text-gray-500">Form ini dikonversi ke kontrak `ClaimData` backend GARDA-JKN.</p></div><button type="button" onClick={handleEvaluate} disabled={loading} className={`${loading ? 'bg-gray-400' : 'bg-[#27b8b5] hover:bg-[#1da19f]'} h-9 border border-[#1d9e9b] px-4 text-sm font-semibold text-white`}>{loading ? 'Mengevaluasi...' : 'Jalankan Evaluasi GARDA'}</button></div>
        <div className="grid gap-x-3 gap-y-3 p-3 md:grid-cols-2 xl:grid-cols-4">
          <Field label="No. Kunjungan / SEP" value={draft.id_kunjungan} onChange={(value) => updateDraft('id_kunjungan', value)} />
          <Field label="Nama Pasien" value={draft.nama_pasien} onChange={(value) => updateDraft('nama_pasien', value)} />
          <Field label="NIK" value={draft.nik} onChange={(value) => updateDraft('nik', value)} />
          <Field label="Usia" type="number" value={draft.usia} onChange={(value) => updateDraft('usia', value)} />
          <Field label="Diagnosa Utama / ICD-10" value={draft.diag_awal} onChange={(value) => updateDraft('diag_awal', value)} />
           <Field label="Diagnosa Sekunder 1" value={draft.diag_sekunder_1} onChange={(value) => updateDraft('diag_sekunder_1', value)} />
           <Field label="Diagnosa Sekunder 2" value={draft.diag_sekunder_2} onChange={(value) => updateDraft('diag_sekunder_2', value)} placeholder="Opsional" />
           <Field label="Tindakan / Procedure" value={draft.tindakan_1} onChange={(value) => updateDraft('tindakan_1', value)} />
           <Field label="Tindakan 2" value={draft.tindakan_2} onChange={(value) => updateDraft('tindakan_2', value)} placeholder="Opsional" />
          <Field label="Fasilitas Kesehatan" value={draft.tipe_faskes} onChange={(value) => updateDraft('tipe_faskes', value)} />
          <Field label="Severity Level" type="number" value={draft.severity_level} onChange={(value) => updateDraft('severity_level', value)} />
          <Field label="Biaya Tagih (Rp)" type="number" value={draft.biaya_tagih} onChange={(value) => updateDraft('biaya_tagih', value)} />
          <Field label="Lama Rawat (hari)" type="number" value={draft.durasi_rawat} onChange={(value) => updateDraft('durasi_rawat', value)} />
          <Field label="ICU (hari)" type="number" value={draft.icu_days} onChange={(value) => updateDraft('icu_days', value)} />
          <Field label="Kreatinin" type="number" value={draft.kreatinin} onChange={(value) => updateDraft('kreatinin', value)} placeholder="Opsional" />
          <Field label="Troponin" type="number" value={draft.troponin} onChange={(value) => updateDraft('troponin', value)} placeholder="Opsional" />
          <label className="flex items-center gap-2 self-end border border-[#d8dddd] px-2 py-2 text-xs text-gray-600"><input type="checkbox" checked={draft.eeg_attached} onChange={(event) => updateDraft('eeg_attached', event.target.checked)} /> Lampiran EEG tersedia</label>
          <label className="block text-xs text-gray-600 md:col-span-2 xl:col-span-1"><span className="mb-1 block font-medium">Catatan Klinis</span><input value={draft.catatan_klinis} onChange={(event) => updateDraft('catatan_klinis', event.target.value)} className="h-9 w-full border border-[#d8dddd] px-2 text-sm outline-none focus:border-[#28b8b5]" placeholder="Opsional" /></label>
        </div>
        <details className="border-t border-[#dfe5e5] bg-[#fbfcfc]">
          <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-gray-500">Mode Advanced: lihat / terapkan raw JSON</summary>
          <div className="p-3"><textarea aria-label="Raw JSON payload" value={payloadText} onChange={(event) => setPayloadText(event.target.value)} rows={8} className="json-area w-full border border-[#d8dddd] bg-white p-3 font-mono text-xs text-gray-700 outline-none focus:border-[#28b8b5]" /><button type="button" onClick={applyJsonPayload} className="mt-2 border border-gray-400 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50">Terapkan JSON ke Form</button></div>
        </details>
      </section>

       <section><div className="mb-2 flex items-center justify-between"><h2 className="text-sm font-semibold text-gray-700">Respon Evaluasi</h2><span className="text-[11px] text-gray-400">AI result + keputusan verifikator</span></div>{renderResponse()}</section>
       {renderTrace()}
    </div>
  );

  const renderAudit = () => {
    const audit = response?.response.audit_trail ?? {};
    return <section className="border border-[#dfe5e5] bg-white"><div className="border-b border-[#dfe5e5] bg-[#f2f6f5] px-3 py-2"><h1 className="text-sm font-semibold text-gray-700">Log Audit SHAP</h1><p className="mt-1 text-xs text-gray-500">Jejak penalaran yang menyertai keputusan adjudikasi.</p></div><div className="grid gap-2 p-3 md:grid-cols-2">{auditItems.map((item) => <div key={item.key} className="border border-[#dfe5e5] bg-[#f8faf9] p-3"><div className="text-[10px] font-semibold uppercase tracking-wide text-[#168f86]">{item.label}</div><p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-700">{audit[item.key] || 'Belum ada data audit. Jalankan evaluasi terlebih dahulu.'}</p></div>)}</div>{response?.response.reason_codes.length ? <div className="border-t border-[#dfe5e5] p-3"><div className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Reason Codes</div><ul className="mt-2 space-y-1">{response.response.reason_codes.map((reason, index) => <li key={`${reason}-${index}`} className="border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-800">{reason}</li>)}</ul></div> : null}</section>;
  };

  const renderTrace = () => (
    <section className="border border-[#dfe5e5] bg-white">
      <div className="border-b border-[#dfe5e5] bg-[#f2f6f5] px-3 py-2">
        <h2 className="text-sm font-semibold text-gray-700">Proses AI</h2>
        <p className="mt-1 text-xs text-gray-500">Status node workflow yang aman ditampilkan ke verifikator, tanpa prompt atau chain-of-thought.</p>
      </div>
      <div className="p-3">
        {!agentEvents.length ? <div className="border border-dashed border-gray-300 p-5 text-center text-sm text-gray-400">Belum ada execution trace.</div> : (
          <ol className="space-y-2">
            {agentEvents.map((event, index) => (
              <li key={`${event.type}-${event.node}-${index}`} className={`border px-3 py-2 text-sm ${event.type === 'run_error' ? 'border-red-200 bg-red-50' : event.type === 'result' ? 'border-green-200 bg-green-50' : 'border-[#dfe5e5] bg-[#f8faf9]'}`}>
                <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-semibold text-gray-700">{event.label || event.node || event.type}</span><span className="text-[11px] text-gray-500">{event.duration_ms ? `${event.duration_ms} ms` : event.status}</span></div>
                {event.error ? <p className="mt-1 text-red-700">{event.error}</p> : null}
                {event.summary ? <pre className="json-area mt-2 overflow-auto text-[11px] text-gray-600">{JSON.stringify(event.summary, null, 2)}</pre> : null}
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );

  const renderRag = () => <section className="space-y-3 border border-[#dfe5e5] bg-white"><div className="border-b border-[#dfe5e5] bg-[#f2f6f5] px-3 py-2"><h1 className="text-sm font-semibold text-gray-700">Database RAG (PNPK)</h1><p className="mt-1 text-xs text-gray-500">Unggah referensi resmi dengan provenance sebelum dipakai validator.</p></div><div className="grid gap-2 p-3 sm:grid-cols-2"><label className="text-xs text-gray-600 sm:col-span-2"><span className="mb-1 block font-medium">Dokumen PDF/MD/TXT/JSON</span><input type="file" accept=".pdf,.md,.markdown,.txt,.json" onChange={(event) => setRagFile(event.target.files?.[0] ?? null)} className="block w-full border border-[#d8dddd] bg-white p-2 text-sm" /></label><Field label="Authority / penerbit" value={ragAuthority} onChange={setRagAuthority} placeholder="Permenkes / PNPK / BPJS" /><Field label="Tanggal berlaku" type="date" value={ragEffectiveDate} onChange={setRagEffectiveDate} /><Field label="Disease / clinical area" value={ragDisease} onChange={setRagDisease} placeholder="Pneumonia" /><Field label="ICD-10" value={ragIcd10} onChange={setRagIcd10} placeholder="J18.9" /><Field label="Rule type" value={ragRuleType} onChange={setRagRuleType} placeholder="medical_necessity" /><div className="flex items-end gap-2"><button type="button" onClick={uploadRagDocument} className="h-9 border border-[#1d9e9b] bg-[#27b8b5] px-3 text-sm font-semibold text-white hover:bg-[#1da19f]">Upload & Index</button><button type="button" onClick={loadRagDocuments} className="h-9 border border-gray-400 bg-white px-3 text-sm font-semibold text-gray-700 hover:bg-gray-50">Refresh</button></div></div>{ragStatus ? <div className="mx-3 mb-3 border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800">{ragStatus}</div> : null}<div className="border-t border-[#dfe5e5] p-3"><h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Manifest Lokal</h2>{ragDocuments.length ? <div className="mt-2 space-y-2">{ragDocuments.map((document, index) => <div key={`${String(document.document_id)}-${index}`} className="border border-[#dfe5e5] bg-[#f8faf9] p-2 text-xs text-gray-600"><span className="font-semibold">{String(document.source ?? 'Dokumen')}</span> | {String(document.authority ?? '-')} | {String(document.effective_date ?? '-')} | {String(document.chunk_count ?? 0)} chunk</div>)}</div> : <p className="mt-2 text-sm text-gray-400">Belum ada dokumen yang diindeks pada manifest.</p>}</div><div className="border-t border-[#dfe5e5] p-3">{response?.response.rag_context ? <div className="whitespace-pre-wrap border border-purple-200 bg-purple-50 p-3 text-sm leading-relaxed text-gray-700">{response.response.rag_context}</div> : <div className="border border-dashed border-gray-300 p-5 text-center text-sm text-gray-400">Jalankan evaluasi untuk melihat referensi yang dipakai.</div>}</div></section>;

  const renderMetrics = () => <section className="border border-[#dfe5e5] bg-white"><div className="border-b border-[#dfe5e5] bg-[#f2f6f5] px-3 py-2"><h1 className="text-sm font-semibold text-gray-700">Metrik Akurasi</h1><p className="mt-1 text-xs text-gray-500">Ringkasan operasional evaluasi klaim terakhir.</p></div><div className="grid gap-2 p-3 sm:grid-cols-2 lg:grid-cols-4"><MetricCard label="Status" value={displayedDecision ?? 'Belum ada'} valueClass={status?.text ?? 'text-gray-400'} /><MetricCard label="ML Risk" value={response ? `${(response.response.ml_risk_score * 100).toFixed(1)}%` : '-'} valueClass="text-orange-600" /><MetricCard label="Confidence" value={response ? `${(response.response.confidence_score * 100).toFixed(1)}%` : '-'} valueClass="text-blue-600" /><MetricCard label="Severity" value={response ? String(response.response.severity_level) : '-'} /></div></section>;

  const renderReference = () => <section className="border border-[#dfe5e5] bg-white"><div className="border-b border-[#dfe5e5] bg-[#f2f6f5] px-3 py-2"><h1 className="text-sm font-semibold text-gray-700">Referensi Fasilitas Kesehatan</h1><p className="mt-1 text-xs text-gray-500">Tampilan referensi mengikuti pola VClaim; data adjudikasi tetap berada di Console Evaluasi GARDA.</p></div><div className="flex flex-col gap-2 border-b border-[#dfe5e5] p-2 sm:flex-row"><input value={providerSearch} onChange={(event) => setProviderSearch(event.target.value)} className="h-9 min-w-0 flex-1 border border-[#d8dddd] px-2 text-sm outline-none focus:border-[#28b8b5]" placeholder="Cari nama provider" /><select className="h-9 border border-[#d8dddd] bg-white px-2 text-sm text-gray-600"><option>Faskes 2/RS</option><option>Faskes 1</option></select><button type="button" onClick={() => setActivePanel('reference')} className="h-9 border border-[#269e9c] bg-[#7bb5c1] px-4 text-sm font-semibold text-white hover:bg-[#69a7b4]">Cari</button></div><div className="overflow-x-auto"><table className="w-full min-w-[560px] border-collapse text-left text-sm"><thead className="bg-[#f5f7f7] text-xs text-gray-600"><tr><th className="border-b border-[#dfe5e5] px-3 py-2 font-medium">Kode Provider</th><th className="border-b border-[#dfe5e5] px-3 py-2 font-medium">Nama Provider</th><th className="border-b border-[#dfe5e5] px-3 py-2 font-medium">Kode Cabang</th><th className="border-b border-[#dfe5e5] px-3 py-2 font-medium">Nama Cabang</th></tr></thead><tbody><tr><td className="border-b border-[#edf0f0] px-3 py-3 text-gray-600">1801R001</td><td className="border-b border-[#edf0f0] px-3 py-3 font-medium text-gray-700">{providerSearch || 'RSUP.DR.WAHIDIN SUDIROHUSODO'}</td><td className="border-b border-[#edf0f0] px-3 py-3 text-gray-600">-</td><td className="border-b border-[#edf0f0] px-3 py-3 text-gray-600">-</td></tr></tbody></table></div></section>;

  const renderMaster = () => <section className="border border-[#dfe5e5] bg-white"><div className="border-b border-[#dfe5e5] bg-[#f2f6f5] px-3 py-2"><h1 className="text-sm font-semibold text-gray-700">{activeMasterItem}</h1><p className="mt-1 text-xs text-gray-500">Modul referensi SIMRS untuk {activeMasterItem}. Aksi adjudikasi GARDA tersedia melalui Console Evaluasi.</p></div><div className="flex min-h-48 items-center justify-center p-8 text-center text-sm text-gray-400">Belum ada operasi backend GARDA untuk modul {activeMasterItem}. Gunakan <button type="button" onClick={() => setActivePanel('console')} className="mx-1 font-semibold text-[#168f86] underline">Console Evaluasi</button> untuk memproses klaim.</div></section>;

  const globalMenu = ['Penyedia', 'Barang', 'Paket', 'Paket Tindakan Farmasi', 'Group Tindakan Lab', 'Tarif', 'Margin Obat', 'Mapping Penjamin', 'BPJS'];
  const vclaimTabs: VClaimTab[] = ['Referensi', 'Peserta', 'SEP', 'Rujukan', 'Monitoring', 'Rencana Kontrol'];

  return (
    <div className="min-h-screen bg-[#edf3f1] font-sans text-gray-700 antialiased">
      <header className="flex h-14 items-center border-b border-[#d5dddd] bg-white text-gray-700">
        <div className="flex h-full w-56 shrink-0 items-center gap-2 border-r border-[#d5dddd] px-2"><span className="flex h-8 w-8 items-center justify-center rounded-full border-4 border-[#35bec0] text-[10px] font-bold text-[#159e9d]">HS</span><div className="leading-tight"><div className="text-sm font-semibold tracking-tight text-[#168f86]">SIMGOS 2</div><div className="text-[7px] text-gray-400">Sistem Informasi Manajemen Rumah Sakit</div></div></div>
        <button type="button" aria-label="Buka menu" className="flex h-full w-12 items-center justify-center border-r border-[#d5dddd] text-xl text-gray-500 hover:bg-gray-50">=</button>
        <div className="hidden items-center gap-3 px-5 md:flex"><span className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-[#1785a0] text-sm font-bold text-[#dc3b36]">W</span><span className="text-base font-medium">RSUP. Dr. Wahidin Sudirohusodo</span></div>
        <div className="ml-auto flex min-w-0 items-center"><select className="hidden h-14 border-l border-r border-[#d5dddd] bg-white px-4 text-sm font-medium outline-none lg:block"><option>PASIEN</option></select><input className="hidden h-9 w-72 border-none px-4 text-sm outline-none xl:block" placeholder="Cari Pasien dgn Memasukkan No.RM/No.KTP/No.Kartu BPJS/Nama" /><div className="flex gap-4 px-4 text-gray-500"><span title="Cari">?</span><span title="Tambah pengguna">+</span><span title="Menu">=</span><span title="Folder">[]</span><span title="Keluar">&gt;</span></div></div>
      </header>

      <div className="flex h-11 items-center border-b border-[#d5dddd] bg-white px-2 text-sm"><button type="button" className="px-3 text-lg text-gray-600">^</button><button type="button" className="flex h-9 items-center gap-2 border-l-4 border-[#35c96d] bg-[#eef3f2] px-4 font-medium">Master <span className="text-gray-400">x</span></button></div>
      <div className="flex h-9 items-center justify-between bg-[#686667] px-3 text-sm text-white"><span><span className="mr-3 text-gray-300">=</span>Master - BPJS</span><span className="text-xs text-gray-300">EXPAND</span></div>

      <div className="flex min-h-[calc(100vh-6.5rem)] flex-col lg:flex-row">
        <aside className="hidden w-64 shrink-0 border-r border-[#d5dddd] bg-white lg:block"><nav>{globalMenu.map((item) => <button type="button" key={item} className={`${item === 'BPJS' ? 'border-l-4 border-l-[#61ed7d] bg-[#e5e9e9] font-semibold' : 'border-b border-[#e5e5e5]'} flex w-full items-center gap-4 px-5 py-3 text-left text-sm hover:bg-[#f1f6f5]`}><span className="w-5 text-center text-xs text-gray-700">{item === 'BPJS' ? 'B' : '+'}</span>{item}</button>)}</nav></aside>

        <main className="min-w-0 flex-1">
          <div className="flex h-10 items-center justify-between bg-[#2ebebb] px-3 text-white"><span className="font-medium"><span className="mr-3">=</span><span className="mr-2">B</span>BPJS - VClaim</span><span className="text-xs text-white/70">GARDA-JKN connected</span></div>
          <div className="flex flex-col xl:flex-row">
            <aside className="w-full shrink-0 bg-white xl:w-40"><div className="flex xl:block">{['VClaim', 'Aplicares'].map((item) => <button type="button" key={item} className={`${item === 'VClaim' ? 'border-l-4 border-l-[#62ed7d] bg-[#e3e7e7] font-medium' : 'border-l-4 border-l-transparent'} flex-1 px-4 py-4 text-center text-sm hover:bg-[#f1f6f5] xl:w-full`}>{item}</button>)}</div></aside>
            <section className="min-w-0 flex-1 bg-[#edf3f1]">
              <div className="flex overflow-x-auto border-b border-[#d5dddd] bg-[#e9efed] whitespace-nowrap">{vclaimTabs.map((tab) => <button type="button" key={tab} onClick={() => selectVClaimTab(tab)} className={`${activeVClaimTab === tab ? 'border-b-2 border-[#63c9d3] bg-[#7db5c2] text-white' : 'text-gray-600 hover:bg-white'} px-4 py-3 text-sm`}>{tab}</button>)}</div>
              <div className="p-2 sm:p-3">{activePanel === 'console' ? renderConsole() : activePanel === 'audit' ? renderAudit() : activePanel === 'rag' ? renderRag() : activePanel === 'metrics' ? renderMetrics() : activePanel === 'reference' ? renderReference() : renderMaster()}</div>
            </section>
             <aside className="w-full shrink-0 bg-[#edf3f1] xl:w-44"><nav className="border-t border-[#d5dddd] xl:border-l xl:border-t-0">{masterItems.map((item) => <button type="button" key={item} onClick={() => selectMasterItem(item)} className={`${activePanel === 'master' && activeMasterItem === item ? 'bg-[#7db5c2] font-medium text-white' : 'text-gray-600 hover:bg-white'} block w-full px-3 py-3 text-left text-sm`}>{item}</button>)}<div className="mt-2 border-t border-[#d5dddd] px-3 py-2 text-[10px] font-bold uppercase tracking-wide text-[#168f86]">GARDA-JKN</div><button type="button" onClick={() => selectPanel('console')} className={`${activePanel === 'console' ? 'bg-[#2ebebb] font-semibold text-white' : 'text-gray-600 hover:bg-white'} block w-full px-3 py-3 text-left text-sm`}>Console Evaluasi</button><button type="button" onClick={() => selectPanel('audit')} className={`${activePanel === 'audit' ? 'bg-[#d8f1ef] font-semibold text-[#168f86]' : 'text-gray-600 hover:bg-white'} block w-full px-3 py-3 text-left text-sm`}>Log Audit SHAP</button><button type="button" onClick={() => { selectPanel('rag'); void loadRagDocuments(); }} className={`${activePanel === 'rag' ? 'bg-[#d8f1ef] font-semibold text-[#168f86]' : 'text-gray-600 hover:bg-white'} block w-full px-3 py-3 text-left text-sm`}>Database RAG</button><button type="button" onClick={() => selectPanel('metrics')} className={`${activePanel === 'metrics' ? 'bg-[#d8f1ef] font-semibold text-white' : 'text-gray-600 hover:bg-white'} block w-full px-3 py-3 text-left text-sm`}>Metrik Akurasi</button></nav></aside>
          </div>
        </main>
      </div>
    </div>
  );
}
