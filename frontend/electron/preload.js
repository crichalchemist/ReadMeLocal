/**
 * ReadMe Electron Preload Script
 * Safely exposes minimal IPC methods to the React frontend
 * Implements contextBridge for security
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose only the IPC methods used by the current UI
contextBridge.exposeInMainWorld('electronAPI', {
  healthCheck: () => ipcRenderer.invoke('health-check'),
});

console.log('[Preload] IPC bridge initialized (minimal API)');