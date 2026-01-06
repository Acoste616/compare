import React, { useCallback, useState, useRef } from 'react';
import { useStore } from '../store';
import { 
  Upload, 
  FileSpreadsheet, 
  Target, 
  TrendingUp, 
  Users, 
  AlertCircle, 
  CheckCircle2, 
  Download,
  Crosshair,
  Zap,
  MapPin,
  Building2,
  Clock,
  ChevronRight,
  RefreshCw,
  Flame,
  DollarSign,
  Battery,
  Brain,
  Gauge,
  Sparkles,
  Shield
} from 'lucide-react';
import { SniperAnalysisResult, SampleLead, ClientDNAType } from '../types';

const API_BASE = 'http://localhost:8000';

// Tier color mapping
const TIER_COLORS = {
  'Tier S': { bg: 'bg-red-500/20', border: 'border-red-500', text: 'text-red-400', icon: '🔥' },
  'Tier A': { bg: 'bg-orange-500/20', border: 'border-orange-500', text: 'text-orange-400', icon: '⚡' },
  'Tier B': { bg: 'bg-yellow-500/20', border: 'border-yellow-500', text: 'text-yellow-400', icon: '📊' },
  'Tier C': { bg: 'bg-zinc-500/20', border: 'border-zinc-500', text: 'text-zinc-400', icon: '📋' },
  'Unknown': { bg: 'bg-zinc-700/20', border: 'border-zinc-700', text: 'text-zinc-500', icon: '❓' }
};

// DNA Type color mapping
const DNA_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  'Analytical': { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: '📊' },
  'Visionary': { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: '🚀' },
  'Cost-Driven': { bg: 'bg-green-500/20', text: 'text-green-400', icon: '💰' },
  'Status-Seeker': { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: '👑' },
  'Pragmatic': { bg: 'bg-cyan-500/20', text: 'text-cyan-400', icon: '🔧' },
  'Unknown': { bg: 'bg-zinc-500/20', text: 'text-zinc-400', icon: '❓' }
};

