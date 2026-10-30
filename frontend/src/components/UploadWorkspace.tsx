import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, X, Sparkles, Cpu, Shield, ArrowRight } from 'lucide-react';

interface UploadWorkspaceProps {
  onStartComparison: (oldFile: File, newFile: File, provider: string, geminiApiKey?: string) => void;
  isLoading: boolean;
}

export const UploadWorkspace: React.FC<UploadWorkspaceProps> = ({ onStartComparison, isLoading }) => {
  const [oldFile, setOldFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);
  const [provider, setProvider] = useState<string>('deterministic');
  const [geminiApiKey, setGeminiApiKey] = useState<string>(() => localStorage.getItem('docudiff_gemini_key') || '');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const oldInputRef = useRef<HTMLInputElement>(null);
  const newInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, isOld: boolean) => {
    setErrorMsg(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (!['.pdf', '.docx', '.txt', '.md'].includes(ext)) {
        setErrorMsg(`Format '${ext}' is unsupported. Please upload a PDF, Word (DOCX), or plain text file.`);
        return;
      }
      if (isOld) {
        setOldFile(file);
      } else {
        setNewFile(file);
      }
    }
  };

  const loadSampleFiles = async () => {
    setErrorMsg(null);
    try {
      const sampleOldText = `Employee Leave Policy
Employees may carry forward up to 15 days of unused leave.
A leave request must be submitted at least 7 days before planned travel.
The system should retain access logs for 30 days.
Access is permitted for approved administrators only.
Unused medical leave is not transferable.`;

      const sampleNewText = `Employee Leave Policy
Employees may carry forward up to 10 days of unused leave.
A leave request must be submitted at least 5 days before planned travel.
The system must retain access logs for 30 days.
Access is permitted for approved administrators and auditors.
Unused medical leave is not transferable.
Emergency access requests require manager approval.`;

      const oldBlob = new Blob([sampleOldText], { type: 'text/plain' });
      const newBlob = new Blob([sampleNewText], { type: 'text/plain' });

      const fileOld = new File([oldBlob], 'policy_v1.txt', { type: 'text/plain' });
      const fileNew = new File([newBlob], 'policy_v2.txt', { type: 'text/plain' });

      setOldFile(fileOld);
      setNewFile(fileNew);
    } catch (err) {
      setErrorMsg('Failed to load sample policy files.');
    }
  };

  const handleCompare = () => {
    if (!oldFile || !newFile) {
      setErrorMsg('Please select both an Old Version and a New Version file to compare.');
      return;
    }
    setErrorMsg(null);
    if (geminiApiKey.trim()) {
      localStorage.setItem('docudiff_gemini_key', geminiApiKey.trim());
    }
    onStartComparison(oldFile, newFile, provider, geminiApiKey.trim());
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Intelligent Document Change Analyzer
        </h2>
        <p className="mt-2 text-sm text-slate-600 max-w-xl mx-auto">
          Upload two document revisions to trace clause-level modifications, modal shifts, numeric thresholds, and review priorities.
        </p>
        <div className="mt-4 flex justify-center">
          <button
            type="button"
            onClick={loadSampleFiles}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Load Policy Benchmark Sample</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-center space-x-3 text-red-700 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Upload Dual Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Old Version */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Baseline Version</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium">Original (Old)</span>
            </div>

            {oldFile ? (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 relative">
                <button
                  onClick={() => setOldFile(null)}
                  className="absolute top-3 right-3 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="flex items-start space-x-3">
                  <div className="p-2.5 bg-blue-100 text-blue-700 rounded-lg">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800 break-all">{oldFile.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{formatFileSize(oldFile.size)}</p>
                    <span className="inline-flex items-center space-x-1 text-xs text-emerald-600 font-medium mt-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Ready for analysis</span>
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div
                onClick={() => oldInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-8 text-center cursor-pointer transition bg-slate-50/50 hover:bg-blue-50/30 flex flex-col items-center justify-center min-h-[170px]"
              >
                <div className="p-3 bg-white rounded-full shadow-xs text-blue-600 mb-2">
                  <Upload className="w-5 h-5" />
                </div>
                <p className="text-sm font-semibold text-slate-700">Choose baseline document</p>
                <p className="text-xs text-slate-400 mt-1">PDF, Word (DOCX), or plain TXT</p>
                <input
                  ref={oldInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  className="hidden"
                  onChange={(e) => handleFileChange(e, true)}
                />
              </div>
            )}
          </div>

          {oldFile && (
            <button
              onClick={() => oldInputRef.current?.click()}
              className="mt-4 text-xs font-medium text-slate-500 hover:text-blue-600 text-center"
            >
              Replace baseline document
            </button>
          )}
        </div>

        {/* New Version */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Revised Version</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium border border-emerald-200">New Version</span>
            </div>

            {newFile ? (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 relative">
                <button
                  onClick={() => setNewFile(null)}
                  className="absolute top-3 right-3 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="flex items-start space-x-3">
                  <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-lg">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800 break-all">{newFile.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{formatFileSize(newFile.size)}</p>
                    <span className="inline-flex items-center space-x-1 text-xs text-emerald-600 font-medium mt-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Ready for analysis</span>
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div
                onClick={() => newInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-8 text-center cursor-pointer transition bg-slate-50/50 hover:bg-emerald-50/30 flex flex-col items-center justify-center min-h-[170px]"
              >
                <div className="p-3 bg-white rounded-full shadow-xs text-emerald-600 mb-2">
                  <Upload className="w-5 h-5" />
                </div>
                <p className="text-sm font-semibold text-slate-700">Choose revised document</p>
                <p className="text-xs text-slate-400 mt-1">PDF, Word (DOCX), or plain TXT</p>
                <input
                  ref={newInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  className="hidden"
                  onChange={(e) => handleFileChange(e, false)}
                />
              </div>
            )}
          </div>

          {newFile && (
            <button
              onClick={() => newInputRef.current?.click()}
              className="mt-4 text-xs font-medium text-slate-500 hover:text-emerald-600 text-center"
            >
              Replace revised document
            </button>
          )}
        </div>
      </div>

      {/* Options and Compare Button */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <label className="text-xs font-semibold text-slate-600 whitespace-nowrap">AI Reasoning Provider:</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="text-xs font-medium bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 w-full sm:w-auto"
            >
              <option value="deterministic">Deterministic Rule Engine (Fast & 100% Reliable Offline)</option>
              <option value="gemini">Gemini API (Hosted LLM — gemini-2.0-flash-lite / 1.5-flash)</option>
            </select>
          </div>

          <button
            onClick={handleCompare}
            disabled={!oldFile || !newFile || isLoading}
            className={`w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl text-sm font-bold shadow-md transition ${
              !oldFile || !newFile || isLoading
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-500/25 active:scale-[0.98]'
            }`}
          >
            <span>Run Intelligent Diff</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {provider === 'gemini' && (
          <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div className="w-full sm:w-2/3">
              <label className="block text-2xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                Gemini API Key (Optional if already configured in .env):
              </label>
              <input
                type="password"
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
                placeholder="AIzaSy... (leave blank to use backend .env)"
                className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800 font-mono text-xs"
              />
            </div>
            <div className="text-2xs text-slate-400 italic">
              ⚡ Batch optimization active: only 1 API call per comparison. Zero rate limiting.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

