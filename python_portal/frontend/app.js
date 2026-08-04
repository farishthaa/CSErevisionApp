// Python Teaching Portal - Client State and Sync Management

// --- Configuration Defaults ---
const DEFAULT_CONFIG = {
    streamlit_url: 'http://localhost:8502',
    username: 'candidate_python_user',
    supabase_url: '',
    supabase_key: ''
};

// --- Syllabus Outline Generator for 30 Days ---
const SYLLABUS_OUTLINE = {};
const MONTH_NAMES = { 1: "Core Python Development & Programming Basics" };

// Populate Outline Topics
for (let d = 1; d <= 30; d++) {
    const month = 1;
    const week = Math.ceil(d / 8); // ~7-8 days per week
    let topic = `Python Concept Practice`;
    let topics = [];
    let difficulty = "Medium";
    
    if (d === 1) {
        topic = "Variables, Basic Maths, and Functions (Write Code)";
        topics = ["Basics", "Variables", "Functions", "PEP8"];
        difficulty = "Easy";
    } else if (d === 2) {
        topic = "Iterating Lists and Loops (Fill in Blanks)";
        topics = ["Lists", "For Loops", "If-Else", "Fill in Blanks"];
        difficulty = "Easy";
    } else if (d === 3) {
        topic = "Try-Except Blocks (Troubleshoot & Debug)";
        topics = ["Exceptions", "Debugging", "Try-Except", "Troubleshoot"];
        difficulty = "Medium";
    } else {
        // General distribution of topics
        const id = d % 5;
        if (id === 0) { 
            topic = `Python Classes, Objects, & Methods (OOP)`; 
            topics = ["OOP", "Classes", "Methods"]; 
        } else if (id === 1) { 
            topic = `File Operations & Context Managers`; 
            topics = ["File I/O", "with-block", "Context Managers"]; 
            difficulty = "Easy"; 
        } else if (id === 2) { 
            topic = `Advanced Dictionaries, Sets, & Tuples`; 
            topics = ["Data Structures", "Dicts", "Sets", "Tuples"]; 
        } else if (id === 3) { 
            topic = `Python Decorators & Function Wrappers`; 
            topics = ["Advanced Python", "Decorators", "Wrappers"]; 
            difficulty = "Hard"; 
        } else { 
            topic = `List Comprehensions, Generators & Iterators`; 
            topics = ["Performance", "Generators", "Comprehensions"]; 
        }
    }
    
    SYLLABUS_OUTLINE[`day_${d}`] = {
        title: topic,
        topics: topics,
        difficulty: difficulty,
        month: month,
        week: week,
        day: d
    };
}

// --- Application State ---
let appState = {
    activeDay: 'day_1',
    activeTab: 'learn-tab',
    config: { ...DEFAULT_CONFIG },
    content: null,          // Holds parsed content.json
    completedDays: {},      // { day_id: true }
    scores: {},             // { day_id: score }
    logs: [],               // Array of evaluation results
    supabase: null          // Supabase client instance
};

// --- DOM References ---
const daysNav = document.getElementById('days-nav');
const currentDayTitle = document.getElementById('current-day-title');
const currentDayDifficulty = document.getElementById('current-day-difficulty');
const dayCompletionBadge = document.getElementById('day-completion-badge');
const topicTags = document.getElementById('topic-tags');
const learnTab = document.getElementById('learn-tab');
const evaluatorIframe = document.getElementById('evaluator-iframe');
const iframeOverlayConfig = document.getElementById('iframe-overlay-config');
const iframeSrcIndicator = document.getElementById('iframe-src-indicator');

// Modals & Settings
const settingsModal = document.getElementById('settings-modal');
const openSettingsBtn = document.getElementById('open-settings-btn');
const closeSettingsModal = document.getElementById('close-settings-modal');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const resetSettingsBtn = document.getElementById('reset-settings-btn');

// Form inputs
const streamlitUrlInput = document.getElementById('streamlit-url-input');
const usernameInput = document.getElementById('username-input');
const supabaseUrlInput = document.getElementById('supabase-url-input');
const supabaseKeyInput = document.getElementById('supabase-key-input');
const navUsername = document.getElementById('nav-username');
const userAvatarInitial = document.getElementById('user-avatar-initial');
const dbStatusBadge = document.getElementById('db-status-badge');

