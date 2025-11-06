/**
 * ReadMe Electron Preload Script
 * Safely exposes IPC methods to the React frontend
 * Implements contextBridge for security
 */

const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose protected methods that allow the renderer process
 * to communicate with the main process and Python backend
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // Health check
  healthCheck: () => ipcRenderer.invoke('health-check'),

  // Book management
  fetchBooks: () => ipcRenderer.invoke('fetch-books'),
  importBook: (filePath) => ipcRenderer.invoke('import-book', filePath),
  getBook: (bookId) => ipcRenderer.invoke('get-book', bookId),

  // Annotations
  createAnnotation: (data) => ipcRenderer.invoke('create-annotation', data),
  getAnnotations: (bookId) => ipcRenderer.invoke('get-annotations', bookId),

  // TTS
  generateTTS: (data) => ipcRenderer.invoke('generate-tts', data),

  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  updateSettings: (data) => ipcRenderer.invoke('update-settings', data),

  // Summarization
  summarizeText: (text) => ipcRenderer.invoke('summarize-text', text),
});

console.log('[Preload] IPC bridge initialized');
