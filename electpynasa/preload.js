/**
 * preload.js
 * ----------
 * Context-isolated bridge between the Electron main process and the renderer.
 *
 * Exposes a single, minimal, audited API surface on ``window.electpynasa``
 * so the renderer cannot accidentally touch Node APIs directly.
 *
 * Pipeline execution is delegated to the main process via IPC
 * (``pipeline:run``). The renderer sends the script path and args; the main
 * process spawns the Python child and streams structured output back via
 * ``pipeline:stdout``, ``pipeline:stderr``, and ``pipeline:close`` events.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electpynasa', {
    /**
     * Open a native file-picker dialog and return the selected path
     * (or null if cancelled).
     */
    selectFile: (options) => ipcRenderer.invoke('dialog:openFile', options || {}),

    /**
     * Resolve the Python interpreter to use.
     */
    resolvePython: () => ipcRenderer.invoke('env:resolvePython'),

    /**
     * Resolve a script path under scripts/.
     */
    resolveScript: (scriptRelativePath) =>
        ipcRenderer.invoke('env:resolveScript', scriptRelativePath),

    /**
     * Return the PYTHONPATH that should be set when spawning Python scripts.
     */
    pythonPath: () => ipcRenderer.invoke('env:pythonPath'),

    /**
     * Run a pipeline in the main process. Returns a pipeline ID.
     * The main process spawns the Python child and sends output back
     * via events.
     */
    runPipeline: (scriptRelativePath, args) =>
        ipcRenderer.invoke('pipeline:run', scriptRelativePath, args),

    /**
     * Listen for pipeline stdout lines from the main process.
     */
    onPipelineStdout: (callback) => {
        ipcRenderer.on('pipeline:stdout', (event, line) => callback(line));
    },

    /**
     * Listen for pipeline stderr lines from the main process.
     */
    onPipelineStderr: (callback) => {
        ipcRenderer.on('pipeline:stderr', (event, line) => callback(line));
    },

    /**
     * Listen for pipeline close events from the main process.
     */
    onPipelineClose: (callback) => {
        ipcRenderer.on('pipeline:close', (event, code) => callback(code));
    },
});
