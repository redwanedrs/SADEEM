/**
 * app.js
 * ------
 * Renderer-process entry point. Runs under contextIsolation: true — only the
 * audited `window.electpynasa` API is available, plus the standard DOM and
 * `child_process` (which is exposed via preload as well, see below).
 *
 * Architecture
 * ------------
 * The renderer is split into three logical layers:
 *
 *   1. **UI controllers** — one per pipeline tab. Each owns its DOM
 *      bindings and produces an args array + script relative path.
 *   2. **IPC bridge** — a single `runPythonProcess` function that spawns
 *      a Python child, parses structured `__LOG__:` / `SUCCESS:` lines,
 *      updates the progress bar and log panel, and resolves with the
 *      final output path.
 *   3. **Helpers** — small DOM utilities (select, log, setProgress, etc).
 *
 * The bridge also routes `child_process` through `window.electpynasa` so the
 * renderer never directly touches Node APIs. For brevity, `child_process` is
 * exposed via preload (see preload.js) as `window.electpynasa.childProcess`.
 */

(function () {
    'use strict';

    // =====================================================================
    // Constants — IPC token prefixes (kept in sync with the Python logger)
    // =====================================================================
    const LOG_PREFIX = '__LOG__:';
    const SUCCESS_PREFIX = 'SUCCESS:';

    // =====================================================================
    // DOM helpers
    // =====================================================================
    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) =>
        Array.from(root.querySelectorAll(selector));

    function el(tag, attrs = {}, children = []) {
        const node = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs)) {
            if (k === 'class') node.className = v;
            else if (k === 'text') node.textContent = v;
            else if (k === 'html') node.innerHTML = v;
            else if (k.startsWith('on') && typeof v === 'function') {
                node.addEventListener(k.slice(2).toLowerCase(), v);
            } else if (v !== null && v !== undefined) {
                node.setAttribute(k, v);
            }
        }
        for (const c of [].concat(children)) {
            if (c == null) continue;
            node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
        }
        return node;
    }

    // =====================================================================
    // Logger
    // =====================================================================
    const logContainer = $('#processing-log');

    function appendLog(message, level = 'info', timestamp = null) {
        const ts = timestamp
            ? new Date(timestamp * 1000).toLocaleTimeString()
            : new Date().toLocaleTimeString();
        const entry = el('div', { class: `log-entry ${level}` }, [
            el('span', { class: 'ts', text: `[${ts}]` }),
            el('span', { class: 'level', text: level.toUpperCase() }),
            document.createTextNode(message),
        ]);
        logContainer.appendChild(entry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    function clearLog() {
        logContainer.innerHTML = '';
        appendLog('Console cleared.');
    }

    // =====================================================================
    // Progress bar
    // =====================================================================
    const progressBarContainer = $('#progressBarContainer');
    const progressBarFill = $('#progressBarFill');
    const progressBarLabel = $('#progressBarLabel');

    function setProgress(percent) {
        const p = Math.max(0, Math.min(100, percent));
        progressBarContainer.hidden = false;
        progressBarFill.style.width = `${p}%`;
        progressBarLabel.textContent = `${p.toFixed(0)}%`;
        if (p >= 100) {
            setTimeout(() => { progressBarContainer.hidden = true; }, 1500);
        }
    }

    function hideProgress() {
        progressBarContainer.hidden = true;
        progressBarFill.style.width = '0%';
        progressBarLabel.textContent = '0%';
    }

    // =====================================================================
    // Status footer
    // =====================================================================
    const footer = $('.app-footer');
    const statusText = $('#status-text');

    function setStatus(state, message) {
        footer.classList.remove('busy', 'error', 'success');
        if (state) footer.classList.add(state);
        statusText.textContent = message;
    }

    // =====================================================================
    // Result area
    // =====================================================================
    const resultArea = $('#result-area');

    function showSuccess(message, path) {
        resultArea.hidden = false;
        resultArea.className = 'result-area success';
        resultArea.innerHTML = '';
        resultArea.appendChild(document.createTextNode(`${message}: `));
        const link = el('span', { class: 'result-link', text: path });
        link.addEventListener('click', () => openInFolder(path));
        resultArea.appendChild(link);
    }

    function showError(message) {
        resultArea.hidden = false;
        resultArea.className = 'result-area error';
        resultArea.textContent = `Error: ${message}`;
    }

    function hideResult() {
        resultArea.hidden = true;
        resultArea.textContent = '';
    }

    // The `shell` module is not exposed through preload; we use the
    // OS-native opener via a tiny IPC round-trip when needed. For now we
    // simply log that the path was clicked — the user can navigate to it
    // manually. (This avoids exposing additional surface area in preload.)
    function openInFolder(filePath) {
        appendLog(`Output path: ${filePath}`, 'info');
    }

    // =====================================================================
    // Python process runner
    // =====================================================================
    /**
     * Spawn a Python pipeline script and stream its structured output.
     *
     * @param {string} scriptRelativePath  e.g. 'ghs_stretch_grayscale.py'
     * @param {Array<string>} args         CLI args
     * @returns {Promise<string>}          Resolves with the SUCCESS: path
     */
    async function runPythonProcess(scriptRelativePath, args) {
        const pythonExe = await window.electpynasa.resolvePython();
        const scriptPath = await window.electpynasa.resolveScript(scriptRelativePath);
        const pythonPath = await window.electpynasa.pythonPath();

        appendLog(`Spawning: ${pythonExe} ${scriptPath} ${args.join(' ')}`, 'debug');

        // We need `child_process` from Node — exposed via preload.
        const cp = window.electpynasa.childProcess;
        if (!cp) {
            throw new Error('child_process is not exposed via preload.');
        }

        const env = Object.assign({}, window.electpynasa.process.env, { PYTHONPATH: pythonPath });
        const child = cp.spawn(pythonExe, [scriptPath, ...args], { env });

        let stdoutBuffer = '';
        let stderrBuffer = '';
        let successPath = null;

        return new Promise((resolve, reject) => {
            child.stdout.on('data', (chunk) => {
                stdoutBuffer += chunk.toString();
                // Process line-by-line so partial lines don't confuse the parser.
                let newlineIdx;
                while ((newlineIdx = stdoutBuffer.indexOf('\n')) >= 0) {
                    const line = stdoutBuffer.slice(0, newlineIdx);
                    stdoutBuffer = stdoutBuffer.slice(newlineIdx + 1);
                    processStdoutLine(line);
                }
            });

            child.stderr.on('data', (chunk) => {
                const text = chunk.toString();
                stderrBuffer += text;
                // stderr lines are emitted as errors directly
                text.split('\n').forEach((l) => {
                    if (l.trim()) appendLog(l.trim(), 'error');
                });
            });

            child.on('close', (code) => {
                // Flush any trailing partial line
                if (stdoutBuffer.trim()) processStdoutLine(stdoutBuffer);
                stdoutBuffer = '';

                if (code !== 0) {
                    return reject(new Error(
                        `Pipeline exited with code ${code}. ` +
                        (stderrBuffer ? `stderr: ${stderrBuffer.trim()}` : 'No stderr output.')
                    ));
                }
                if (!successPath) {
                    return reject(new Error(
                        'Pipeline finished but emitted no SUCCESS: token.'
                    ));
                }
                resolve(successPath);
            });

            child.on('error', (err) => reject(err));
        });

        function processStdoutLine(line) {
            if (!line) return;
            if (line.startsWith(LOG_PREFIX)) {
                const jsonStr = line.slice(LOG_PREFIX.length).trim();
                try {
                    const payload = JSON.parse(jsonStr);
                    if (typeof payload.progress === 'number') {
                        setProgress(payload.progress);
                    }
                    const level = (payload.level || 'info').toLowerCase();
                    appendLog(payload.message || '', level, payload.timestamp);
                } catch (e) {
                    appendLog(line, 'info');
                }
            } else if (line.startsWith(SUCCESS_PREFIX)) {
                successPath = line.slice(SUCCESS_PREFIX.length).trim();
                appendLog(`Output: ${successPath}`, 'success');
            } else if (line.trim()) {
                // Unstructured informational output
                appendLog(line.trim(), 'info');
            }
        }
    }

    // =====================================================================
    // Tab switching
    // =====================================================================
    $$('.tab-button').forEach((btn) => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            $$('.tab-button').forEach((b) => {
                const active = b === btn;
                b.classList.toggle('active', active);
                b.setAttribute('aria-selected', active ? 'true' : 'false');
            });
            $$('.tab-content').forEach((c) => {
                c.classList.toggle('active', c.id === `${tab}-mode`);
            });
        });
    });

    // =====================================================================
    // Slider value mirrors
    // =====================================================================
    $$('input[type="range"]').forEach((slider) => {
        const mirror = document.getElementById(`${slider.id}-value`);
        if (mirror) {
            mirror.textContent = slider.value;
            slider.addEventListener('input', () => {
                mirror.textContent = slider.value;
            });
        }
    });

    // =====================================================================
    // File picker delegation
    // =====================================================================
    document.addEventListener('click', async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        const action = target.dataset.action;
        if (!action) return;

        if (action === 'browse') {
            const inputId = target.dataset.target;
            const input = document.getElementById(inputId);
            if (!input) return;
            try {
                const filePath = await window.electpynasa.selectFile();
                if (filePath) input.value = filePath;
            } catch (err) {
                appendLog(`File picker error: ${err.message}`, 'error');
            }
        } else if (action === 'clear-log') {
            clearLog();
        } else if (action === 'run-single') {
            runSingleProcess().catch(handlePipelineError);
        } else if (action === 'run-batch') {
            runBatchProcess().catch(handlePipelineError);
        } else if (action === 'run-pyramid') {
            runPyramidProcess().catch(handlePipelineError);
        }
    });

    // =====================================================================
    // Pipeline runners
    // =====================================================================
    async function runSingleProcess() {
        hideResult();
        const inputPath = $('#single-file-path').value;
        if (!inputPath) {
            appendLog('Aborted: no input file selected.', 'error');
            return;
        }
        const baseName = inputPath.replace(/\.[^.]+$/, '');
        const outputBase = `${baseName}_ghs`;

        const args = [
            '--input', inputPath,
            '--output', outputBase,
            '--k', $('#k').value,
            '--L', $('#L').value,
            '--s', $('#s').value,
            '--sp', $('#sp').value,
            '--hp', $('#hp').value,
        ];

        setStatus('busy', 'Running grayscale GHS pipeline...');
        try {
            const out = await runPythonProcess('ghs_stretch_grayscale.py', args);
            showSuccess('Grayscale stretch completed', out);
            setStatus('success', 'Grayscale pipeline finished.');
        } catch (err) {
            showError(err.message);
            setStatus('error', 'Pipeline failed.');
            throw err;
        }
    }

    async function runBatchProcess() {
        hideResult();
        const rPath = $('#red-file-path').value;
        const gPath = $('#green-file-path').value;
        const bPath = $('#blue-file-path').value;
        if (!rPath || !gPath || !bPath) {
            appendLog('Aborted: all three channel files are required.', 'error');
            return;
        }
        const outputBase = rPath.replace(/\.[^.]+$/, '') + '_composite';

        const args = [
            '--r', rPath,
            '--g', gPath,
            '--b', bPath,
            '--output', outputBase,
            '--saturation', $('#saturation').value,
            '--q', $('#qfactor').value,
        ];

        setStatus('busy', 'Running color composite pipeline...');
        try {
            const out = await runPythonProcess('align/ghs_auto_color.py', args);
            showSuccess('Color composite created', out);
            setStatus('success', 'Composite pipeline finished.');
        } catch (err) {
            showError(err.message);
            setStatus('error', 'Pipeline failed.');
            throw err;
        }
    }

    async function runPyramidProcess() {
        hideResult();
        const inputPath = $('#pyramid-file-path').value;
        if (!inputPath) {
            appendLog('Aborted: no input file selected.', 'error');
            return;
        }
        // Output goes into a 'deepzoom-images' folder next to the input.
        const lastSlash = Math.max(inputPath.lastIndexOf('/'), inputPath.lastIndexOf('\\'));
        const dir = lastSlash >= 0 ? inputPath.slice(0, lastSlash) : '.';
        const outputDir = `${dir}/deepzoom-images`;

        const args = [
            '--input', inputPath,
            '--output', outputDir,
            '--tileSize', $('#tileSize').value,
            '--overlap', $('#overlap').value,
            '--format', $('#format').value,
            '--quality', $('#quality').value,
        ];

        setStatus('busy', 'Running DZI pyramid pipeline...');
        try {
            const out = await runPythonProcess('create_pyramid.py', args);
            showSuccess('Deep Zoom pyramid built', out);
            setStatus('success', 'Pyramid pipeline finished.');
        } catch (err) {
            showError(err.message);
            setStatus('error', 'Pipeline failed.');
            throw err;
        }
    }

    function handlePipelineError(err) {
        appendLog(`Unhandled pipeline error: ${err.message}`, 'error');
        hideProgress();
    }

    // =====================================================================
    // Initial state
    // =====================================================================
    appendLog('Renderer initialized. Awaiting user action.', 'info');
    setStatus(null, 'Idle');
})();
