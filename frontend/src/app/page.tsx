'use client';

import { useState } from 'react';

const defaultClaim = `{
  "id_kunjungan": "K-11201",
  "nama_pasien": "Agus Pratama",
  "nik": "3201012345678903",
  "usia": 55,
  "diag_awal": "Pneumonia Berat",
  "diag_sekunder_1": "Gagal Napas",
  "tindakan_1": "Pemasangan Ventilator",
  "icu_days": 6,
  "severity_level": 3,
  "biaya_tagih": 28000000,
  "durasi_rawat": 12
}`;

export default function VClaimPage() {
  const [payload, setPayload] = useState(defaultClaim);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    try {
      const parsedPayload = JSON.parse(payload);
      // In production, this points to your Render.com / Railway FastAPI URL
      // For now, it points to local if testing locally
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://web-production-c93a2.up.railway.app/api/v1/adjudicate';
      
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsedPayload)
      });
      
      if (!res.ok) {
        throw new Error(`API Error: ${res.status}`);
      }
      
      const data = await res.json();
      setResponse(data);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate claim.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-100 text-gray-800 antialiased h-screen flex flex-col overflow-hidden font-sans">
      
      {/* Top Header */}
      <header className="bg-[#1db2a6] h-12 flex items-center justify-between px-4 text-white shadow-sm shrink-0 z-10">
          <div className="flex items-center space-x-3">
              <svg className="w-5 h-5 cursor-pointer" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
              <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                  <span className="font-semibold tracking-wide">BPJS - VClaim</span>
              </div>
          </div>
          <div className="flex items-center space-x-4 text-sm">
              <span>User: RSUP Dr. Wahidin S.</span>
              <svg className="w-4 h-4 cursor-pointer" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
          </div>
      </header>
  
      <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar */}
          <aside className="w-48 bg-white border-r border-gray-200 shrink-0 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)] z-0">
              <nav className="flex flex-col mt-2">
                  <a href="#" className="px-5 py-3 text-sm text-gray-800 bg-gray-50 border-l-4 border-l-[#1db2a6] font-medium flex items-center justify-between">
                      VClaim
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
                  </a>
                  <a href="#" className="px-5 py-3 text-sm text-gray-600 hover:bg-gray-50 border-l-4 border-l-transparent flex items-center justify-between">
                      Aplicares
                  </a>
                  
                  <div className="mt-6 mb-2 px-5 text-xs font-semibold text-gray-400 uppercase tracking-wider">AI Modules</div>
                  <a href="#" className="px-5 py-3 text-sm text-[#1db2a6] hover:bg-[#e6f7f5] border-l-4 border-l-[#1db2a6] font-medium flex items-center justify-between shadow-sm relative overflow-hidden group">
                      <span className="relative z-10 flex items-center space-x-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                          <span>GARDA-JKN</span>
                      </span>
                  </a>
              </nav>
          </aside>
  
          {/* Main Content */}
          <main className="flex-1 flex flex-col bg-white overflow-hidden relative">
              {/* Top Tabs */}
              <div className="flex items-center border-b border-gray-200 bg-gray-50 px-2 shrink-0">
                  <a href="#" className="px-6 py-3 text-sm text-gray-600 hover:text-[#1db2a6] font-medium border-b-2 border-transparent">Referensi</a>
                  <a href="#" className="px-6 py-3 text-sm text-gray-600 hover:text-[#1db2a6] font-medium border-b-2 border-transparent">Peserta</a>
                  <a href="#" className="px-6 py-3 text-sm text-gray-600 hover:text-[#1db2a6] font-medium border-b-2 border-transparent">SEP</a>
                  <a href="#" className="px-6 py-3 text-sm text-gray-600 hover:text-[#1db2a6] font-medium border-b-2 border-transparent">Rujukan</a>
                  <a href="#" className="px-6 py-3 text-sm text-gray-600 hover:text-[#1db2a6] font-medium border-b-2 border-transparent">Monitoring</a>
                  <a href="#" className="px-6 py-3 text-sm text-white bg-[#1db2a6] font-medium border-b-2 border-[#1db2a6] shadow-inner">GARDA-JKN Evaluator</a>
              </div>
  
              {/* Content Area */}
              <div className="flex flex-1 overflow-hidden">
                  <div className="flex-1 p-6 flex flex-col overflow-y-auto">
                      <div className="mb-6 pb-4 border-b border-gray-100 flex items-center justify-between">
                          <div>
                              <h1 className="text-lg font-medium text-gray-800">Adjudikasi AI Cerdas (GARDA-JKN)</h1>
                              <p className="text-xs text-gray-500 mt-1">Evaluasi Payload Klaim menggunakan XGBoost & LangGraph</p>
                          </div>
                          <button 
                            onClick={handleEvaluate}
                            disabled={loading}
                            className={`${loading ? 'bg-gray-400' : 'bg-[#1db2a6] hover:bg-[#159a8f]'} text-white text-sm px-4 py-2 rounded flex items-center space-x-2 transition-colors shadow-sm`}
                          >
                              {loading ? (
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                              )}
                              <span>{loading ? 'Mengevaluasi...' : 'Jalankan Evaluasi'}</span>
                          </button>
                      </div>
  
                      <div className="flex space-x-6 h-full">
                          {/* Left: JSON Input */}
                          <div className="w-1/2 flex flex-col h-full">
                              <label className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                  Payload Tindakan & Tagihan (JSON)
                              </label>
                              <textarea 
                                className="flex-1 w-full border border-gray-300 rounded p-4 font-mono text-sm text-gray-700 bg-gray-50 focus:border-[#1db2a6] focus:ring-1 focus:ring-[#1db2a6] outline-none resize-none shadow-inner" 
                                spellCheck="false"
                                value={payload}
                                onChange={(e) => setPayload(e.target.value)}
                              />
                          </div>
  
                          {/* Right: Output Area */}
                          <div className="w-1/2 flex flex-col h-full">
                              <label className="text-sm font-medium text-gray-700 mb-2">
                                  Respon Evaluasi
                              </label>
                              <div className="flex-1 border border-gray-300 rounded bg-white overflow-hidden flex flex-col">
                                  {error ? (
                                    <div className="bg-red-50 border-b border-red-200 px-4 py-3 flex items-start space-x-3">
                                      <div className="text-sm font-bold text-red-700">ERROR: {error}</div>
                                    </div>
                                  ) : response ? (
                                    <>
                                      {/* AI Status Banner */}
                                      <div className={`${response.response.decision === 'APPROVED' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} border-b px-4 py-3 flex items-start space-x-3`}>
                                          <svg className={`w-5 h-5 ${response.response.decision === 'APPROVED' ? 'text-green-500' : 'text-red-500'} mt-0.5`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                                          <div>
                                              <div className={`text-sm font-bold ${response.response.decision === 'APPROVED' ? 'text-green-700' : 'text-red-700'}`}>STATUS: {response.response.decision}</div>
                                              <div className={`text-xs ${response.response.decision === 'APPROVED' ? 'text-green-600' : 'text-red-600'} mt-0.5`}>Skor Risiko: {(response.response.ml_risk_score * 100).toFixed(1)}%</div>
                                          </div>
                                      </div>
                                      
                                      {/* Detailed JSON Response */}
                                      <div className="p-4 font-mono text-sm text-gray-700 overflow-y-auto json-area whitespace-pre">
                                        {JSON.stringify(response, null, 2)}
                                      </div>
                                    </>
                                  ) : (
                                    <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
                                      Klik "Jalankan Evaluasi" untuk melihat hasil.
                                    </div>
                                  )}
                              </div>
                          </div>
                      </div>
                  </div>
  
                  {/* Right Sub-Menu */}
                  <aside className="w-56 bg-gray-50 border-l border-gray-200 shrink-0 overflow-y-auto shadow-inner">
                      <nav className="flex flex-col text-sm text-gray-600">
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer">Diagnosa</div>
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer border-b border-gray-200">Poli</div>
                          
                          <div className="bg-gray-200 px-5 py-1 text-xs font-semibold text-gray-500 uppercase">GARDA-JKN</div>
                          <div className="px-5 py-3 bg-[#1db2a6] text-white font-medium cursor-pointer shadow-sm">Console Evaluasi</div>
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer">Log Audit SHAP</div>
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer">Database RAG (PNPK)</div>
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer">Metrik Akurasi</div>
                          
                          <div className="bg-gray-200 px-5 py-1 text-xs font-semibold text-gray-500 uppercase mt-2">Master Lainnya</div>
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer">Fasilitas Kesehatan</div>
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer">Procedure</div>
                          <div className="px-5 py-3 hover:bg-gray-100 cursor-pointer">Kelas Rawat</div>
                      </nav>
                  </aside>
              </div>
          </main>
      </div>
    </div>
  );
}