const AssetSniperTab: React.FC = () => {
  const { t, sniperState, setSniperProgress, setSniperAnalysisResult, setSniperError, resetSniperState } = useStore();
  
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [includeIntelligence, setIncludeIntelligence] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file);
        handleAnalyze(file);
      } else {
        setSniperError('Please upload a CSV file');
      }
    }
  }, [includeIntelligence]);

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      handleAnalyze(file);
    }
  };

  // Analyze CSV (preview mode with intelligence)
  const handleAnalyze = async (file: File) => {
    resetSniperState();
    setSniperProgress(10, 'uploading');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      setSniperProgress(30, 'cleaning');
      
      const response = await fetch(`${API_BASE}/api/sniper/analyze?include_intelligence=${includeIntelligence}`, {
        method: 'POST',
        body: formData
      });
      
      setSniperProgress(60, 'enriching');
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }
      
      setSniperProgress(90, 'analyzing');
      
      const result: SniperAnalysisResult = await response.json();
      setSniperAnalysisResult(result);
      setSniperProgress(100, 'complete');
      
    } catch (error: any) {
      console.error('Analysis error:', error);
      setSniperError(error.message || 'Failed to analyze CSV');
    }
  };

  // Download enriched CSV
  const handleDownload = async (enableDeepEnrichment: boolean = false) => {
    if (!selectedFile) return;
    
    setIsDownloading(true);
    
    // Update progress steps for deep enrichment
    if (enableDeepEnrichment) {
      setSniperProgress(10, 'uploading');
      setTimeout(() => setSniperProgress(30, 'cleaning'), 500);
      setTimeout(() => setSniperProgress(50, 'enriching'), 1000);
      setTimeout(() => setSniperProgress(70, 'dna_profiling'), 2000);
      setTimeout(() => setSniperProgress(85, 'generating_hooks'), 3000);
    }
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      const response = await fetch(
        `${API_BASE}/api/sniper/upload?enable_deep_enrichment=${enableDeepEnrichment}`, 
        {
          method: 'POST',
          body: formData
        }
      );
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      // Get filename from header or generate
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition?.match(/filename=(.+)/)?.[1] || 'sniper_enriched.csv';
      
      // Get stats from header
      const statsHeader = response.headers.get('X-Sniper-Stats');
      if (statsHeader) {
        try {
          const stats = JSON.parse(statsHeader);
          console.log('[SNIPER] Download stats:', stats);
        } catch (e) {
          console.warn('[SNIPER] Could not parse stats header');
        }
      }
      
      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setSniperProgress(100, 'complete');
      
    } catch (error: any) {
      console.error('Download error:', error);
      setSniperError(error.message || 'Failed to download enriched CSV');
    } finally {
      setIsDownloading(false);
    }
  };

  const result = sniperState.analysisResult;
  const tierDist = result?.tier_distribution;

  // Intelligence Card Component
  const IntelligenceCard: React.FC<{ lead: SampleLead; index: number }> = ({ lead, index }) => {
    const dnaType = (lead.estimated_dna_type || 'Unknown') as string;
    const dnaColors = DNA_COLORS[dnaType] || DNA_COLORS['Unknown'];
    
    return (
      <div 
        className="bg-zinc-900/80 rounded-xl p-4 border border-zinc-700/50 hover:border-red-500/30 transition-all duration-300 group"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="p-1.5 bg-red-500/20 rounded-lg">
              <Building2 className="w-4 h-4 text-red-400" />
            </div>
            <div className="min-w-0">
              <h4 className="text-white font-medium text-sm truncate">
                {lead.company}
              </h4>
              <p className="text-zinc-500 text-xs truncate">
                {lead.industry_name || 'Działalność gospodarcza'}
              </p>
            </div>
          </div>
          <div className={`px-2 py-1 rounded-lg text-xs font-mono font-bold ${TIER_COLORS['Tier S'].bg} ${TIER_COLORS['Tier S'].text}`}>
            {lead.tier_score}
          </div>
        </div>
        
        {/* Intelligence Grid */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {/* Tax Saving */}
          <div className="bg-zinc-800/50 rounded-lg p-2">
            <div className="flex items-center gap-1.5 mb-1">
              <DollarSign className="w-3 h-3 text-green-400" />
              <span className="text-[10px] text-zinc-500 uppercase">Tax Saving</span>
            </div>
            <div className="text-sm font-bold text-green-400 font-mono">
              {lead.estimated_tax_saving ? `${(lead.estimated_tax_saving / 1000).toFixed(0)}k PLN` : 'N/A'}
            </div>
          </div>
          
          {/* Charger Distance */}
          <div className="bg-zinc-800/50 rounded-lg p-2">
            <div className="flex items-center gap-1.5 mb-1">
              <Battery className="w-3 h-3 text-blue-400" />
              <span className="text-[10px] text-zinc-500 uppercase">Charger</span>
            </div>
            <div className="text-sm font-bold text-blue-400 font-mono">
              {lead.estimated_charger_km ? `${lead.estimated_charger_km} km` : 'N/A'}
            </div>
          </div>
          
          {/* DNA Type */}
          <div className={`${dnaColors.bg} rounded-lg p-2`}>
            <div className="flex items-center gap-1.5 mb-1">
              <Brain className="w-3 h-3 text-purple-400" />
              <span className="text-[10px] text-zinc-500 uppercase">DNA Type</span>
            </div>
            <div className={`text-sm font-bold ${dnaColors.text} font-mono flex items-center gap-1`}>
              <span>{dnaColors.icon}</span>
              <span className="truncate">{dnaType}</span>
            </div>
          </div>
          
          {/* Market Urgency */}
          <div className="bg-zinc-800/50 rounded-lg p-2">
            <div className="flex items-center gap-1.5 mb-1">
              <Gauge className="w-3 h-3 text-orange-400" />
              <span className="text-[10px] text-zinc-500 uppercase">Urgency</span>
            </div>
            <div className="text-sm font-bold text-orange-400 font-mono">
              {lead.market_urgency || 0}/100
            </div>
          </div>
        </div>
        
        {/* Context Bar */}
        <div className="flex items-center gap-2 text-xs text-zinc-500 mb-2">
          <div className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            <span>{lead.wealth_tier}</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{lead.leasing_cycle}</span>
          </div>
        </div>
        
        {/* Next Action */}
        <div className="flex items-center gap-1 text-xs text-red-400 bg-red-500/10 rounded-lg px-2 py-1.5">
          <Sparkles className="w-3 h-3" />
          <span className="truncate font-medium">{lead.next_action}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full overflow-y-auto bg-zinc-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-red-500/20 rounded-lg">
            <Crosshair className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">ASSET SNIPER</h1>
            <p className="text-zinc-500 text-sm font-mono">v4.2 • GOTHAM + BigDecoder Integration</p>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-4">
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="font-mono">SYSTEM ONLINE</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-600 font-mono">
            <Shield className="w-3 h-3" />
            <span>Palantir Tactics Ready</span>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Upload Zone */}
        <div className="lg:col-span-1">
          {/* Intelligence Toggle */}
          <div className="mb-4 p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeIntelligence}
                onChange={(e) => setIncludeIntelligence(e.target.checked)}
                className="w-4 h-4 rounded bg-zinc-800 border-zinc-700 text-red-500 focus:ring-red-500"
              />
              <div>
                <div className="text-sm text-white font-medium">Include Intelligence Preview</div>
                <div className="text-xs text-zinc-500">Show Tax/Charger/DNA estimates (Palantir)</div>
              </div>
            </label>
          </div>
          
          {/* Dropzone */}
          <div
            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer
              ${isDragActive 
                ? 'border-red-500 bg-red-500/10' 
                : 'border-zinc-700 hover:border-zinc-600 bg-zinc-900/50'
              }
              ${sniperState.isProcessing ? 'pointer-events-none opacity-50' : ''}
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            
            <div className="flex flex-col items-center gap-4">
              {sniperState.currentStep === 'idle' ? (
                <>
                  <div className={`p-4 rounded-full ${isDragActive ? 'bg-red-500/20' : 'bg-zinc-800'}`}>
                    <Upload className={`w-8 h-8 ${isDragActive ? 'text-red-500' : 'text-zinc-400'}`} />
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">{t('dropCSV')}</p>
                    <p className="text-zinc-500 text-sm">CEIDG Export Format Supported</p>
                  </div>
                </>
              ) : sniperState.currentStep === 'error' ? (
                <>
                  <div className="p-4 rounded-full bg-red-500/20">
                    <AlertCircle className="w-8 h-8 text-red-500" />
                  </div>
                  <div>
                    <p className="text-red-400 font-medium mb-1">Processing Error</p>
                    <p className="text-zinc-500 text-sm">{sniperState.error}</p>
                  </div>
                </>
              ) : sniperState.currentStep === 'complete' ? (
                <>
                  <div className="p-4 rounded-full bg-green-500/20">
                    <CheckCircle2 className="w-8 h-8 text-green-500" />
                  </div>
                  <div>
                    <p className="text-green-400 font-medium mb-1">Analysis Complete</p>
                    <p className="text-zinc-500 text-sm">{selectedFile?.name}</p>
                  </div>
                </>
              ) : (
                <>
                  <div className="p-4 rounded-full bg-red-500/20">
                    <RefreshCw className="w-8 h-8 text-red-500 animate-spin" />
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">{t('processing')}</p>
                    <p className="text-zinc-500 text-sm capitalize">
                      {sniperState.currentStep === 'dna_profiling' ? 'DNA Profiling...' :
                       sniperState.currentStep === 'generating_hooks' ? 'Generating Hooks...' :
                       `${sniperState.currentStep}...`}
                    </p>
                  </div>
                </>
              )}
            </div>

            {/* Progress Bar */}
            {(sniperState.isProcessing || isDownloading) && (
              <div className="mt-6">
                <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-red-500 to-orange-500 transition-all duration-300"
                    style={{ width: `${sniperState.progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Download Actions */}
          {sniperState.currentStep === 'complete' && (
            <div className="mt-4 space-y-3">
              <button
                onClick={() => handleDownload(false)}
                disabled={isDownloading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                {isDownloading ? 'Downloading...' : 'Download (Local Only)'}
              </button>
              
              <button
                onClick={() => handleDownload(true)}
                disabled={isDownloading || !result?.tier_distribution?.['Tier S']}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-500/20"
              >
                <Sparkles className="w-4 h-4" />
                <span>🔥 DEEP ENRICHMENT (GOTHAM + AI)</span>
              </button>
              <p className="text-xs text-zinc-500 text-center">
                Includes: Tax Savings • Charger Distance • DNA Profile • AI Hooks
              </p>
              
              <button
                onClick={() => {
                  resetSniperState();
                  setSelectedFile(null);
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 text-zinc-400 hover:text-white text-sm transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Process Another File
              </button>
            </div>
          )}

          {/* Pipeline Info */}
          <div className="mt-6 p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
            <h3 className="text-sm font-bold text-zinc-400 mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" />
              ENRICHMENT PIPELINE v4.2
            </h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                <span className="text-zinc-400">L0: Data Cleaning (NIP, Phone)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="text-zinc-400">L1: Local Scoring ($0 cost)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                <span className="text-zinc-400">L2: GOTHAM Intelligence (Tier S/A)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                <span className="text-zinc-400">L3: BigDecoder DNA + AI Hooks</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Results Dashboard */}
        <div className="lg:col-span-2">
          {result ? (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Total Leads */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-zinc-500 text-xs mb-2">
                    <Users className="w-4 h-4" />
                    {t('totalLeads')}
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">
                    {result.total_rows.toLocaleString()}
                  </div>
                </div>
                
                {/* Tier S */}
                <div className={`${TIER_COLORS['Tier S'].bg} border ${TIER_COLORS['Tier S'].border} rounded-lg p-4`}>
                  <div className={`flex items-center gap-2 ${TIER_COLORS['Tier S'].text} text-xs mb-2`}>
                    <Flame className="w-4 h-4" />
                    {t('tierS')}
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">
                    {tierDist?.['Tier S'] || 0}
                  </div>
                </div>
                
                {/* Tier A */}
                <div className={`${TIER_COLORS['Tier A'].bg} border ${TIER_COLORS['Tier A'].border} rounded-lg p-4`}>
                  <div className={`flex items-center gap-2 ${TIER_COLORS['Tier A'].text} text-xs mb-2`}>
                    <Zap className="w-4 h-4" />
                    {t('tierA')}
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">
                    {tierDist?.['Tier A'] || 0}
                  </div>
                </div>
                
                {/* Avg Wealth */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-zinc-500 text-xs mb-2">
                    <TrendingUp className="w-4 h-4" />
                    {t('avgWealthScore')}
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">
                    {result.avg_wealth_score?.toLocaleString() || 0}
                    <span className="text-sm text-zinc-500 ml-1">PLN</span>
                  </div>
                </div>
              </div>

              {/* Tier Distribution Bar */}
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                <h3 className="text-sm font-bold text-zinc-400 mb-4">TIER DISTRIBUTION</h3>
                <div className="h-6 flex rounded-lg overflow-hidden">
                  {tierDist && Object.entries(tierDist).map(([tier, count]) => {
                    const percentage = (count / result.total_rows) * 100;
                    if (percentage < 0.5) return null;
                    
                    const colors = TIER_COLORS[tier as keyof typeof TIER_COLORS] || TIER_COLORS['Unknown'];
                    return (
                      <div
                        key={tier}
                        className={`${colors.bg} ${colors.border} border-r flex items-center justify-center transition-all hover:opacity-80`}
                        style={{ width: `${percentage}%` }}
                        title={`${tier}: ${count} (${percentage.toFixed(1)}%)`}
                      >
                        {percentage > 5 && (
                          <span className={`text-xs font-mono ${colors.text}`}>
                            {percentage.toFixed(0)}%
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between mt-2">
                  {tierDist && Object.entries(tierDist).map(([tier, count]) => {
                    const colors = TIER_COLORS[tier as keyof typeof TIER_COLORS] || TIER_COLORS['Unknown'];
                    return (
                      <div key={tier} className="flex items-center gap-1 text-xs">
                        <div className={`w-2 h-2 rounded-full ${colors.bg} ${colors.border} border`}></div>
                        <span className="text-zinc-500">{tier}: {count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Intelligence Cards for Tier S */}
              {result.sample_tier_s && result.sample_tier_s.length > 0 && (
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                  <h3 className="text-sm font-bold text-zinc-400 mb-4 flex items-center gap-2">
                    <Flame className="w-4 h-4 text-red-500" />
                    TIER S INTELLIGENCE CARDS
                    {result.intelligence_included && (
                      <span className="ml-2 px-2 py-0.5 bg-purple-500/20 text-purple-400 text-[10px] rounded-full font-mono">
                        PALANTIR DATA
                      </span>
                    )}
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.sample_tier_s.map((lead: SampleLead, idx: number) => (
                      result.intelligence_included ? (
                        <IntelligenceCard key={idx} lead={lead} index={idx} />
                      ) : (
                        // Simple card without intelligence
                        <div 
                          key={idx}
                          className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-700/50 hover:border-red-500/30 transition-colors"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4 text-zinc-500" />
                              <span className="text-white font-medium text-sm truncate max-w-[200px]">
                                {lead.company}
                              </span>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-xs font-mono ${TIER_COLORS['Tier S'].bg} ${TIER_COLORS['Tier S'].text}`}>
                              Score: {lead.tier_score}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="flex items-center gap-1 text-zinc-400">
                              <MapPin className="w-3 h-3" />
                              <span>{lead.wealth_tier}</span>
                            </div>
                            <div className="flex items-center gap-1 text-zinc-400">
                              <Clock className="w-3 h-3" />
                              <span>{lead.leasing_cycle}</span>
                            </div>
                          </div>
                          <div className="mt-2 flex items-center gap-1 text-xs text-red-400">
                            <ChevronRight className="w-3 h-3" />
                            <span className="truncate">{lead.next_action}</span>
                          </div>
                        </div>
                      )
                    ))}
                  </div>
                </div>
              )}

              {/* Processing Stats */}
              <div className="flex items-center justify-between text-xs text-zinc-500 font-mono">
                <div className="flex items-center gap-4">
                  <span>Processed: {result.processed_rows.toLocaleString()} rows</span>
                  <span>•</span>
                  <span>Time: {result.processing_time_ms}ms</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>{result.filename}</span>
                </div>
              </div>
            </div>
          ) : (
            // Empty State
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <div className="p-6 bg-zinc-900/50 rounded-2xl mb-6">
                <Crosshair className="w-16 h-16 text-zinc-700" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">No Data Loaded</h3>
              <p className="text-zinc-500 max-w-md mb-6">
                Upload a CEIDG CSV export to analyze and segment your leads. 
                The v4.2 system includes GOTHAM hard data and BigDecoder DNA profiling.
              </p>
              <div className="grid grid-cols-2 gap-4 text-left max-w-lg">
                <div className="bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
                  <div className="flex items-center gap-2 text-red-500 font-bold text-lg mb-1">
                    <Flame className="w-5 h-5" />
                    Tier S
                  </div>
                  <p className="text-xs text-zinc-500">VIP leads with full intelligence: Tax Savings, Charger Distance, DNA Profile, AI Hooks.</p>
                </div>
                <div className="bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
                  <div className="flex items-center gap-2 text-orange-500 font-bold text-lg mb-1">
                    <Zap className="w-5 h-5" />
                    Tier A
                  </div>
                  <p className="text-xs text-zinc-500">Hot leads with GOTHAM enrichment. Priority outreach recommended.</p>
                </div>
                <div className="bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
                  <div className="flex items-center gap-2 text-purple-500 font-bold text-lg mb-1">
                    <Brain className="w-5 h-5" />
                    DNA Profiling
                  </div>
                  <p className="text-xs text-zinc-500">BigDecoder predicts decision style: Analytical, Visionary, Cost-Driven, etc.</p>
                </div>
                <div className="bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
                  <div className="flex items-center gap-2 text-green-500 font-bold text-lg mb-1">
                    <DollarSign className="w-5 h-5" />
                    GOTHAM Data
                  </div>
                  <p className="text-xs text-zinc-500">Hard financial intel: Tax potential, Charger infrastructure, Market urgency.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssetSniperTab;
