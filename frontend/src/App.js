import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = 'http://localhost:5000';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [book, setBook] = useState(null); // {id, title, content: []}
  const [sentences, setSentences] = useState([]);
  const [currentSentence, setCurrentSentence] = useState(0);
  const [audioSrc, setAudioSrc] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [message, setMessage] = useState('');
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  // Phase 7: Text-audio sync
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);

  const audioRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    checkHealth();
    // Initial speed fetch and start polling every minute (Phase 6)
    fetchSpeed();
    fetchSettings();
    const interval = setInterval(fetchSpeed, 60_000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Apply playback rate to audio element
    if (audioRef.current) {
      audioRef.current.playbackRate = speed || 1.0;
    }
  }, [speed, audioSrc]);

  useEffect(() => {
    // Auto-scroll to keep current sentence in view
    const el = document.getElementById(`sentence-${currentSentence}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [currentSentence]);

  // Phase 7: Text-audio sync polling during playback
  useEffect(() => {
    let syncInterval;
    if (isPlaying && sentences.length > 0) {
      syncInterval = setInterval(fetchCurrentSentence, 500); // Poll every 500ms
    }
    return () => {
      if (syncInterval) clearInterval(syncInterval);
    };
  }, [isPlaying, sentences.length]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.code === 'ArrowLeft') {
        seekBy(-15);
      } else if (e.code === 'ArrowRight') {
        seekBy(15);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [audioSrc, isPlaying]);

  const checkHealth = async () => {
    try {
      if (window.electronAPI) {
        const status = await window.electronAPI.healthCheck();
        setHealthStatus(status);
      } else {
        const response = await fetch(`${API_BASE}/api/health`);
        const status = await response.json();
        setHealthStatus(status);
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'error', message: error.message });
    } finally {
      setLoading(false);
    }
  };

  const fetchSpeed = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/playback/speed`);
      if (!res.ok) return;
      const data = await res.json();
      setSpeed(data.speed);
    } catch (e) {
      // ignore
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/settings`);
      if (!res.ok) return;
      const data = await res.json();
      const vs = Array.isArray(data.voices) ? data.voices.filter(v => v.enabled !== false) : [];
      setVoices(vs);
      if (!selectedVoice && vs.length) {
        const preferred = vs.find(v => v.type === 'cloud') || vs[0];
        setSelectedVoice(preferred?.name || '');
      }
    } catch (e) {
      // ignore
    }
  };

  const fetchCurrentBook = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/book/current`);
      if (!res.ok) throw new Error('No book loaded');
      const data = await res.json();
      setBook(data);
      setSentences(data.content || []);
      setCurrentSentence(0);
      setCurrentSentenceIndex(0);
      // Scroll to first sentence
      setTimeout(() => setCurrentSentence(0), 100);
      return data;
    } catch (e) {
      setBook(null);
      setSentences([]);
      return null;
    }
  };

  // Phase 7: Fetch current sentence from backend based on audio position
  const fetchCurrentSentence = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/playback/current-sentence`);
      if (!res.ok) return;
      const data = await res.json();
      const newIndex = data.sentence_index;
      if (newIndex !== currentSentenceIndex) {
        setCurrentSentenceIndex(newIndex);
        setCurrentSentence(newIndex);
      }
    } catch (e) {
      // ignore sync errors
    }
  };

  const onSelectFile = () => fileInputRef.current?.click();

  const onFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (file) await importFile(file);
    e.target.value = '';
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files?.[0];
    if (file) await importFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const ensureSingleBookSlot = async () => {
    if (!book) return true;
    const confirmed = window.confirm('A book is already open. Close it before importing a new one?');
    if (!confirmed) {
      setMessage('Import cancelled — current book is still open.');
      return false;
    }
    await closeBook();
    return true;
  };

  const importFile = async (file) => {
    const slotReady = await ensureSingleBookSlot();
    if (!slotReady) {
      return;
    }
    setMessage('Importing...');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${API_BASE}/api/book/import`, { method: 'POST', body: form });
      if (res.status === 409) {
        throw new Error('A book is already open. Close it before importing another.');
      }
      if (!res.ok) throw new Error(await res.text());
      const current = await fetchCurrentBook();
      setMessage('Generating audio...');
      await generateTTSFromCurrent(current?.content || []);
      setMessage('');
    } catch (e) {
      console.error(e);
      setMessage(`Error: ${e.message || e}`);
    }
  };

  const generateTTSFromCurrent = async (incomingSentences) => {
    const targetSentences = Array.isArray(incomingSentences) && incomingSentences.length
      ? incomingSentences
      : sentences;
    if (!targetSentences.length) return;
    setTtsLoading(true);
    try {
      const text = (targetSentences.length ? targetSentences.join(' ') : '').slice(0, 8000);
      const res = await fetch(`${API_BASE}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, mode: 'cloud', voice: selectedVoice || undefined })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const url = `${API_BASE}${data.audio_path}`;
      setAudioSrc(url);
      // Autoplay when ready
      setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.src = url;
          audioRef.current.playbackRate = speed || 1.0;
          audioRef.current.play().catch(() => {});
          setIsPlaying(true);
        }
      }, 200);
    } catch (e) {
      console.error(e);
      setMessage(`TTS Error: ${e.message || e}`);
    } finally {
      setTtsLoading(false);
    }
  };

  const togglePlay = async () => {
    if (!audioRef.current) return;
    if (audioRef.current.paused) {
      await audioRef.current.play().catch(() => {});
      setIsPlaying(true);
    } else {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const seekBy = (delta) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(0, (audioRef.current.currentTime || 0) + delta);
  };

  const closeBook = async () => {
    try {
      await fetch(`${API_BASE}/api/book/close`, { method: 'POST' });
      setBook(null);
      setSentences([]);
      setAudioSrc('');
      setIsPlaying(false);
    } catch (e) {
      // ignore
    }
  };

  // Phase 7: Update backend with current audio position
  const handleTimeUpdate = async () => {
    if (!audioRef.current) return;
    const currentTime = audioRef.current.currentTime;
    try {
      await fetch(`${API_BASE}/api/playback/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position_seconds: currentTime })
      });
    } catch (e) {
      // ignore position update errors
    }
  };

  const EmptyState = () => (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center bg-white hover:border-blue-400 transition"
    >
      <div className="text-2xl font-semibold mb-2">Drop a file to begin (.txt, .md, .pdf, .epub, .docx)</div>
      <div className="text-gray-600 mb-6">or</div>
      <button onClick={onSelectFile} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Select File</button>
      {message && <div className="mt-4 text-sm text-gray-500">{message}</div>}
    </div>
  );

  const ReadingView = () => (
    <div className="bg-white rounded-lg shadow flex flex-col h-[70vh]">
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <div>
          <div className="font-semibold text-lg">{book?.title || 'Current Book'}</div>
          <div className="text-sm text-gray-500">Sentences: {sentences.length}</div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Speed: {speed.toFixed(2)}×</span>
          <button onClick={closeBook} className="px-3 py-1.5 text-sm bg-gray-100 rounded hover:bg-gray-200">Close</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-3">
        {sentences.map((s, idx) => (
          <p
            key={idx}
            id={`sentence-${idx}`}
            onClick={() => setCurrentSentence(idx)}
            className={`leading-relaxed cursor-pointer ${idx === currentSentence ? 'bg-yellow-50' : ''}`}
          >
            {s}
          </p>
        ))}
      </div>
      <div className="px-4 py-3 border-t flex items-center gap-3">
        <button onClick={() => seekBy(-15)} className="px-3 py-1.5 bg-gray-100 rounded hover:bg-gray-200">⟲ 15s</button>
        <button onClick={togglePlay} className="px-4 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700">
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button onClick={() => seekBy(15)} className="px-3 py-1.5 bg-gray-100 rounded hover:bg-gray-200">15s ⟳</button>
        <div className="text-sm text-gray-500 ml-auto">{ttsLoading ? 'Generating audio…' : audioSrc ? 'Ready' : 'No audio'}</div>
      </div>
      <audio
        ref={audioRef}
        src={audioSrc}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={handleTimeUpdate}
      />
    </div>
  );

  return (
    <div className="App">
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-5xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">ReadMe</h1>
              <p className="text-xs text-gray-500">Local AI Reading Assistant</p>
            </div>
            <div>
              <span className={`px-2 py-1 rounded text-xs ${healthStatus?.status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700'}`}>
                {healthStatus?.status || 'unknown'}
              </span>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main>
          <div className="max-w-5xl mx-auto py-6 sm:px-6 lg:px-8">
            <div className="px-4 py-4 sm:px-0 space-y-6">
              {!book ? (
                <EmptyState />
              ) : (
                <ReadingView />
              )}

              {/* Controls below for import and TTS */}
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center gap-3">
                  <button onClick={onSelectFile} className="px-3 py-1.5 bg-gray-100 rounded hover:bg-gray-200">Select File</button>
                  <button onClick={fetchCurrentBook} className="px-3 py-1.5 bg-gray-100 rounded hover:bg-gray-200">Refresh Book</button>
                  <label className="text-sm text-gray-600">Voice:
                    <select value={selectedVoice} onChange={(e) => setSelectedVoice(e.target.value)} className="ml-2 border rounded px-2 py-1 text-sm">
                      <option value="">default</option>
                      {voices.map(v => (
                        <option key={v.name} value={v.name}>{v.name}</option>
                      ))}
                    </select>
                  </label>
                  <button onClick={generateTTSFromCurrent} disabled={!sentences.length || ttsLoading} className="px-3 py-1.5 bg-gray-900 text-white rounded disabled:opacity-50">Generate TTS</button>
                  <span className="text-sm text-gray-500">Speed: {speed.toFixed(2)}×</span>
                </div>
                {message && <div className="mt-2 text-sm text-gray-600">{message}</div>}
                <input type="file" accept=".txt,.md,.pdf,.epub,.docx" ref={fileInputRef} onChange={onFileChange} className="hidden" />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
