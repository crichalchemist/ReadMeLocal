/**
 * ReadMe Electron Main Process
 * Manages window creation, Python backend subprocess, and IPC communication
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

// Python backend configuration
const PYTHON_PORT = 5000;
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

/**
 * Start Python FastAPI backend server
 */
function startPythonBackend() {
  const backendPath = path.join(__dirname, '../../backend');
  const pythonScript = path.join(backendPath, 'main.py');

  console.log('[Backend] Starting Python server...');
  console.log('[Backend] Path:', pythonScript);

  // Use python3 or python depending on system
  const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';

  pythonProcess = spawn(pythonCommand, [pythonScript], {
    cwd: backendPath,
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log('[Backend]', data.toString().trim());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error('[Backend Error]', data.toString().trim());
  });

  pythonProcess.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
  });

  // Give the server a moment to start
  return new Promise(resolve => setTimeout(resolve, 2000));
}

/**
 * Stop Python backend gracefully
 */
function stopPythonBackend() {
  if (pythonProcess) {
    console.log('[Backend] Stopping Python server...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'default',
    show: false // Don't show until ready
  });

  // Load React app
  const startUrl = isDev
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../build/index.html')}`;

  mainWindow.loadURL(startUrl);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * App lifecycle events
 */
app.whenReady().then(async () => {
  await startPythonBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopPythonBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopPythonBackend();
});

/**
 * IPC Handlers - Communication bridge between React and Python backend
 */

// Health check
ipcMain.handle('health-check', async () => {
  try {
    const response = await fetch(`http://localhost:${PYTHON_PORT}/api/health`);
    return await response.json();
  } catch (error) {
    console.error('[IPC] Health check failed:', error);
    return { status: 'error', message: error.message };
  }
});

console.log('[Main] Electron app starting...');