// Stats Elements
const statRate = document.getElementById('stat-rate');
const statCompleted = document.getElementById('stat-completed');
const statAvgScore = document.getElementById('stat-avg-score');
const syncConnectionInfo = document.getElementById('sync-connection-info');
const syncUseridInfo = document.getElementById('sync-userid-info');
const syncCacheInfo = document.getElementById('sync-cache-info');
const historyLogTable = document.getElementById('history-log-table');

// Manual Sync Triggers
const quickSyncBtn = document.getElementById('quick-sync-btn');
const syncIcon = document.getElementById('sync-icon');
const manualPullCloudBtn = document.getElementById('manual-pull-cloud-btn');
const manualPushCloudBtn = document.getElementById('manual-push-cloud-btn');
const setupBackendBtn = document.getElementById('setup-backend-btn');
const reloadIframeBtn = document.getElementById('reload-iframe-btn');

// Mobile Menu
const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
const closeSidebarMobile = document.getElementById('close-sidebar-mobile');
const sidebar = document.getElementById('sidebar');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    loadLocalSettings();
    initializeSupabase();
    await fetchContent();
    setupEventHandlers();
    
    // Parse initial day from URL hash if present
    if (window.location.hash) {
        const hashDay = window.location.hash.replace('#', '');
        if (SYLLABUS_OUTLINE[hashDay]) {
            appState.activeDay = hashDay;
        }
    }
    
    // Sync initially if Supabase is connected
    if (appState.supabase) {
        try {
            await pullProgressFromSupabase(false); // quiet pull
        } catch (e) {
            console.warn("Initial quiet sync failed:", e);
        }
    }
    
    renderSidebar();
    loadActiveDay();
    updateStatsUI();
});

// --- Loader functions ---
async function fetchContent() {
    try {
        const response = await fetch('content.json');
        if (!response.ok) throw new Error("Content file not found");
        appState.content = await response.json();
    } catch (e) {
        console.warn("Failed to load content.json via fetch, using fallback layout.", e);
        appState.content = { days: {} };
    }
}

function loadLocalSettings() {
    // Load config (isolated with python-specific keys)
    const savedConfig = localStorage.getItem('python_portal_config');
    if (savedConfig) {
        try {
            appState.config = { ...DEFAULT_CONFIG, ...JSON.parse(savedConfig) };
        } catch(e) {
            appState.config = { ...DEFAULT_CONFIG };
        }
    }
    
    // Load local progress cache
    const savedProgress = localStorage.getItem('python_portal_completed_days');
    if (savedProgress) {
        try { appState.completedDays = JSON.parse(savedProgress); } catch(e) {}
    }
    
    const savedScores = localStorage.getItem('python_portal_scores');
    if (savedScores) {
        try { appState.scores = JSON.parse(savedScores); } catch(e) {}
    }
    
    const savedLogs = localStorage.getItem('python_portal_logs');
    if (savedLogs) {
        try { appState.logs = JSON.parse(savedLogs); } catch(e) {}
    }
}

function saveLocalSettings() {
    localStorage.setItem('python_portal_config', JSON.stringify(appState.config));
}

function saveLocalProgressCache() {
    localStorage.setItem('python_portal_completed_days', JSON.stringify(appState.completedDays));
    localStorage.setItem('python_portal_scores', JSON.stringify(appState.scores));
    localStorage.setItem('python_portal_logs', JSON.stringify(appState.logs));
}

function initializeSupabase() {
    const { supabase_url, supabase_key } = appState.config;
    
    if (supabase_url && supabase_key && typeof supabase !== 'undefined') {
        try {
            appState.supabase = supabase.createClient(supabase_url, supabase_key);
            
            // Update UI status badges
            dbStatusBadge.textContent = "Supabase Synced";
            dbStatusBadge.className = "text-[10px] text-emerald-400 uppercase font-bold";
            
            syncConnectionInfo.textContent = "Connected";
            syncConnectionInfo.className = "font-bold text-emerald-400";
            
            const badge = document.getElementById('modal-supabase-indicator');
            badge.className = "w-2.5 h-2.5 rounded-full bg-emerald-500";
            document.getElementById('modal-supabase-text').textContent = "Connected";
            document.getElementById('modal-supabase-text').className = "text-[10px] text-emerald-400 font-semibold";
        } catch (e) {
            console.error("Failed to initialize Supabase:", e);
            appState.supabase = null;
            resetSupabaseUIBadges("Error");
        }
    } else {
        appState.supabase = null;
        resetSupabaseUIBadges("Disconnected");
    }
    
    // Set username text
    navUsername.textContent = appState.config.username;
    userAvatarInitial.textContent = appState.config.username.substring(0, 2).toUpperCase();
    syncUseridInfo.textContent = appState.config.username;
}

