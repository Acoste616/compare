import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Server, Shield, Activity, Cpu, ArrowLeft, Database, Edit2, Plus, Save, X,
    Upload, FileSpreadsheet, Target, TrendingUp, Users, AlertCircle, CheckCircle2, 
    Download, Crosshair, Zap, MapPin, Building2, Clock, ChevronRight, RefreshCw,
    Flame, DollarSign, Battery, Brain, Gauge, Sparkles, Eye, Settings
} from 'lucide-react';
import { useStore } from '../store';
import { Session, SniperAnalysisResult, SampleLead, ClientDNAType } from '../types';

const API_BASE = 'http://localhost:8000';

interface RAGNugget {
    id: string;
    title: string;
    content: string;
    keywords: string[];
    language: string;
}

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

type AdminTab = 'overview' | 'sniper' | 'knowledge' | 'logs';

const AdminPanel: React.FC = () => {
    const { setView, systemLogs, sessions } = useStore();
    const [activeTab, setActiveTab] = useState<AdminTab>('overview');
    const [ragNuggets, setRagNuggets] = useState<RAGNugget[]>([]);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isGoldenModalOpen, setIsGoldenModalOpen] = useState(false);
    const [editingNugget, setEditingNugget] = useState<RAGNugget | null>(null);
    const [goldenForm, setGoldenForm] = useState({
        trigger_context: '', golden_response: '', category: 'price', language: 'PL'
    });

    // Sniper State
    const [sniperFile, setSniperFile] = useState<File | null>(null);
    const [sniperAnalysis, setSniperAnalysis] = useState<SniperAnalysisResult | null>(null);
    const [sniperProcessing, setSniperProcessing] = useState(false);
    const [sniperProgress, setSniperProgress] = useState(0);
    const [sniperError, setSniperError] = useState<string | null>(null);
    const [includeIntelligence, setIncludeIntelligence] = useState(true);
    const [isDragActive, setIsDragActive] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const sessionList = Object.values(sessions) as Session[];
    const closedSessions = sessionList.filter(s => s.status === 'closed');
    const wonSessions = closedSessions.filter(s => s.outcome === 'sale');
    const winRate = closedSessions.length > 0 ? Math.round((wonSessions.length / closedSessions.length) * 100) : 0;

    useEffect(() => {
        fetch(`${API_BASE}/api/admin/rag/list`)
            .then(res => res.json())
            .then(data => setRagNuggets(data.nuggets || []))
            .catch(err => console.error('Failed to load RAG nuggets:', err));
    }, []);

    const handleEditNugget = (nugget: RAGNugget) => {
        setEditingNugget({ ...nugget });
        setIsEditModalOpen(true);
    };

    const handleSaveNugget = async () => {
        if (!editingNugget) return;
        try {
            const response = await fetch(`${API_BASE}/api/admin/rag/edit/${editingNugget.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: editingNugget.title,
                    content: editingNugget.content,
                    keywords: editingNugget.keywords,
                    language: editingNugget.language
                })
            });
            if (response.ok) {
                setRagNuggets(prev => prev.map(n => n.id === editingNugget.id ? editingNugget : n));
                setIsEditModalOpen(false);
                setEditingNugget(null);
            }
        } catch (error) {
            console.error('Error saving nugget:', error);
        }
    };

    const handleAddGoldenStandard = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/admin/golden-standards/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(goldenForm)
            });
            if (response.ok) {
                setIsGoldenModalOpen(false);
                setGoldenForm({ trigger_context: '', golden_response: '', category: 'price', language: 'PL' });
                const data = await fetch(`${API_BASE}/api/admin/rag/list`).then(r => r.json());
                setRagNuggets(data.nuggets || []);
            }
        } catch (error) {
            console.error('Error adding golden standard:', error);
        }
    };

    // === SNIPER HANDLERS ===
    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragActive(true);
        } else if (e.type === 'dragleave') {
            setIsDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragActive(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            if (file.name.endsWith('.csv')) {
                setSniperFile(file);
                handleAnalyze(file);
            } else {
                setSniperError('Please upload a CSV file');
            }
        }
    }, [includeIntelligence]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setSniperFile(file);
            handleAnalyze(file);
        }
    };

    const handleAnalyze = async (file: File) => {
        setSniperAnalysis(null);
        setSniperError(null);
        setSniperProcessing(true);
        setSniperProgress(10);
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            setSniperProgress(30);
            
            const response = await fetch(`${API_BASE}/api/sniper/analyze?include_intelligence=${includeIntelligence}`, {
                method: 'POST',
                body: formData
            });
            
            setSniperProgress(60);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Analysis failed');
            }
            
            setSniperProgress(90);
            
            const result: SniperAnalysisResult = await response.json();
            setSniperAnalysis(result);
            setSniperProgress(100);
            
        } catch (error: any) {
            console.error('Analysis error:', error);
            setSniperError(error.message || 'Failed to analyze CSV');
        } finally {
            setSniperProcessing(false);
        }
    };

    const handleDownload = async (enableDeepEnrichment: boolean = false) => {
        if (!sniperFile) return;
        
        setIsDownloading(true);
        setSniperProgress(10);
        
        try {
            const formData = new FormData();
            formData.append('file', sniperFile);
            
            if (enableDeepEnrichment) {
                setSniperProgress(30);
                // Simulate progress for deep enrichment
                const progressInterval = setInterval(() => {
                    setSniperProgress(prev => Math.min(prev + 10, 85));
                }, 2000);
                
                const response = await fetch(
                    `${API_BASE}/api/sniper/upload?enable_deep_enrichment=true`, 
                    { method: 'POST', body: formData }
                );
                
                clearInterval(progressInterval);
                
                if (!response.ok) throw new Error('Download failed');
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `sniper_enriched_deep_${Date.now()}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const response = await fetch(
                    `${API_BASE}/api/sniper/upload?enable_deep_enrichment=false`, 
                    { method: 'POST', body: formData }
                );
                
                if (!response.ok) throw new Error('Download failed');
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `sniper_enriched_local_${Date.now()}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
            
            setSniperProgress(100);
            
        } catch (error: any) {
            console.error('Download error:', error);
            setSniperError(error.message || 'Failed to download enriched CSV');
        } finally {
            setIsDownloading(false);
        }
    };

    const resetSniper = () => {
        setSniperFile(null);
        setSniperAnalysis(null);
        setSniperError(null);
        setSniperProgress(0);
    };

    // Tab navigation
    const tabs: { id: AdminTab; label: string; icon: React.ReactNode }[] = [
        { id: 'overview', label: 'Overview', icon: <Server size={16} /> },
        { id: 'sniper', label: 'Asset Sniper', icon: <Crosshair size={16} /> },
        { id: 'knowledge', label: 'Knowledge Base', icon: <Database size={16} /> },
        { id: 'logs', label: 'System Logs', icon: <Activity size={16} /> },
    ];

    return (
        <div className="flex flex-col h-screen bg-black text-zinc-300 overflow-hidden">
            {/* Header */}
            <div className="flex items-center gap-4 p-6 border-b border-zinc-800">
                <button onClick={() => setView('dashboard')} className="hover:text-white transition-colors">
                    <ArrowLeft size={20} />
                </button>
                <div>
                    <h1 className="text-2xl font-bold text-white">System Administration</h1>
                    <p className="text-zinc-500 text-sm">ULTRA v4.3 • Admin Panel</p>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex items-center gap-2 px-6 py-3 border-b border-zinc-800 bg-zinc-950">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                            ${activeTab === tab.id 
                                ? 'bg-red-500/20 text-red-400 border border-red-500/50' 
                                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                            }`}
                    >
                        {tab.icon}
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                {/* OVERVIEW TAB */}
                {activeTab === 'overview' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                            <div className="flex items-center gap-3 mb-4 text-white font-bold">
                                <Server size={20} className="text-green-500" />
                                <h2>Global Operations</h2>
                            </div>
                            <div className="space-y-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Total Sessions</span>
                                    <span className="font-mono text-white">{sessionList.length}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Active Now</span>
                                    <span className="font-mono text-green-400">{sessionList.filter(s => s.status === 'active').length}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Win Rate (Closed)</span>
                                    <span className="font-mono text-blue-400">{winRate}%</span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                            <div className="flex items-center gap-3 mb-4 text-white font-bold">
                                <Cpu size={20} className="text-blue-500" />
                                <h2>AI Providers</h2>
                            </div>
                            <div className="space-y-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Primary (Fast)</span>
                                    <span className="font-mono">Gemini 2.0 Flash</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Fallback (Fast)</span>
                                    <span className="font-mono text-purple-400">Llama 3.3 70B</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Deep Analysis</span>
                                    <span className="font-mono text-cyan-400">DeepSeek V3.1</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Status</span>
                                    <span className="font-mono text-green-400 flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                        Operational
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                            <div className="flex items-center gap-3 mb-4 text-white font-bold">
                                <Shield size={20} className="text-red-500" />
                                <h2>Security & Privacy</h2>
                            </div>
                            <div className="space-y-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">PII Stripping</span>
                                    <span className="font-mono text-green-400">ACTIVE</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Prompt Injection Guard</span>
                                    <span className="font-mono text-green-400">ACTIVE</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Encryption</span>
                                    <span className="font-mono text-green-400">AES-256</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ASSET SNIPER TAB */}
                {activeTab === 'sniper' && (
                    <div className="space-y-6">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-red-500/20 rounded-lg">
                                    <Crosshair className="w-6 h-6 text-red-500" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">ASSET SNIPER</h2>
                                    <p className="text-zinc-500 text-sm font-mono">v4.2 • GOTHAM + BigDecoder Integration</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={includeIntelligence}
                                        onChange={(e) => setIncludeIntelligence(e.target.checked)}
                                        className="w-4 h-4 rounded bg-zinc-800 border-zinc-700 text-red-500 focus:ring-red-500"
                                    />
                                    <span className="text-sm text-zinc-400">Include Intelligence Preview</span>
                                </label>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Upload Zone */}
                            <div className="lg:col-span-1 space-y-4">
                                <div
                                    className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer
                                        ${isDragActive 
                                            ? 'border-red-500 bg-red-500/10' 
                                            : 'border-zinc-700 hover:border-zinc-600 bg-zinc-900/50'
                                        }
                                        ${sniperProcessing ? 'pointer-events-none opacity-50' : ''}
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
                                        {!sniperProcessing && !sniperAnalysis && !sniperError && (
                                            <>
                                                <div className={`p-4 rounded-full ${isDragActive ? 'bg-red-500/20' : 'bg-zinc-800'}`}>
                                                    <Upload className={`w-8 h-8 ${isDragActive ? 'text-red-500' : 'text-zinc-400'}`} />
                                                </div>
                                                <div>
                                                    <p className="text-white font-medium mb-1">Drop CSV here or click to upload</p>
                                                    <p className="text-zinc-500 text-sm">CEIDG Export Format Supported</p>
                                                </div>
                                            </>
                                        )}
                                        
                                        {sniperProcessing && (
                                            <>
                                                <div className="p-4 rounded-full bg-red-500/20">
                                                    <RefreshCw className="w-8 h-8 text-red-500 animate-spin" />
                                                </div>
                                                <div>
                                                    <p className="text-white font-medium mb-1">Processing...</p>
                                                    <p className="text-zinc-500 text-sm">{sniperFile?.name}</p>
                                                </div>
                                            </>
                                        )}
                                        
                                        {sniperError && (
                                            <>
                                                <div className="p-4 rounded-full bg-red-500/20">
                                                    <AlertCircle className="w-8 h-8 text-red-500" />
                                                </div>
                                                <div>
                                                    <p className="text-red-400 font-medium mb-1">Error</p>
                                                    <p className="text-zinc-500 text-sm">{sniperError}</p>
                                                </div>
                                            </>
                                        )}
                                        
                                        {sniperAnalysis && !sniperProcessing && !sniperError && (
                                            <>
                                                <div className="p-4 rounded-full bg-green-500/20">
                                                    <CheckCircle2 className="w-8 h-8 text-green-500" />
                                                </div>
                                                <div>
                                                    <p className="text-green-400 font-medium mb-1">Analysis Complete</p>
                                                    <p className="text-zinc-500 text-sm">{sniperFile?.name}</p>
                                                </div>
                                            </>
                                        )}
                                    </div>

                                    {(sniperProcessing || isDownloading) && (
                                        <div className="mt-6">
                                            <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                                                <div 
                                                    className="h-full bg-gradient-to-r from-red-500 to-orange-500 transition-all duration-300"
                                                    style={{ width: `${sniperProgress}%` }}
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Download Buttons */}
                                {sniperAnalysis && (
                                    <div className="space-y-3">
                                        <button
                                            onClick={() => handleDownload(false)}
                                            disabled={isDownloading}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        >
                                            <Download className="w-4 h-4" />
                                            Download (Local Only)
                                        </button>
                                        
                                        <button
                                            onClick={() => handleDownload(true)}
                                            disabled={isDownloading || !sniperAnalysis?.tier_distribution?.['Tier S']}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white rounded-lg font-bold transition-all disabled:opacity-50 shadow-lg shadow-red-500/20"
                                        >
                                            <Sparkles className="w-4 h-4" />
                                            🔥 DEEP ENRICHMENT (GOTHAM + AI)
                                        </button>
                                        <p className="text-xs text-zinc-500 text-center">
                                            Includes: Tax Savings • Charger Distance • DNA Profile • AI Hooks
                                        </p>
                                        
                                        <button
                                            onClick={resetSniper}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-zinc-400 hover:text-white text-sm transition-colors"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                            Process Another File
                                        </button>
                                    </div>
                                )}

                                {/* Pipeline Info */}
                                <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
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

                            {/* Results Dashboard */}
                            <div className="lg:col-span-2">
                                {sniperAnalysis ? (
                                    <div className="space-y-6">
                                        {/* Stats Grid */}
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                            <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                                                <div className="flex items-center gap-2 text-zinc-500 text-xs mb-2">
                                                    <Users className="w-4 h-4" />
                                                    Total Leads
                                                </div>
                                                <div className="text-2xl font-bold text-white font-mono">
                                                    {sniperAnalysis.total_rows.toLocaleString()}
                                                </div>
                                            </div>
                                            
                                            <div className={`${TIER_COLORS['Tier S'].bg} border ${TIER_COLORS['Tier S'].border} rounded-lg p-4`}>
                                                <div className={`flex items-center gap-2 ${TIER_COLORS['Tier S'].text} text-xs mb-2`}>
                                                    <Flame className="w-4 h-4" />
                                                    Tier S (VIP)
                                                </div>
                                                <div className="text-2xl font-bold text-white font-mono">
                                                    {sniperAnalysis.tier_distribution?.['Tier S'] || 0}
                                                </div>
                                            </div>
                                            
                                            <div className={`${TIER_COLORS['Tier A'].bg} border ${TIER_COLORS['Tier A'].border} rounded-lg p-4`}>
                                                <div className={`flex items-center gap-2 ${TIER_COLORS['Tier A'].text} text-xs mb-2`}>
                                                    <Zap className="w-4 h-4" />
                                                    Tier A (Hot)
                                                </div>
                                                <div className="text-2xl font-bold text-white font-mono">
                                                    {sniperAnalysis.tier_distribution?.['Tier A'] || 0}
                                                </div>
                                            </div>
                                            
                                            <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                                                <div className="flex items-center gap-2 text-zinc-500 text-xs mb-2">
                                                    <TrendingUp className="w-4 h-4" />
                                                    Avg Wealth
                                                </div>
                                                <div className="text-2xl font-bold text-white font-mono">
                                                    {sniperAnalysis.avg_wealth_score?.toLocaleString() || 0}
                                                    <span className="text-sm text-zinc-500 ml-1">PLN</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Tier Distribution Bar */}
                                        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                                            <h3 className="text-sm font-bold text-zinc-400 mb-4">TIER DISTRIBUTION</h3>
                                            <div className="h-6 flex rounded-lg overflow-hidden">
                                                {sniperAnalysis.tier_distribution && Object.entries(sniperAnalysis.tier_distribution).map(([tier, count]) => {
                                                    const countNum = count as number;
                                                    const percentage = (countNum / sniperAnalysis.total_rows) * 100;
                                                    if (percentage < 0.5) return null;
                                                    
                                                    const colors = TIER_COLORS[tier as keyof typeof TIER_COLORS] || TIER_COLORS['Unknown'];
                                                    return (
                                                        <div
                                                            key={tier}
                                                            className={`${colors.bg} ${colors.border} border-r flex items-center justify-center transition-all hover:opacity-80`}
                                                            style={{ width: `${percentage}%` }}
                                                            title={`${tier}: ${countNum} (${percentage.toFixed(1)}%)`}
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
                                                {sniperAnalysis.tier_distribution && Object.entries(sniperAnalysis.tier_distribution).map(([tier, count]) => {
                                                    const countNum = count as number;
                                                    const colors = TIER_COLORS[tier as keyof typeof TIER_COLORS] || TIER_COLORS['Unknown'];
                                                    return (
                                                        <div key={tier} className="flex items-center gap-1 text-xs">
                                                            <div className={`w-2 h-2 rounded-full ${colors.bg} ${colors.border} border`}></div>
                                                            <span className="text-zinc-500">{tier}: {countNum}</span>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>

                                        {/* Tier S Intelligence Cards */}
                                        {sniperAnalysis.sample_tier_s && sniperAnalysis.sample_tier_s.length > 0 && (
                                            <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                                                <h3 className="text-sm font-bold text-zinc-400 mb-4 flex items-center gap-2">
                                                    <Flame className="w-4 h-4 text-red-500" />
                                                    TIER S INTELLIGENCE CARDS
                                                    {sniperAnalysis.intelligence_included && (
                                                        <span className="ml-2 px-2 py-0.5 bg-purple-500/20 text-purple-400 text-[10px] rounded-full font-mono">
                                                            PALANTIR DATA
                                                        </span>
                                                    )}
                                                </h3>
                                                
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {sniperAnalysis.sample_tier_s.map((lead: SampleLead, idx: number) => {
                                                        const dnaType = (lead.estimated_dna_type || 'Unknown') as string;
                                                        const dnaColors = DNA_COLORS[dnaType] || DNA_COLORS['Unknown'];
                                                        
                                                        return (
                                                            <div 
                                                                key={idx}
                                                                className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-700/50 hover:border-red-500/30 transition-colors"
                                                            >
                                                                <div className="flex items-start justify-between mb-2">
                                                                    <div className="flex items-center gap-2 flex-1 min-w-0">
                                                                        <Building2 className="w-4 h-4 text-zinc-500 flex-shrink-0" />
                                                                        <span className="text-white font-medium text-sm truncate">
                                                                            {lead.company}
                                                                        </span>
                                                                    </div>
                                                                    <span className={`px-2 py-0.5 rounded text-xs font-mono ${TIER_COLORS['Tier S'].bg} ${TIER_COLORS['Tier S'].text}`}>
                                                                        {lead.tier_score}
                                                                    </span>
                                                                </div>
                                                                
                                                                {sniperAnalysis.intelligence_included && (
                                                                    <div className="grid grid-cols-2 gap-2 mb-2">
                                                                        <div className="bg-zinc-900/50 rounded px-2 py-1">
                                                                            <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                                                                                <DollarSign className="w-3 h-3 text-green-400" />
                                                                                Tax Saving
                                                                            </div>
                                                                            <div className="text-xs font-bold text-green-400 font-mono">
                                                                                {lead.estimated_tax_saving ? `${(lead.estimated_tax_saving / 1000).toFixed(0)}k PLN` : 'N/A'}
                                                                            </div>
                                                                        </div>
                                                                        <div className="bg-zinc-900/50 rounded px-2 py-1">
                                                                            <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                                                                                <Battery className="w-3 h-3 text-blue-400" />
                                                                                Charger
                                                                            </div>
                                                                            <div className="text-xs font-bold text-blue-400 font-mono">
                                                                                {lead.estimated_charger_km ? `${lead.estimated_charger_km} km` : 'N/A'}
                                                                            </div>
                                                                        </div>
                                                                        <div className={`${dnaColors.bg} rounded px-2 py-1`}>
                                                                            <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                                                                                <Brain className="w-3 h-3 text-purple-400" />
                                                                                DNA Type
                                                                            </div>
                                                                            <div className={`text-xs font-bold ${dnaColors.text} font-mono flex items-center gap-1`}>
                                                                                <span>{dnaColors.icon}</span>
                                                                                <span className="truncate">{dnaType}</span>
                                                                            </div>
                                                                        </div>
                                                                        <div className="bg-zinc-900/50 rounded px-2 py-1">
                                                                            <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                                                                                <Gauge className="w-3 h-3 text-orange-400" />
                                                                                Urgency
                                                                            </div>
                                                                            <div className="text-xs font-bold text-orange-400 font-mono">
                                                                                {lead.market_urgency || 0}/100
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                )}
                                                                
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
                                                                
                                                                <div className="flex items-center gap-1 text-xs text-red-400 bg-red-500/10 rounded px-2 py-1">
                                                                    <ChevronRight className="w-3 h-3" />
                                                                    <span className="truncate">{lead.next_action}</span>
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}

                                        {/* Processing Stats */}
                                        <div className="flex items-center justify-between text-xs text-zinc-500 font-mono">
                                            <div className="flex items-center gap-4">
                                                <span>Processed: {sniperAnalysis.processed_rows.toLocaleString()} rows</span>
                                                <span>•</span>
                                                <span>Time: {sniperAnalysis.processing_time_ms}ms</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <FileSpreadsheet className="w-4 h-4" />
                                                <span>{sniperAnalysis.filename}</span>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    /* Empty State */
                                    <div className="h-full flex flex-col items-center justify-center text-center p-8 min-h-[400px]">
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
                                                <div className="flex items-center gap-2 text-purple-500 font-bold text-lg mb-1">
                                                    <Brain className="w-5 h-5" />
                                                    DNA Profiling
                                                </div>
                                                <p className="text-xs text-zinc-500">BigDecoder predicts decision style: Analytical, Visionary, Cost-Driven, etc.</p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* KNOWLEDGE BASE TAB */}
                {activeTab === 'knowledge' && (
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3 text-white font-bold">
                                <Database size={20} className="text-blue-500" />
                                <h2>Baza Wiedzy (RAG)</h2>
                            </div>
                            <button onClick={() => setIsGoldenModalOpen(true)} className="flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium">
                                <Plus size={16} />Dodaj Złoty Standard
                            </button>
                        </div>
                        <div className="space-y-3 max-h-[600px] overflow-y-auto">
                            {ragNuggets.map((nugget) => (
                                <div key={nugget.id} className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition-colors">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-2">
                                                <h3 className="text-white font-medium text-sm truncate">{nugget.title}</h3>
                                                <span className="text-[10px] text-zinc-500 font-mono bg-zinc-800 px-2 py-0.5 rounded">{nugget.id.slice(0, 8)}...</span>
                                            </div>
                                            <p className="text-zinc-400 text-xs line-clamp-2 mb-2">{nugget.content}</p>
                                            <div className="flex flex-wrap gap-1">
                                                {nugget.keywords.slice(0, 4).map((kw, i) => (
                                                    <span key={i} className="text-[10px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full">{kw}</span>
                                                ))}
                                            </div>
                                        </div>
                                        <button onClick={() => handleEditNugget(nugget)} className="p-2 hover:bg-zinc-800 rounded-lg transition-colors text-blue-400 hover:text-blue-300" title="Edit">
                                            <Edit2 size={16} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 text-xs text-zinc-600 text-center">Total Nuggets: {ragNuggets.length}</div>
                    </div>
                )}

                {/* SYSTEM LOGS TAB */}
                {activeTab === 'logs' && (
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                        <div className="flex items-center gap-3 mb-4 text-white font-bold">
                            <Activity size={20} className="text-zinc-500" />
                            <h2>System Logs</h2>
                        </div>
                        <div className="font-mono text-xs space-y-1 h-[600px] overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700">
                            {systemLogs.length > 0 ? systemLogs.map((log) => (
                                <div key={log.id} className="flex gap-4 hover:bg-zinc-800/50 p-1 rounded">
                                    <span className="text-zinc-500 w-20 shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                                    <span className={`w-16 shrink-0 font-bold ${log.type === 'INFO' ? 'text-blue-500' : log.type === 'WARN' ? 'text-amber-500' : log.type === 'ERROR' ? 'text-red-500' : 'text-green-500'}`}>[{log.type}]</span>
                                    <span className="text-zinc-300">{log.message}</span>
                                </div>
                            )) : (
                                <div className="text-zinc-600 italic p-4">Waiting for system events...</div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Edit Modal */}
            {isEditModalOpen && editingNugget && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white">Edytuj Nugget</h2>
                            <button onClick={() => setIsEditModalOpen(false)} className="text-zinc-400 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Title</label>
                                <input type="text" value={editingNugget.title} onChange={(e) => setEditingNugget({ ...editingNugget, title: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Content</label>
                                <textarea value={editingNugget.content} onChange={(e) => setEditingNugget({ ...editingNugget, content: e.target.value })} rows={6} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 resize-none" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Keywords (comma-separated)</label>
                                <input type="text" value={editingNugget.keywords.join(', ')} onChange={(e) => setEditingNugget({ ...editingNugget, keywords: e.target.value.split(',').map(k => k.trim()) })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Language</label>
                                <select value={editingNugget.language} onChange={(e) => setEditingNugget({ ...editingNugget, language: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500">
                                    <option value="PL">Polish (PL)</option>
                                    <option value="EN">English (EN)</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={handleSaveNugget} className="flex-1 flex items-center justify-center gap-2 bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-lg transition-colors font-medium">
                                <Save size={18} />Save Changes
                            </button>
                            <button onClick={() => setIsEditModalOpen(false)} className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors">Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Golden Standard Modal */}
            {isGoldenModalOpen && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white">Dodaj Złoty Standard</h2>
                            <button onClick={() => setIsGoldenModalOpen(false)} className="text-zinc-400 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Trigger Context (pytanie klienta)</label>
                                <input type="text" value={goldenForm.trigger_context} onChange={(e) => setGoldenForm({ ...goldenForm, trigger_context: e.target.value })} placeholder="np. Klient pyta o cenę Model 3 Long Range" className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white placeholder-zinc-600 focus:outline-none focus:border-blue-500" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-400 mb-2">Golden Response (idealna odpowiedź)</label>
                                <textarea value={goldenForm.golden_response} onChange={(e) => setGoldenForm({ ...goldenForm, golden_response: e.target.value })} placeholder="Model 3 Long Range w Polsce kosztuje 229,990 PLN katalogowo..." rows={5} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white placeholder-zinc-600 focus:outline-none focus:border-blue-500 resize-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-zinc-400 mb-2">Category</label>
                                    <select value={goldenForm.category} onChange={(e) => setGoldenForm({ ...goldenForm, category: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500">
                                        <option value="price">Price</option>
                                        <option value="objections">Objections</option>
                                        <option value="features">Features</option>
                                        <option value="closing">Closing</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-zinc-400 mb-2">Language</label>
                                    <select value={goldenForm.language} onChange={(e) => setGoldenForm({ ...goldenForm, language: e.target.value })} className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500">
                                        <option value="PL">Polish (PL)</option>
                                        <option value="EN">English (EN)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={handleAddGoldenStandard} className="flex-1 flex items-center justify-center gap-2 bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-lg transition-colors font-medium">
                                <Plus size={18} />Dodaj Standard
                            </button>
                            <button onClick={() => setIsGoldenModalOpen(false)} className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors">Cancel</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminPanel;
