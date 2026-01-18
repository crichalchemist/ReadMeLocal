import React, { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import { baseMsForWpm, tokenDelayMs } from "./rsvp/timing";

const API_BASE = "http://localhost:5000";

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
  const nextAtRef = useRef(0);

  useEffect(() => {
    fetch(`${API_BASE}/api/library`)
      .then((res) => {
        if (!res.ok) {
          throw new Error("Library not configured. Set library_path in settings.yaml.");
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
  }, []);

  const baseMs = useMemo(() => baseMsForWpm(wpm), [wpm]);

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
    setPlaying(false);
    nextAtRef.current = 0;
  };

  const togglePlay = () => {
    setPlaying((prev) => {
      if (!prev) {
        nextAtRef.current = 0;
      }
      return !prev;
    });
  };

  const handleWpmChange = (event) => {
    const value = clamp(Number(event.target.value), 150, 1024);
    setWpm(value);
    nextAtRef.current = 0;
  };

  return (
    <div className="app">
      <aside className="library">
        <div className="library-header">
          <h2>Library</h2>
          <p className="library-subtitle">Local PDF + EPUB collection</p>
        </div>
        {error ? <div className="error">{error}</div> : null}
        <ul className="library-list">
          {library.map((item) => (
            <li key={item.id}>
              <button type="button" onClick={() => loadBook(item.id)}>
                {item.title}
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main className="reader">
        <header className="reader-header">
          <div>
            <h1>{book?.title || "Select a book"}</h1>
            <p>{book?.author || ""}</p>
          </div>
          <div className="controls">
            <button type="button" onClick={togglePlay} disabled={tokens.length === 0}>
              {playing ? "Pause" : "Play"}
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
            <p key={i}>{paragraph}</p>
          ))}
        </section>
      </main>
    </div>
  );
}

export default App;