function resetSupabaseUIBadges(label) {
    dbStatusBadge.textContent = "Local Cache Only";
    dbStatusBadge.className = "text-[10px] text-slate-500 uppercase font-bold";
    
    syncConnectionInfo.textContent = label;
    syncConnectionInfo.className = "font-bold text-slate-500";
    
    const badge = document.getElementById('modal-supabase-indicator');
    badge.className = "w-2.5 h-2.5 rounded-full bg-slate-600";
    document.getElementById('modal-supabase-text').textContent = label;
    document.getElementById('modal-supabase-text').className = "text-[10px] text-slate-500 font-semibold";
}

// --- Sidebar Renderer ---
function renderSidebar() {
    daysNav.innerHTML = '';
    
    const months = [1]; // 30 days is single course module
    const searchQuery = document.getElementById('day-search').value.toLowerCase();
    
    months.forEach(month => {
        const monthDays = Object.keys(SYLLABUS_OUTLINE).filter(dayId => {
            const dayObj = SYLLABUS_OUTLINE[dayId];
            if (dayObj.month !== month) return false;
            
            if (searchQuery) {
                const matchTitle = dayObj.title.toLowerCase().includes(searchQuery);
                const matchTopics = dayObj.topics.some(t => t.toLowerCase().includes(searchQuery));
                const matchDay = dayId.replace('day_', '').includes(searchQuery);
                return matchTitle || matchTopics || matchDay;
            }
            return true;
        });
        
        if (monthDays.length === 0) return;
        
        const monthHeader = document.createElement('div');
        monthHeader.className = "pt-2 pb-1 text-xs font-bold text-indigo-400/80 uppercase tracking-wider border-b border-slate-800/60 mb-2";
        monthHeader.textContent = `${MONTH_NAMES[month]}`;
        daysNav.appendChild(monthHeader);
        
        const weeksInMonth = [...new Set(monthDays.map(d => SYLLABUS_OUTLINE[d].week))].sort((a,b) => a - b);
        
        weeksInMonth.forEach(week => {
            const weekHeader = document.createElement('div');
            weekHeader.className = "text-[10px] text-slate-500 font-bold uppercase tracking-wider pl-1 mb-1 mt-2";
            weekHeader.textContent = `Week ${week}`;
            daysNav.appendChild(weekHeader);
            
            const weekDays = monthDays.filter(d => SYLLABUS_OUTLINE[d].week === week).sort((a,b) => {
                return parseInt(a.replace('day_','')) - parseInt(b.replace('day_',''));
            });
            
            const ul = document.createElement('ul');
            ul.className = "space-y-1";
            
            weekDays.forEach(dayId => {
                const dayObj = SYLLABUS_OUTLINE[dayId];
                const isCompleted = appState.completedDays[dayId] === true;
                const score = appState.scores[dayId] || 0;
                const isActive = appState.activeDay === dayId;
                
                const li = document.createElement('li');
                
                li.innerHTML = `
                    <button class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-all ${isActive ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'}" data-day="${dayId}">
                        <div class="truncate flex items-center gap-2 pr-2">
                            <span class="font-mono text-xs opacity-60">D${dayObj.day}</span>
                            <span class="truncate text-sm font-medium">${dayObj.title}</span>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0">
                            ${score > 0 ? `<span class="text-[10px] px-1.5 py-0.5 rounded font-mono ${isCompleted ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}">${score}</span>` : ''}
                            ${isCompleted ? 
                                `<i data-lucide="check-circle" class="w-4 h-4 text-emerald-400 shrink-0"></i>` : 
                                `<i data-lucide="circle" class="w-4 h-4 text-slate-700 hover:text-slate-500 shrink-0"></i>`
                            }
                        </div>
                    </button>
                `;
                
                li.querySelector('button').addEventListener('click', () => {
                    appState.activeDay = dayId;
                    window.location.hash = dayId;
                    renderSidebar();
                    loadActiveDay();
                    
                    sidebar.classList.add('-translate-x-full');
                });
                
                ul.appendChild(li);
            });
            
            daysNav.appendChild(ul);
        });
    });
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// --- Content and Iframe Loader ---
function loadActiveDay() {
    const dayId = appState.activeDay;
    let dayData = appState.content?.days?.[dayId] || SYLLABUS_OUTLINE[dayId];
    
    if (!dayData.learning_material) {
        dayData = {
            ...SYLLABUS_OUTLINE[dayId],
            learning_material: `# Day ${dayData.day}: ${dayData.title}\n\nThis day covers **${dayData.topics.join(', ')}**.\n\n### Core Focus:\n- Study Python syntax and execution scopes.\n- Implement functions conforming to specifications.\n\n> [!NOTE]\n> Complete the practice code submission to register your day completion.`,
            coding_challenge: {
                title: `${dayData.title} Coding Sandbox`,
                description: `Review the syllabus for **${dayData.title}** and solve a functional programming solution in the editor.`,
                starter_code: "def run_tutor_sandbox():\n    # Implement Python solutions here\n    return True"
            }
        };
    }
    
    currentDayTitle.textContent = `Day ${dayData.day || dayId.replace('day_','')}: ${dayData.title}`;
    currentDayDifficulty.textContent = dayData.difficulty || "Medium";
    
    const diff = (dayData.difficulty || "Medium").toLowerCase();
    if (diff === 'easy') {
        currentDayDifficulty.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-950 text-emerald-400 border border-emerald-900/50";
    } else if (diff === 'hard') {
        currentDayDifficulty.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-950 text-rose-400 border border-rose-900/50";
    } else {
        currentDayDifficulty.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-950 text-indigo-400 border border-indigo-900/30";
    }
    
    const isCompleted = appState.completedDays[dayId] === true;
    if (isCompleted) {
        dayCompletionBadge.classList.remove('hidden');
        dayCompletionBadge.classList.add('flex');
    } else {
        dayCompletionBadge.classList.add('hidden');
        dayCompletionBadge.classList.remove('flex');
    }
    
    topicTags.innerHTML = '';
    const topics = dayData.topics || [];
    topics.forEach(tag => {
        const span = document.createElement('span');
        span.className = "px-2 py-0.5 bg-slate-900 border border-slate-800 rounded text-[11px] font-medium text-slate-400";
        span.textContent = tag;
        topicTags.appendChild(span);
    });
    
    if (typeof marked !== 'undefined') {
        learnTab.innerHTML = marked.parse(dayData.learning_material || '');
    } else {
        learnTab.textContent = dayData.learning_material || '';
    }
    
    setupEvaluatorIframeUrl();
}

function setupEvaluatorIframeUrl() {
    const { streamlit_url, username } = appState.config;
    
    if (!streamlit_url) {
        iframeOverlayConfig.classList.remove('hidden');
        evaluatorIframe.src = "";
        return;
    }
    
    iframeOverlayConfig.classList.add('hidden');
    
    const cleanStreamlitUrl = streamlit_url.endsWith('/') ? streamlit_url.slice(0, -1) : streamlit_url;
    // Includes ?embed=true to prevent clickjacking and loop redirects in browser
    const finalUrl = `${cleanStreamlitUrl}/?embed=true&day_id=${appState.activeDay}&user_id=${encodeURIComponent(username)}`;
    
    if (evaluatorIframe.src !== finalUrl) {
        evaluatorIframe.src = finalUrl;
        iframeSrcIndicator.textContent = streamlit_url.includes('localhost') ? "Local Sandbox" : "Cloud Sandbox";
    }
}

// --- Supabase Cloud Sync Actions ---
async function pushProgressToSupabase() {
    if (!appState.supabase) {
        alert("Supabase integration is not configured. Input credentials in Settings first.");
        return;
    }
    
    syncIcon.classList.add('animate-spin');
    
    try {
        const username = appState.config.username;
        const uploadRows = [];
        
        for (const dayId in appState.completedDays) {
            const completed = appState.completedDays[dayId];
            const score = appState.scores[dayId] || 0;
            
            const logEntry = appState.logs.find(l => l.day_id === dayId) || {};
            
            uploadRows.push({
                user_id: username,
                day_id: dayId,
                completed: completed,
                score: score,
                code_submission: logEntry.code || '',
                feedback: logEntry.feedback || 'Synced from local cache.'
            });
        }
        
        if (uploadRows.length === 0) {
            alert("No cached python portal items found to push.");
            syncIcon.classList.remove('animate-spin');
            return;
        }
        
        // Target: python_portal_progress table
        const { error } = await appState.supabase
            .from('python_portal_progress')
            .upsert(uploadRows, { onConflict: 'user_id,day_id' });
            
        if (error) throw error;
        
        alert(`Successfully synced ${uploadRows.length} Python progress records to Supabase Cloud!`);
        await pullProgressFromSupabase(true);
        
    } catch (e) {
        console.error("Cloud push error:", e);
        alert(`Failed to push to cloud: ${e.message || e}`);
    } finally {
        syncIcon.classList.remove('animate-spin');
    }
}

async function pullProgressFromSupabase(showAlert = true) {
    if (!appState.supabase) {
        if (showAlert) alert("Supabase integration is not configured.");
        return;
    }
    
    syncIcon.classList.add('animate-spin');
    
    try {
        const username = appState.config.username;
        
        // Target: python_portal_progress table
        const { data, error } = await appState.supabase
            .from('python_portal_progress')
            .select('*')
            .eq('user_id', username);
            
        if (error) throw error;
        
        if (data && data.length > 0) {
            appState.completedDays = {};
            appState.scores = {};
            
            data.forEach(row => {
                appState.completedDays[row.day_id] = row.completed;
                appState.scores[row.day_id] = row.score;
                
                const exists = appState.logs.some(l => l.day_id === row.day_id);
                if (!exists) {
                    appState.logs.push({
                        day_id: row.day_id,
                        score: row.score,
                        status: row.completed ? 'PASSED' : 'REDO',
                        feedback: row.feedback || '',
                        code: row.code_submission || '',
                        timestamp: row.updated_at || new Date().toISOString()
                    });
                }
            });
            
            saveLocalProgressCache();
            renderSidebar();
            loadActiveDay();
            updateStatsUI();
            
            if (showAlert) alert(`Successfully pulled ${data.length} records from Supabase!`);
        } else {
            if (showAlert) alert("No records found for this user in the database.");
        }
    } catch (e) {
        console.error("Cloud pull error:", e);
        if (showAlert) alert(`Failed to pull cloud sync: ${e.message || e}`);
    } finally {
        syncIcon.classList.remove('animate-spin');
    }
}

// --- UI Stats updates ---
function updateStatsUI() {
    const totalDays = 30; // 30 Day Course
    const completedCount = Object.keys(appState.completedDays).filter(k => appState.completedDays[k]).length;
    const rate = Math.round((completedCount / totalDays) * 100);
    
    document.getElementById('progress-percent').textContent = `${completedCount} / ${totalDays} (${rate}%)`;
    document.getElementById('progress-bar').style.width = `${rate}%`;
    
    statRate.textContent = `${rate}%`;
    statCompleted.textContent = `${completedCount} / ${totalDays}`;
    
    const scoreValues = Object.values(appState.scores);
    const avgScore = scoreValues.length > 0 ? Math.round(scoreValues.reduce((sum, val) => sum + val, 0) / scoreValues.length) : 0;
    statAvgScore.textContent = `${avgScore} / 100`;
    
    syncCacheInfo.textContent = `${Object.keys(appState.completedDays).length} records`;
    
    historyLogTable.innerHTML = '';
    if (appState.logs.length === 0) {
        historyLogTable.innerHTML = `
            <tr>
                <td colspan="5" class="px-4 py-8 text-center text-slate-500">No submissions found. Start a practice challenge.</td>
            </tr>
        `;
        return;
    }
    
    const sortedLogs = [...appState.logs].sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    sortedLogs.forEach(entry => {
        const dayNum = entry.day_id.replace('day_', '');
        const dayTitle = SYLLABUS_OUTLINE[entry.day_id]?.title || "Python Topic";
        const dateStr = new Date(entry.timestamp).toLocaleDateString(undefined, {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
        const isPassed = entry.status === 'PASSED';
        
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-900/60 transition-colors border-b border-slate-900";
        tr.innerHTML = `
            <td class="px-4 py-3 font-mono font-bold text-xs text-indigo-400">Day ${dayNum}</td>
            <td class="px-4 py-3 font-medium text-slate-200">
                ${dayTitle}
                <div class="text-[10px] text-slate-500 max-w-sm truncate mt-0.5">${entry.feedback}</div>
            </td>
            <td class="px-4 py-3 text-center font-mono font-bold ${isPassed ? 'text-emerald-400' : 'text-amber-400'}">${entry.score}</td>
            <td class="px-4 py-3 text-center">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isPassed ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}">
                    ${entry.status}
                </span>
            </td>
            <td class="px-4 py-3 text-xs text-slate-500 font-medium">${dateStr}</td>
        `;
        historyLogTable.appendChild(tr);
    });
}

// --- Tab Triggers ---
function setupEventHandlers() {
    document.querySelectorAll('.tab-trigger').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            const targetTab = trigger.getAttribute('data-tab');
            
            document.querySelectorAll('.tab-trigger').forEach(t => {
                t.classList.remove('border-indigo-500', 'text-indigo-400');
                t.classList.add('border-transparent', 'text-slate-400');
            });
            trigger.classList.add('border-indigo-500', 'text-indigo-400');
            trigger.classList.remove('border-transparent', 'text-slate-400');
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(targetTab).classList.add('active');
            
            appState.activeTab = targetTab;
            
            if (targetTab === 'practice-tab') {
                setupEvaluatorIframeUrl();
            }
        });
    });
    
    openSettingsBtn.addEventListener('click', () => {
        streamlitUrlInput.value = appState.config.streamlit_url || '';
        usernameInput.value = appState.config.username || 'candidate_python_user';
        supabaseUrlInput.value = appState.config.supabase_url || '';
        supabaseKeyInput.value = appState.config.supabase_key || '';
        
        settingsModal.classList.remove('hidden');
    });
    
    closeSettingsModal.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });
    
    resetSettingsBtn.addEventListener('click', () => {
        streamlitUrlInput.value = DEFAULT_CONFIG.streamlit_url;
        usernameInput.value = DEFAULT_CONFIG.username;
        supabaseUrlInput.value = '';
        supabaseKeyInput.value = '';
    });
    
    saveSettingsBtn.addEventListener('click', () => {
        appState.config = {
            streamlit_url: streamlitUrlInput.value.trim(),
            username: usernameInput.value.trim() || 'candidate_python_user',
            supabase_url: supabaseUrlInput.value.trim(),
            supabase_key: supabaseKeyInput.value.trim()
        };
        
        saveLocalSettings();
        initializeSupabase();
        setupEvaluatorIframeUrl();
        updateStatsUI();
        
        settingsModal.classList.add('hidden');
    });
    
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.add('hidden');
        }
    });
    
    document.getElementById('day-search').addEventListener('input', () => {
        renderSidebar();
    });
    
    quickSyncBtn.addEventListener('click', () => {
        if (appState.supabase) {
            pullProgressFromSupabase(true);
        } else {
            alert("No Supabase configuration detected.");
        }
    });
    
    manualPullCloudBtn.addEventListener('click', () => {
        pullProgressFromSupabase(true);
    });
    
    manualPushCloudBtn.addEventListener('click', () => {
        pushProgressToSupabase();
    });
    
    setupBackendBtn.addEventListener('click', () => {
        openSettingsBtn.click();
    });
    
    reloadIframeBtn.addEventListener('click', () => {
        const temp = evaluatorIframe.src;
        evaluatorIframe.src = "";
        setTimeout(() => {
            evaluatorIframe.src = temp;
        }, 100);
    });
    
    mobileSidebarToggle.addEventListener('click', () => {
        sidebar.classList.remove('-translate-x-full');
    });
    closeSidebarMobile.addEventListener('click', () => {
        sidebar.classList.add('-translate-x-full');
    });
    
    // --- Message listener for iframe sandbox evaluation updates ---
    window.addEventListener('message', async (event) => {
        const data = event.data;
        if (data && data.type === 'SDE_PORTAL_EVALUATION') { // shares matching protocol for parent compatibility
            console.log("Captured evaluation message in dashboard:", data);
            
            const { day_id, score, completed, feedback } = data;
            
            appState.completedDays[day_id] = completed;
            appState.scores[day_id] = score;
            
            const logEntry = {
                day_id: day_id,
                score: score,
                status: completed ? 'PASSED' : 'REDO',
                feedback: feedback || '',
                code: '',
                timestamp: new Date().toISOString()
            };
            
            appState.logs = appState.logs.filter(l => l.day_id !== day_id);
            appState.logs.push(logEntry);
            
            saveLocalProgressCache();
            
            renderSidebar();
            loadActiveDay();
            updateStatsUI();
        }
    });
}
