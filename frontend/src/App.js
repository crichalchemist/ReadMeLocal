import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import { baseMsForWpm, tokenDelayMs } from "./rsvp/timing";

// API base: empty for production (same origin via nginx), localhost for dev
const API_BASE = process.env.NODE_ENV === "production" ? "" : "http://localhost:5000";

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

function App() {
  const [library, setLibrary] = useState([]);
  const [book, setBook] = useState(null);
  const [tokens, setTokens] = useState([]);
  const [paragraphs, setParagraphs] = useState([]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [wpm, setWpm] = useState(150);
  const [error, setError] = useState("");
  const [libraryPath, setLibraryPath] = useState("");
  const [savingPath, setSavingPath] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [currentParagraphAudio, setCurrentParagraphAudio] = useState(null);
  const [showAnnotationModal, setShowAnnotationModal] = useState(false);
  const [annotationText, setAnnotationText] = useState("");
  const [annotations, setAnnotations] = useState([]);
  const [pauseTime, setPauseTime] = useState(null);
  const [pausedParagraphIndex, setPausedParagraphIndex] = useState(null);
  const nextAtRef = useRef(0);
  const audioRef = useRef(null);
  const ttsAbortRef = useRef(null);
  const prevParagraphRef = useRef(0);

  const REWIND_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

  const loadLibrary = () => {
    fetch(`${API_BASE}/api/library`)
      .then((res) => {
        if (!res.ok) {
          throw new Error("Library not configured. Set library_path or save a path.");
        }
        return res.json();
      })
      .then((data) => {
        setLibrary(data);
        setError("");
      })
      .catch((err) => {
        setLibrary([]);
        setError(err.message);
      });
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/settings`)
      .then((res) => res.json())
      .then((data) => {
        if (data?.rsvp?.wpm_default) {
          setWpm(data.rsvp.wpm_default);
        }
        if (typeof data?.library_path === "string") {
          setLibraryPath(data.library_path);
        }
      })
      .catch(() => {});

    loadLibrary();
  }, []);

  const baseMs = useMemo(() => baseMsForWpm(wpm), [wpm]);

  const libraryByType = useMemo(() => {
    const groups = {};
    library.forEach((item) => {
      const ext = (item.ext || ".unknown").replace(".", "").toUpperCase();
      if (!groups[ext]) groups[ext] = [];
      groups[ext].push(item);
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [library]);

  // Get current paragraph index from current token (defined early for use in effects)
  const currentParagraphIndex = tokens[index]?.paragraph_index ?? 0;

  // Generate TTS for a paragraph and return the audio URL
  const generateTts = async (text) => {
    if (!text || !ttsEnabled) return null;
    try {
      const res = await fetch(`${API_BASE}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice: "en-US-Neural2-D" }),
      });
      if (!res.ok) {
        console.error("TTS generation failed");
        return null;
      }
      const data = await res.json();
      return {
        url: `${API_BASE}${data.audio_path}`,
        duration: data.duration,
      };
    } catch (err) {
      console.error("TTS error:", err);
      return null;
    }
  };

  // Load annotations when book changes
  useEffect(() => {
    if (book?.id) {
      fetch(`${API_BASE}/api/annotations/${book.id}`)
        .then((res) => res.json())
        .then((data) => setAnnotations(data.annotations || []))
        .catch(() => setAnnotations([]));
    }
  }, [book?.id]);

  const handleCloseAnnotationModal = useCallback(() => {
    setShowAnnotationModal(false);
    setAnnotationText("");

    // Check if we need to rewind (paused > 5 minutes)
    if (pauseTime && Date.now() - pauseTime >= REWIND_THRESHOLD_MS) {
      // Rewind to start of the paused paragraph
      const paragraphStartIndex = tokens.findIndex(
        (t) => t.paragraph_index === pausedParagraphIndex
      );
      if (paragraphStartIndex >= 0) {
        setIndex(paragraphStartIndex);
      }
    }

    setPauseTime(null);
    setPausedParagraphIndex(null);
  }, [pauseTime, tokens, pausedParagraphIndex]);

  const handleSaveAnnotation = useCallback(async () => {
    if (!annotationText.trim() || !book) return;

    const currentParagraph = paragraphs[currentParagraphIndex] || "";

    try {
      const response = await fetch(`${API_BASE}/api/annotations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          book_id: book.id,
          paragraph_index: currentParagraphIndex,
          section_title: null,
          source_text: currentParagraph,
          note_text: annotationText.trim(),
        }),
      });

      if (response.ok) {
        const newAnnotation = await response.json();
        setAnnotations((prev) => [...prev, newAnnotation]);
      }
    } catch (err) {
      console.error("Failed to save annotation:", err);
    }

    handleCloseAnnotationModal();
  }, [annotationText, book, currentParagraphIndex, paragraphs, handleCloseAnnotationModal]);

  const handleExportAnnotations = useCallback(() => {
    if (!book?.id) return;
    window.open(`${API_BASE}/api/annotations/${book.id}/export`, "_blank");
  }, [book]);

  // Handle paragraph transitions for TTS
  useEffect(() => {
    if (!playing || !ttsEnabled) return;
    if (prevParagraphRef.current !== currentParagraphIndex) {
      prevParagraphRef.current = currentParagraphIndex;
      // Load audio for new paragraph
      const loadNextAudio = async () => {
        const paragraphText = paragraphs[currentParagraphIndex];
        if (!paragraphText) return;
        const ttsData = await generateTts(paragraphText);
        if (ttsData && audioRef.current) {
          setCurrentParagraphAudio(ttsData);
          audioRef.current.src = ttsData.url;
          audioRef.current.play().catch((err) => console.error("Audio play error:", err));
        }
      };
      loadNextAudio();
    }
  }, [currentParagraphIndex, playing, ttsEnabled, paragraphs]);

  // Keyboard handler for annotations
  useEffect(() => {
    const handleKeyDown = (e) => {
      // 'N' to open annotation modal (when playing or paused with a book loaded)
      if (e.key === "n" || e.key === "N") {
        if (book && !showAnnotationModal) {
          e.preventDefault();
          setPauseTime(Date.now());
          setPausedParagraphIndex(currentParagraphIndex);
          setPlaying(false);
          setShowAnnotationModal(true);
        }
      }

      // Escape to close modal
      if (e.key === "Escape" && showAnnotationModal) {
        e.preventDefault();
        handleCloseAnnotationModal();
      }

      // Cmd/Ctrl + Enter to save annotation
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && showAnnotationModal) {
        e.preventDefault();
        handleSaveAnnotation();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [book, showAnnotationModal, currentParagraphIndex, playing, handleCloseAnnotationModal, handleSaveAnnotation]);

  useEffect(() => {
    if (!playing || tokens.length === 0) return;
    let rafId;

    const tick = (now) => {
      if (!playing) return;
      if (nextAtRef.current === 0) {
        nextAtRef.current = now + tokenDelayMs(tokens[index] || {}, baseMs);
      }
      if (now >= nextAtRef.current) {
        setIndex((prev) => {
          if (prev >= tokens.length - 1) {
            setPlaying(false);
            if (audioRef.current) {
              audioRef.current.pause();
            }
            nextAtRef.current = 0;
            return prev;
          }
          const next = prev + 1;
          nextAtRef.current = now + tokenDelayMs(tokens[next] || {}, baseMs);
          return next;
        });
      }
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [playing, tokens, index, baseMs]);

  const loadBook = async (bookId) => {
    // Stop any current playback
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
    }
    setPlaying(false);
    setCurrentParagraphAudio(null);

    const res = await fetch(`${API_BASE}/api/books/${bookId}`);
    if (!res.ok) {
      setError("Failed to load book.");
      return;
    }
    const data = await res.json();
    setBook(data);
    setTokens(data.tokens || []);
    setParagraphs(data.paragraphs || []);
    setIndex(0);
    nextAtRef.current = 0;
    prevParagraphRef.current = 0;
  };

  const togglePlay = async () => {
    if (playing) {
      // Pausing
      setPlaying(false);
      if (audioRef.current) {
        audioRef.current.pause();
      }
      return;
    }

    // Starting playback
    nextAtRef.current = 0;

    if (ttsEnabled && paragraphs.length > 0) {
      setTtsLoading(true);
      const paragraphText = paragraphs[currentParagraphIndex];
      const ttsData = await generateTts(paragraphText);
      setTtsLoading(false);

      if (ttsData) {
        setCurrentParagraphAudio(ttsData);
        if (audioRef.current) {
          audioRef.current.src = ttsData.url;
          audioRef.current.play().catch((err) => console.error("Audio play error:", err));
        }
      }
    }

    setPlaying(true);
  };

  const handleWpmChange = (event) => {
    const value = clamp(Number(event.target.value), 150, 1024);
    setWpm(value);
    nextAtRef.current = 0;
  };

  const saveLibraryPath = async () => {
    setSavingPath(true);
    try {
      const res = await fetch(`${API_BASE}/api/library/path`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: libraryPath }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data?.detail || "Failed to save library path");
      }
      const data = await res.json();
      setLibraryPath(data.library_path || "");
      if (Array.isArray(data.items)) {
        setLibrary(data.items);
      } else {
        loadLibrary();
      }
      setError("");
    } catch (err) {
      setError(err.message || "Failed to save library path");
    } finally {
      setSavingPath(false);
    }
  };

  return (
    <div className="app">
      <audio ref={audioRef} style={{ display: "none" }} />
      <aside className="library">
        <div className="library-header">
          <h2>Library</h2>
          <p className="library-subtitle">Local PDF + EPUB collection</p>
        </div>
        <div className="library-config">
          <label htmlFor="library-path">Library path</label>
          <input
            id="library-path"
            type="text"
            value={libraryPath}
            onChange={(event) => setLibraryPath(event.target.value)}
            placeholder="/path/to/books"
          />
          <button type="button" onClick={saveLibraryPath} disabled={savingPath}>
            {savingPath ? "Saving..." : "Save path"}
          </button>
        </div>
        {error ? <div className="error">{error}</div> : null}
        <div className="library-count">{library.length} items</div>
        <div className="library-list">
          {libraryByType.map(([ext, items]) => (
            <div key={ext} className="library-section">
              <h3 className="library-section-header">{ext} ({items.length})</h3>
              <ul>
                {items.map((item) => (
                  <li key={item.id}>
                    <button type="button" onClick={() => loadBook(item.id)}>
                      {item.title}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </aside>
      <main className="reader">
        <header className="reader-header">
          <div>
            <h1>{book?.title || "Select a book"}</h1>
            <p>{book?.author || ""}</p>
          </div>
          <div className="controls">
            <button
              type="button"
              onClick={togglePlay}
              disabled={tokens.length === 0 || ttsLoading}
            >
              {ttsLoading ? "Loading..." : playing ? "Pause" : "Play"}
            </button>
            <button
              type="button"
              className={`tts-toggle ${ttsEnabled ? "active" : ""}`}
              onClick={() => setTtsEnabled((prev) => !prev)}
              title={ttsEnabled ? "TTS On" : "TTS Off"}
            >
              {ttsEnabled ? "🔊" : "🔇"}
            </button>
            <label>
              <span>{wpm} WPM</span>
              <input
                type="range"
                min="150"
                max="1024"
                value={wpm}
                onChange={handleWpmChange}
              />
            </label>
            {annotations.length > 0 && (
              <button onClick={handleExportAnnotations} className="export-btn">
                Export Notes ({annotations.length})
              </button>
            )}
          </div>
        </header>
        <section className="rsvp">
          <div className="focus-guide" />
          <div className="word" key={tokens[index]?.text || ""}>
            {tokens[index]?.text || ""}
          </div>
          <div className="progress">
            {tokens.length ? `${index + 1} / ${tokens.length}` : ""}
          </div>
        </section>
        <section className="context">
          {paragraphs.map((paragraph, i) => (
            <p key={i} className={i === tokens[index]?.paragraph_index ? "active" : ""}>
              {paragraph}
            </p>
          ))}
        </section>
      </main>

      {/* Annotation Modal */}
      {showAnnotationModal && (
        <div className="annotation-modal-overlay">
          <div className="annotation-modal">
            <h3>Add Note</h3>
            <div className="annotation-context">
              <strong>Current paragraph:</strong>
              <p className="annotation-source">
                {paragraphs[currentParagraphIndex]?.substring(0, 200)}
                {paragraphs[currentParagraphIndex]?.length > 200 ? "..." : ""}
              </p>
            </div>
            <textarea
              className="annotation-input"
              placeholder="Type your note here..."
              value={annotationText}
              onChange={(e) => setAnnotationText(e.target.value)}
              autoFocus
            />
            <div className="annotation-buttons">
              <button onClick={handleCloseAnnotationModal}>Cancel (Esc)</button>
              <button onClick={handleSaveAnnotation} className="primary">
                Save (Cmd+Enter)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
