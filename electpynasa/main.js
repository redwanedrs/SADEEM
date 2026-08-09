/**
 * main.js
 * -------
 * Electron main-process entry point. Responsibilities:
 *
 *   1. Manage the BrowserWindow lifecycle (create, activate, close).
 *   2. Register IPC handlers for the renderer (file picker, message relay).
 *   3. Resolve the Python interpreter and CLI script paths in a portable
 *      way so the renderer can spawn pipeline processes without hardcoding.
 *
 * Security notes
 * --------------
 * The renderer is loaded with ``contextIsolation: true`` and
 * ``nodeIntegration: false``. The preload script exposes a single,
 * audited ``window.electpynasa`` API surface. No ``require`` leaks into
 * the renderer.
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// ---------------------------------------------------------------------------
// GPU workaround — prevents black/blank window on Linux
// ---------------------------------------------------------------------------
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('disable-gpu');

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const APP_NAME = 'electPyNasa';
const APP_TITLE = 'electPyNasa — Astronomical Image Processing Engine';

// Resolve the project root (the directory that contains this file).
const PROJECT_ROOT = __dirname;

// The Python entry-point scripts live under scripts/ for backward
// compatibility with the original Electron app.
const SCRIPTS_DIR = path.join(PROJECT_ROOT, 'scripts');

// The Python package source lives under src/. We inject it into PYTHONPATH
// so the scripts can `import electpynasa.*` without an explicit install step.
const SRC_DIR = path.join(PROJECT_ROOT, 'src');

// ---------------------------------------------------------------------------
// Window lifecycle
// ---------------------------------------------------------------------------
let mainWindow = null;

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 1000,
        minWidth: 820,
        minHeight: 720,
        backgroundColor: '#0f0f11',
        title: APP_TITLE,
        show: true,
        center: true,
        webPreferences: {
            preload: path.join(PROJECT_ROOT, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: false,
        },
    });

    // Debug: capture all renderer console messages
    mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
        console.log(`[RENDERER] ${message}`);
    });

    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
        console.error(`[LOAD FAILED] code=${errorCode} desc=${errorDescription} url=${validatedURL}`);
    });

    mainWindow.webContents.on('did-finish-load', () => {
        console.log('[LOAD OK] Page finished loading.');
    });

    mainWindow.webContents.on('dom-ready', () => {
        console.log('[DOM READY] DOM is ready.');
    });

    const htmlPath = path.join(PROJECT_ROOT, 'renderer', 'index.html');
    console.log(`[DEBUG] Loading file: ${htmlPath}`);
    console.log(`[DEBUG] File exists: ${fs.existsSync(htmlPath)}`);

    mainWindow.loadFile(htmlPath);

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // DevTools open for debugging:
    mainWindow.webContents.openDevTools({ mode: 'detach' });
}

app.whenReady().then(() => {
    createMainWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createMainWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// ---------------------------------------------------------------------------
// IPC: file picker
// ---------------------------------------------------------------------------
ipcMain.handle('dialog:openFile', async (event, options = {}) => {
    const filters = options.filters || [
        { name: 'Astronomical', extensions: ['fits', 'fit', 'tif', 'tiff'] },
        { name: 'Common Graphics', extensions: ['jpg', 'jpeg', 'png', 'webp'] },
        { name: 'All Files', extensions: ['*'] },
    ];

    const { canceled, filePaths } = await dialog.showOpenDialog({
        title: options.title || 'Select an image',
        properties: ['openFile'],
        filters,
    });

    if (canceled || !filePaths.length) {
        return null;
    }
    return filePaths[0];
});

// ---------------------------------------------------------------------------
// IPC: environment discovery
// ---------------------------------------------------------------------------
ipcMain.handle('env:resolvePython', async () => {
    /**
     * Resolve the Python interpreter to use for pipeline execution.
     * Order of preference:
     *   1. ELECTPYNASA_PYTHON env var
     *   2. 'python3' on unix, 'python' on windows
     */
    if (process.env.ELECTPYNASA_PYTHON) {
        return process.env.ELECTPYNASA_PYTHON;
    }
    return process.platform === 'win32' ? 'python' : 'python3';
});

ipcMain.handle('env:resolveScript', async (event, scriptRelativePath) => {
    /**
     * Resolve a script path under scripts/ and verify it exists.
     * Returns the absolute path or throws.
     */
    const abs = path.join(SCRIPTS_DIR, scriptRelativePath);
    if (!fs.existsSync(abs)) {
        throw new Error(`Script not found: ${abs}`);
    }
    return abs;
});

ipcMain.handle('env:pythonPath', async () => {
    /**
     * Return the PYTHONPATH that should be set when spawning Python scripts.
     * The src/ directory contains the electpynasa package; injecting it into
     * PYTHONPATH means the app works without `pip install electpynasa`.
     */
    return SRC_DIR;
});
