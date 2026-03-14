const state = {
    currentTest: null,
    history: [],
    isTesting: false,
    aiConnected: false,
    progressCancelled: false
};

const elements = {};

document.addEventListener('DOMContentLoaded', () => {
    cacheDom();
    bindEvents();
    checkAiStatus();
    loadHistory();
    setInterval(checkAiStatus, 30000);
});

function cacheDom() {
    const ids = [
        'cable-type', 'start-test', 'view-history', 'cable-selector',
        'progress-area', 'progress-fill', 'progress-status', 'progress-percent',
        'result-area', 'result-time', 'test-status', 'cable-type-display',
        's11-value', 's21-value', 's11-status', 's21-status',
        'ai-input', 'ai-ask-btn', 'ai-response', 'ai-content',
        'history-area', 'history-list', 'close-history',
        'ai-status-chip', 'toast'
    ];
    ids.forEach(id => elements[id] = document.getElementById(id));
}

function bindEvents() {
    elements['start-test']?.addEventListener('click', startTest);
    elements['view-history']?.addEventListener('click', showHistory);
    elements['close-history']?.addEventListener('click', hideHistory);
    elements['ai-ask-btn']?.addEventListener('click', askAI);
    elements['ai-input']?.addEventListener('keypress', e => {
        if (e.key === 'Enter') askAI();
    });
}

async function startTest() {
    if (state.isTesting) return;
    state.isTesting = true;
    state.progressCancelled = false;
    elements['start-test'].disabled = true;
    showPanel('progress-area');
    playProgressScript();

    try {
        const cableType = elements['cable-type'].value;
        const response = await fetchWithTimeout('/api/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cable_type: cableType })
        }, 15000);

        const result = await safeJson(response);
        if (!result.success) throw new Error(result.error || '检测失败');

        state.currentTest = result.data;
        updateProgress(100, '检测完成');
        await loadHistory();
        showResult(result.data);
        showPanel('result-area');
    } catch (err) {
        showToast(err.message || '检测失败，请稍后再试');
        showPanel('cable-selector');
    } finally {
        state.progressCancelled = true;
        state.isTesting = false;
        elements['start-test'].disabled = false;
    }
}

function showResult(data) {
    const detail = data.analysis_detail || {};
    const time = data.device_info?.test_time || new Date().toLocaleString();

    elements['result-time'].textContent = time;
    elements['cable-type-display'].textContent = data.cable_type || '-';

    const statusEl = elements['test-status'];
    if (statusEl) {
        statusEl.className = `badge ${data.qualified ? 'badge--pass' : 'badge--fail'}`;
        statusEl.textContent = data.qualified ? '合格 ✓' : '不合格 ✗';
    }

    elements['s11-value'].textContent = formatMetric(detail.s11_mean, data.cable_type, 'S11');
    elements['s21-value'].textContent = formatMetric(detail.s21_mean, data.cable_type, 'S21');

    elements['s11-status'].textContent = data.s11_qualified ? '短路正常' : '短路异常';
    elements['s21-status'].textContent = data.s21_qualified ? '传输正常' : '传输异常';

    elements['ai-input'].value = '';
    elements['ai-response'].classList.add('hidden');
}

function formatMetric(value, cableType, key) {
    if (value === undefined || value === null) return '-';
    if (cableType === 'USB-Type-C' && key === 'S11') {
        return `${Math.abs(value).toFixed(0)} mΩ`;
    }
    if (cableType === 'USB-Type-C' && key === 'S21') {
        return value >= 0 ? '正常' : '异常';
    }
    return `${Number(value).toFixed(1)} dB`;
}

async function askAI() {
    if (!state.currentTest) {
        showToast('请先完成一次检测');
        return;
    }
    if (!state.aiConnected) {
        showToast('AI服务暂不可用');
        return;
    }

    const question = elements['ai-input'].value.trim();
    if (!question) {
        showToast('请输入问题');
        return;
    }

    setAiButtonState(true);
    try {
        const response = await fetchWithTimeout('/api/ai-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ result: state.currentTest, question })
        }, 15000);

        const result = await safeJson(response);
        elements['ai-content'].textContent = result.analysis || 'AI分析失败';
        elements['ai-response'].classList.remove('hidden');
        elements['ai-input'].value = '';
    } catch (err) {
        elements['ai-content'].textContent = 'AI服务暂时不可用';
        elements['ai-response'].classList.remove('hidden');
        showToast(err.message || 'AI分析失败');
    } finally {
        setAiButtonState(false);
    }
}

async function loadHistory() {
    try {
        const response = await fetchWithTimeout('/api/history', {}, 8000);
        const result = await safeJson(response);
        if (result.success) {
            state.history = result.data || [];
            renderHistory();
        }
    } catch (err) {
        console.error('历史记录加载失败', err);
    }
}

function renderHistory() {
    const container = elements['history-list'];
    if (!container) return;

    if (!state.history.length) {
        container.innerHTML = '<p>暂无历史记录</p>';
        return;
    }

    container.innerHTML = state.history.map(item => `
        <div class="history-card">
            <div class="history-card__meta">
                <span>${item.cable_type || '未知'}</span>
                <span class="history-card__status ${item.qualified ? 'pass' : 'fail'}">
                    ${item.qualified ? '合格' : '不合格'}
                </span>
            </div>
            <p>${item.message || ''}</p>
            <small>${item.timestamp || ''}</small>
            <small>S11: ${formatNumber(item.s11_mean)} dB · S21: ${formatNumber(item.s21_mean)} dB</small>
        </div>
    `).join('');
}

function showHistory() {
    showPanel('history-area');
    renderHistory();
}

function hideHistory() {
    if (state.currentTest) {
        showPanel('result-area');
    } else {
        showPanel('cable-selector');
    }
}

async function checkAiStatus() {
    try {
        const response = await fetchWithTimeout('/api/test-ai', {}, 7000);
        const result = await safeJson(response);
        updateAiStatus(Boolean(result.success), result.message);
    } catch (err) {
        updateAiStatus(false, err.message);
    }
}

function updateAiStatus(isConnected, message = '') {
    state.aiConnected = isConnected;
    const chip = elements['ai-status-chip'];
    if (!chip) return;

    chip.classList.toggle('online', isConnected);
    chip.classList.toggle('offline', !isConnected);
    chip.textContent = isConnected ? 'AI 已连接' : 'AI 未连接';
    if (!isConnected && message) {
        console.warn('AI状态', message);
    }
}

function showPanel(targetId) {
    ['cable-selector', 'progress-area', 'result-area', 'history-area'].forEach(id => {
        const panel = elements[id];
        if (!panel) return;
        if (id === targetId) {
            panel.classList.remove('hidden');
        } else {
            panel.classList.add('hidden');
        }
    });
}

function playProgressScript() {
    const steps = [
        { percent: 12, text: '初始化设备…' },
        { percent: 32, text: '校准参数…' },
        { percent: 58, text: '扫频测量…' },
        { percent: 78, text: '数据分析…' },
        { percent: 92, text: '生成报告…' }
    ];

    (async () => {
        for (const step of steps) {
            if (state.progressCancelled) break;
            updateProgress(step.percent, step.text);
            await delay(700);
        }
    })();
}

function updateProgress(percent, text) {
    elements['progress-fill'].style.width = `${percent}%`;
    elements['progress-percent'].textContent = `${percent}%`;
    elements['progress-status'].textContent = text;
}

function setAiButtonState(isLoading) {
    const btn = elements['ai-ask-btn'];
    if (!btn) return;
    btn.disabled = isLoading;
    btn.textContent = isLoading ? '分析中…' : '询问';
}

function showToast(message) {
    const toast = elements['toast'];
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove('hidden');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

async function fetchWithTimeout(resource, options = {}, timeout = 10000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    const response = await fetch(resource, { ...options, signal: controller.signal });
    clearTimeout(id);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response;
}

async function safeJson(response) {
    try {
        return await response.json();
    } catch {
        throw new Error('响应解析失败');
    }
}

function formatNumber(value) {
    if (value === null || value === undefined) return '-';
    return Number(value).toFixed(1);
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

window.addEventListener('error', e => console.error(e));
window.addEventListener('unhandledrejection', e => console.error(e.reason));