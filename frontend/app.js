// Ensure frontend and backend origins align to prevent strict browser CORS/PNA network errors
// Default to localhost if opened via file:/// protocol (where hostname is empty)
const hostname = window.location.hostname || 'localhost';
const API_BASE = `http://${hostname}:8000/api`;

// ---- Backend Health State ----
// Tracks whether the backend server is reachable. Starts as null (unknown),
// then flips to true/false after the first auth attempt.
let BACKEND_AVAILABLE = null;

// ---- Mock Auth (fallback when backend is offline) ----
function mockSignup(name, email, password) {
    console.log('[MockAuth] Signup attempt for:', email);
    const users = JSON.parse(localStorage.getItem('mock_users') || '{}');
    if (users[email]) {
        return { success: false, error: 'Email already registered (offline mode).' };
    }
    users[email] = { name, password };
    localStorage.setItem('mock_users', JSON.stringify(users));
    const token = 'mock_' + Date.now();
    localStorage.setItem('mock_token_email', email);
    console.log('[MockAuth] Signup successful, token:', token);
    return { success: true, token, name };
}

function mockLogin(email, password) {
    console.log('[MockAuth] Login attempt for:', email);
    const users = JSON.parse(localStorage.getItem('mock_users') || '{}');
    // Accept any email/password — create user on the fly for demo mode
    if (!users[email]) {
        const name = email.split('@')[0];
        users[email] = { name, password };
        localStorage.setItem('mock_users', JSON.stringify(users));
        console.log('[MockAuth] New user auto-created in offline mode.');
    }
    const token = 'mock_' + Date.now();
    localStorage.setItem('mock_token_email', email);
    const name = users[email].name;
    console.log('[MockAuth] Login successful, token:', token);
    return { success: true, token, name };
}

function showAuthError(message) {
    // Show a styled inline error instead of a bare alert when possible
    const errEl = document.getElementById('auth-error-msg');
    if (errEl) {
        errEl.textContent = message;
        errEl.classList.remove('hidden');
        setTimeout(() => errEl.classList.add('hidden'), 6000);
    } else {
        alert(message);
    }
}

function hideAuthError() {
    const errEl = document.getElementById('auth-error-msg');
    if (errEl) errEl.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    // ---- DOM Elements ----
    
    // Sections
    const authSection = document.getElementById('auth-section');
    const inputSection = document.getElementById('input-section');
    const dashboardContainer = document.getElementById('dashboard-container');
    const profileSection = document.getElementById('profile-section');
    const settingsSection = document.getElementById('settings-section');
    const loader = document.getElementById('loader');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const navItems = document.querySelectorAll('.nav-item');
    const aiCoachNavBtn = document.getElementById('ai-coach-nav-btn');
    const backToDashBtn = document.getElementById('back-to-dash-btn');
    const homeSection = document.getElementById('home-section');
    const landingNavbar = document.getElementById('landing-navbar');
    const navAuthBtn = document.getElementById('nav-auth-btn');
    
    // Auth
    const loginContainer = document.getElementById('login-container');
    const signupContainer = document.getElementById('signup-container');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const showSignupBtn = document.getElementById('show-signup');
    const showLoginBtn = document.getElementById('show-login');
    const logoutBtn = document.getElementById('logout-btn');
    const sidebarLogoutBtn = document.getElementById('sidebar-logout');
    
    // Auth Tabs & Org
    const tabIndividual = document.getElementById('tab-individual');
    const tabOrganization = document.getElementById('tab-organization');
    const individualAuth = document.getElementById('individual-auth');
    const organizationAuth = document.getElementById('organization-auth');
    
    const orgLoginContainer = document.getElementById('org-login-container');
    const orgSignupContainer = document.getElementById('org-signup-container');
    const showOrgSignupBtn = document.getElementById('show-org-signup');
    const showOrgLoginBtn = document.getElementById('show-org-login');
    const orgLoginForm = document.getElementById('org-login-form');
    const orgSignupForm = document.getElementById('org-signup-form');
    
    // Forms & Inputs
    const advisorForm = document.getElementById('advisor-form');
    const resetBtn = document.getElementById('reset-btn');
    
    // Chat widget
    const chatWidget = document.getElementById('chat-widget');
    const chatToggle = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatMessages = document.getElementById('chat-messages');

    // Account Bar
    const accountBar = document.getElementById('account-bar');
    const accountProfileBtn = document.getElementById('account-profile-btn');
    const accountDropdown = document.getElementById('account-dropdown');
    const userAvatar = document.getElementById('user-avatar');
    const userNameDisplay = document.getElementById('user-name-display');
    const dropdownLogout = document.getElementById('dropdown-logout');
    
    // Notifications
    const notifBtn = document.getElementById('notif-btn');
    const notifDropdown = document.getElementById('notif-dropdown');
    const notifBadge = document.getElementById('notif-badge');
    const notifList = document.getElementById('notif-list');
    
    let notifications = [];

    let budgetChartInstance = null;
    
    // ---- Global State ----
    window.appState = null;

    // ---- Router Logic ----
    function init() {
        if (!window.location.hash) {
            window.location.hash = localStorage.getItem('token') ? (localStorage.getItem('userType') === 'organization' ? '#org-dashboard' : '#input') : '#home';
        }
        window.addEventListener('hashchange', handleRoute);
        handleRoute();
        
        if (localStorage.getItem('token')) {
            updateAccountBar();
        }
    }

    function handleRoute() {
        const hash = window.location.hash;
        const token = localStorage.getItem('token');

        authSection.classList.add('hidden');
        inputSection.classList.add('hidden');
        dashboardContainer.classList.add('hidden');
        profileSection.classList.add('hidden');
        settingsSection.classList.add('hidden');
        homeSection.classList.add('hidden');
        chatWidget.classList.add('hidden');
        landingNavbar.classList.add('hidden');
        const secOrgInputEl = document.getElementById('sec-org-input');
        const secOrgDashboardEl = document.getElementById('sec-org-dashboard');
        if (secOrgInputEl) secOrgInputEl.classList.add('hidden');
        if (secOrgDashboardEl) secOrgDashboardEl.classList.add('hidden');

        // Smart Back Button State Management
        updateSmartBackButton(hash);

        // Layout Separation logic (CleanLayout vs DashboardLayout)
        const appLayout = document.querySelector('.app-layout');
        const showSidebar = hash.startsWith('#dashboard');

        if (!showSidebar) {
            sidebar.classList.add('hidden');
            if (appLayout) {
                appLayout.classList.add('layout-clean');
                appLayout.classList.remove('layout-dashboard');
            }
        } else {
            sidebar.classList.remove('hidden');
            if (appLayout) {
                appLayout.classList.remove('layout-clean');
                appLayout.classList.add('layout-dashboard');
            }
        }

        // Auth Gate
        const publicRoutes = ['#signup', '#login', '#home', '#org-login', '#org-signup'];
        if (!token && !publicRoutes.includes(hash)) {
            window.location.hash = '#home';
            return;
        }

        // Clear nav highlights; re-apply below where needed
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

        // View Router
        if (hash === '#login' || hash === '#signup' || hash === '#org-login' || hash === '#org-signup') {
            window.appState = null;
            authSection.classList.remove('hidden');
            accountBar.classList.add('hidden');

            if (hash === '#org-login' || hash === '#org-signup') {
                switchAuthTab('organization');
                if (hash === '#org-signup') {
                    orgLoginContainer.classList.add('hidden');
                    orgSignupContainer.classList.remove('hidden');
                } else {
                    orgSignupContainer.classList.add('hidden');
                    orgLoginContainer.classList.remove('hidden');
                }
            } else {
                switchAuthTab('individual');
                if (hash === '#signup') {
                    loginContainer.classList.add('hidden');
                    signupContainer.classList.remove('hidden');
                } else {
                    signupContainer.classList.add('hidden');
                    loginContainer.classList.remove('hidden');
                }
            }
        }
        else if (hash === '#home') {
            homeSection.classList.remove('hidden');
            landingNavbar.classList.remove('hidden');
            accountBar.classList.add('hidden');
        }
        else if (hash === '#input') {
            inputSection.classList.remove('hidden');
            accountBar.classList.remove('hidden');
        }
        else if (hash === '#org-dashboard') {
            accountBar.classList.remove('hidden');
            if (window.loadOrgDashboard) window.loadOrgDashboard();
        }
        else if (hash === '#profile') {
            profileSection.classList.remove('hidden');
            accountBar.classList.remove('hidden');
            chatWidget.classList.remove('hidden');
            loadUserProfile();
        }
        else if (hash === '#settings') {
            settingsSection.classList.remove('hidden');
            accountBar.classList.remove('hidden');
            chatWidget.classList.remove('hidden');
            loadUserSettings();
        }
        else if (hash.startsWith('#dashboard')) {
            if (!window.appState) {
                window.location.hash = '#input';
                return;
            }
            dashboardContainer.classList.remove('hidden');
            accountBar.classList.remove('hidden');
            chatWidget.classList.remove('hidden');

            const tab = hash.split('/')[1] || 'overview';
            document.querySelectorAll('.dashboard-tab').forEach(el => el.classList.add('hidden'));

            const activeTab = document.getElementById(`sec-${tab}`) || document.getElementById('sec-overview');
            activeTab.classList.remove('hidden');

            const activeNav = document.querySelector(`.nav-item[data-target="sec-${tab}"]`);
            if (activeNav) activeNav.classList.add('active');
        }
    }

    // ---- Sidebar Toggle (mobile only — desktop uses CSS hover expansion) ----
    sidebarToggle.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('mobile-open');
        }
        // On desktop the sidebar expands via CSS :hover — no click needed
    });

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            if (item.classList.contains('logout-btn') || item.id === 'ai-coach-nav-btn') return;
            const target = item.getAttribute('data-target'); // e.g., sec-analysis
            if (target) {
                const tabId = target.replace('sec-', '');
                window.location.hash = `#dashboard/${tabId}`;
            }
        });
    });

    if (aiCoachNavBtn) {
        aiCoachNavBtn.addEventListener('click', () => {
            chatWindow.classList.toggle('hidden');
        });
    }

    if (backToDashBtn) {
        backToDashBtn.addEventListener('click', () => {
            window.location.hash = '#dashboard/overview';
        });
    }

    // ---- Profile & Settings Dropdown Links ----
    const dropdownProfile = document.getElementById('dropdown-profile');
    const dropdownSettings = document.getElementById('dropdown-settings');

    if (dropdownProfile) {
        dropdownProfile.addEventListener('click', (e) => {
            e.preventDefault();
            accountDropdown.classList.remove('active');
            window.location.hash = '#profile';
        });
    }
    if (dropdownSettings) {
        dropdownSettings.addEventListener('click', (e) => {
            e.preventDefault();
            accountDropdown.classList.remove('active');
            window.location.hash = '#settings';
        });
    }

    // ---- Smart Back Navigation State ----
    let lastValidMainPage = '#dashboard/overview';
    const sidebarOrder = ['overview', 'expenses', 'goals', 'investments'];
    const smartBackBtn = document.getElementById('smart-back-btn');

    if (smartBackBtn) {
        smartBackBtn.addEventListener('click', () => {
            const currentHash = window.location.hash;
            
            // Case 4: Profile / Settings fallback to previous main page
            if (currentHash === '#profile' || currentHash === '#settings') {
                window.location.hash = lastValidMainPage;
                return;
            }
            
            // Case 1 & 3: Sidebar Navigation 
            if (currentHash.startsWith('#dashboard/')) {
                const currentTab = currentHash.split('/')[1] || 'overview';
                const currentIndex = sidebarOrder.indexOf(currentTab);
                
                if (currentIndex > 0) {
                    // Go to previous sidebar item
                    window.location.hash = `#dashboard/${sidebarOrder[currentIndex - 1]}`;
                } else {
                    // Fallback to previous logical flow step to prevent history loops
                    window.location.hash = '#input';
                }
            } else if (currentHash === '#input') {
                // If exiting the primary app flow, go home
                window.location.hash = '#home';
            } else {
                // Default fallback
                window.history.back();
            }
        });
    }

    function updateSmartBackButton(hash) {
        if (!smartBackBtn) return;
        
        // Hide button on main un-authenticated / landing pages
        if (['', '#home', '#login', '#signup'].includes(hash)) {
            smartBackBtn.classList.add('hidden');
            return;
        }

        smartBackBtn.classList.remove('hidden');

        // Track last valid main page continuously
        if (hash.startsWith('#dashboard/') || hash === '#input') {
            lastValidMainPage = hash;
        }
    }

    // ---- Profile Logic ----
    function loadUserProfile() {
        const saved = JSON.parse(localStorage.getItem('userProfile') || '{}');
        const name = localStorage.getItem('userName') || '';
        const email = localStorage.getItem('userEmail') || '';

        document.getElementById('prof-name').value = saved.name || name;
        document.getElementById('prof-email').value = saved.email || email;
        document.getElementById('prof-job').value = saved.job || '';
        document.getElementById('prof-age').value = saved.age || '';
        document.getElementById('prof-bio').value = saved.bio || '';
        document.getElementById('prof-dependents').value = saved.dependents || '';
        if (saved.empType) document.getElementById('prof-empType').value = saved.empType;
        if (saved.stability) document.getElementById('prof-stability').value = saved.stability;

        // Ensure read-only state on load
        setProfileReadonly(true);
    }

    function setProfileReadonly(readonly) {
        const fields = ['prof-name', 'prof-email', 'prof-job', 'prof-age', 'prof-bio', 'prof-dependents'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            el.readOnly = readonly;
            el.classList.toggle('readonly-input', readonly);
        });
        const selects = ['prof-empType', 'prof-stability'];
        selects.forEach(id => {
            const el = document.getElementById(id);
            el.disabled = readonly;
            el.classList.toggle('readonly-input', readonly);
        });

        const editBtn = document.getElementById('prof-edit-btn');
        const saveBtn = document.getElementById('prof-save-btn');
        if (readonly) {
            editBtn.classList.remove('hidden');
            saveBtn.classList.add('hidden');
        } else {
            editBtn.classList.add('hidden');
            saveBtn.classList.remove('hidden');
        }
    }

    const profEditBtn = document.getElementById('prof-edit-btn');
    const profSaveBtn = document.getElementById('prof-save-btn');

    if (profEditBtn) {
        profEditBtn.addEventListener('click', () => setProfileReadonly(false));
    }

    if (profSaveBtn) {
        profSaveBtn.addEventListener('click', () => {
            // Validate
            const age = document.getElementById('prof-age').value;
            const email = document.getElementById('prof-email').value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (age && (isNaN(age) || age < 10 || age > 120)) {
                alert('Please enter a valid age (10–120).');
                return;
            }
            if (email && !emailRegex.test(email)) {
                alert('Please enter a valid email address.');
                return;
            }

            const profile = {
                name: document.getElementById('prof-name').value,
                email: document.getElementById('prof-email').value,
                job: document.getElementById('prof-job').value,
                age: document.getElementById('prof-age').value,
                bio: document.getElementById('prof-bio').value,
                dependents: document.getElementById('prof-dependents').value,
                empType: document.getElementById('prof-empType').value,
                stability: document.getElementById('prof-stability').value,
            };
            localStorage.setItem('userProfile', JSON.stringify(profile));
            if (profile.name) localStorage.setItem('userName', profile.name);
            if (profile.email) localStorage.setItem('userEmail', profile.email);

            updateAccountBar();
            setProfileReadonly(true);
            addNotification('Profile updated successfully! ✅');
        });
    }

    // ---- Settings Logic ----
    function loadUserSettings() {
        const saved = JSON.parse(localStorage.getItem('userSettings') || '{}');
        if (saved.pubVis !== undefined) document.getElementById('set-pub-vis').checked = saved.pubVis;
        if (saved.saveData !== undefined) document.getElementById('set-save-data').checked = saved.saveData;
        if (saved.currency) document.getElementById('set-currency').value = saved.currency;
    }

    function saveSettings() {
        const settings = {
            pubVis: document.getElementById('set-pub-vis').checked,
            saveData: document.getElementById('set-save-data').checked,
            currency: document.getElementById('set-currency').value,
        };
        localStorage.setItem('userSettings', JSON.stringify(settings));
    }

    // Auto-save settings on any change
    ['set-pub-vis', 'set-save-data', 'set-currency'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', saveSettings);
    });

    // Security update button
    const setSecBtn = document.getElementById('set-sec-btn');
    if (setSecBtn) {
        setSecBtn.addEventListener('click', () => {
            const curr = document.getElementById('set-pass-curr').value;
            const newPass = document.getElementById('set-pass').value;
            const confirm = document.getElementById('set-pass-confirm').value;
            const newEmail = document.getElementById('set-email').value;

            if (!curr) { alert('Please enter your current password to make changes.'); return; }
            if (newPass && newPass !== confirm) { alert('New passwords do not match.'); return; }
            if (newPass && newPass.length < 6) { alert('Password must be at least 6 characters.'); return; }

            // Simulated save — would call backend in production
            if (newEmail) localStorage.setItem('userEmail', newEmail);
            addNotification('Security settings updated successfully! 🔐');
            document.getElementById('set-pass-curr').value = '';
            document.getElementById('set-pass').value = '';
            document.getElementById('set-pass-confirm').value = '';
        });
    }

    // ---- Auth Logic ----
    showSignupBtn.addEventListener('click', () => { window.location.hash = '#signup'; });
    showLoginBtn.addEventListener('click', () => { window.location.hash = '#login'; });
    showOrgSignupBtn.addEventListener('click', () => { window.location.hash = '#org-signup'; });
    showOrgLoginBtn.addEventListener('click', () => { window.location.hash = '#org-login'; });

    // Tab Switching
    function switchAuthTab(type) {
        if (type === 'individual') {
            tabIndividual.classList.add('active');
            tabOrganization.classList.remove('active');
            individualAuth.classList.remove('hidden');
            organizationAuth.classList.add('hidden');
        } else {
            tabOrganization.classList.add('active');
            tabIndividual.classList.remove('active');
            organizationAuth.classList.remove('hidden');
            individualAuth.classList.add('hidden');
        }
    }

    tabIndividual.addEventListener('click', () => {
        window.location.hash = '#login';
    });

    tabOrganization.addEventListener('click', () => {
        window.location.hash = '#org-login';
    });
    
    async function handleAuth(url, payload) {
        const endpoint = `${API_BASE}${url}`;
        console.log(`[Auth] Attempting ${url} →`, endpoint, 'Payload captured:', { ...payload, password: '***' });

        // Manual abort controller — AbortSignal.timeout() has limited support
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.warn('[Auth] ⏱️ Request timed out after 5s — aborting.');
            controller.abort();
        }, 5000);

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            console.log(`[Auth] Response received — HTTP status: ${response.status}`);
            let data;
            try {
                data = await response.json();
                console.log('[Auth] Response body parsed:', data);
            } catch (parseErr) {
                console.error('[Auth] ❌ Failed to parse JSON response:', parseErr);
                throw new Error('Invalid response from server.');
            }

            if (response.ok && data.success) {
                BACKEND_AVAILABLE = true;
                const isOrg = url === '/org_login' || url === '/org_signup';
                console.log('[Auth] ✅ Backend authentication successful. Org?', isOrg);
                localStorage.setItem('token', data.token);
                localStorage.setItem('userType', isOrg ? 'organization' : 'individual');
                if (isOrg) {
                    localStorage.setItem('orgName', payload.orgName || data.orgName || '');
                } else {
                    localStorage.setItem('userEmail', payload.identifier || payload.email || '');
                    if (data.name) localStorage.setItem('userName', data.name);
                }
                updateAccountBar();
                window.location.hash = isOrg ? '#org-dashboard' : '#input';
            } else {
                BACKEND_AVAILABLE = true;
                const msg = data.error || data.detail || 'Authentication failed.';
                console.warn('[Auth] ❌ Auth rejected by backend:', msg);
                showAuthError(msg);
            }

        } catch (err) {
            clearTimeout(timeoutId);
            // Network / connection error OR abort — backend likely down
            const isNetworkErr = err instanceof TypeError || err.name === 'AbortError';
            if (isNetworkErr) {
                BACKEND_AVAILABLE = false;
                console.warn('[Auth] ⚠️ Backend unreachable (error: ' + err.message + ') — switching to offline/mock mode.');

                // ---- Fallback: Mock Authentication via localStorage ----
                const isMockLogin = url === '/login';
                console.log(`[Auth] Running mock ${isMockLogin ? 'login' : 'signup'} for:`, payload.email);
                const mockResult = isMockLogin
                    ? mockLogin(payload.email, payload.password)
                    : mockSignup(payload.name, payload.email, payload.password);

                console.log('[Auth] Mock result:', { ...mockResult, token: mockResult.token ? '***' : undefined });

                if (mockResult.success) {
                    localStorage.setItem('token', mockResult.token);
                    localStorage.setItem('userEmail', payload.email);
                    if (mockResult.name) localStorage.setItem('userName', mockResult.name);

                    // Show non-blocking notice about offline mode
                    const offlineNotice = document.getElementById('offline-notice');
                    if (offlineNotice) {
                        offlineNotice.classList.remove('hidden');
                        setTimeout(() => offlineNotice.classList.add('hidden'), 8000);
                    }
                    console.log('[Auth] ✅ Mock auth successful — logged in offline. Redirecting to #input...');
                    updateAccountBar();
                    window.location.hash = '#input';
                } else {
                    console.error('[Auth] ❌ Mock auth failed:', mockResult.error);
                    showAuthError(mockResult.error || 'Offline authentication failed.');
                }
            } else {
                // Server gave an unexpected error (5xx, parse fail etc.)
                console.error('[Auth] ❌ Unexpected auth error:', err.name, err.message);
                showAuthError('Server error: ' + err.message);
            }
        }
    }

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const identifier = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const payload = { login_identifier: identifier, password };
        hideAuthError();
        handleAuth('/login', payload);
    });

    signupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = document.getElementById('signup-name').value.trim();
        const email = document.getElementById('signup-email').value.trim();
        const password = document.getElementById('signup-password').value;
        console.log('[SignupForm] Submit triggered. Name:', name, '| Email:', email, '| Password length:', password.length);
        if (!name || !email || !password) {
            showAuthError('Please fill in all fields.');
            return;
        }
        if (password.length < 6) {
            showAuthError('Password must be at least 6 characters.');
            return;
        }
        const payload = { name, email, password };
        hideAuthError();
        handleAuth('/signup', payload);
    });

    orgLoginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const orgName = document.getElementById('org-login-name').value.trim();
        const password = document.getElementById('org-login-password').value;
        const payload = { orgName, password };
        hideAuthError();
        handleAuth('/org_login', payload);
    });

    orgSignupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const orgName = document.getElementById('org-signup-name').value.trim();
        const password = document.getElementById('org-signup-password').value;
        const country = document.getElementById('org-signup-country').value.trim();
        const employees = parseInt(document.getElementById('org-signup-employees').value, 10);
        
        const payload = { 
            orgName, password, country, 
            numberOfEmployees: isNaN(employees) ? null : employees 
        };
        hideAuthError();
        handleAuth('/org_signup', payload);
    });
    
    function handleLogout() {
        console.log('[Auth] Logout triggered. Clearing session...');
        localStorage.removeItem('token');
        localStorage.removeItem('userName');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userType');
        localStorage.removeItem('orgName');
        window.appState = null;
        window.location.hash = '#home';
        
        // Clear forms
        if (loginForm) loginForm.reset();
        if (signupForm) signupForm.reset();
        if (advisorForm) advisorForm.reset();
        if (chatMessages) chatMessages.innerHTML = `
            <div class="chat-msg ai-msg">
                <p>Hello! I'm your AI Coach. Feel free to ask me anything about your analysis or how to improve your finances.</p>
            </div>
        `;
        console.log('[Auth] ✅ Logged out successfully.');
    }
    
    logoutBtn.addEventListener('click', handleLogout);
    sidebarLogoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        handleLogout();
    });
    dropdownLogout.addEventListener('click', (e) => {
        e.preventDefault();
        handleLogout();
    });

    // ---- Account Bar Logic ----
    function updateAccountBar() {
        const name = localStorage.getItem('userName') || 'User';
        userNameDisplay.innerText = name;
        userAvatar.innerText = name.charAt(0).toUpperCase();

        accountBar.classList.remove('hidden');
        renderNotifications();
    }

    function addNotification(message) {
        notifications.push({ id: Date.now(), text: message, read: false });
        renderNotifications();
    }

    function renderNotifications() {
        if (!notifBadge || !notifList) return;
        
        const unreadCount = notifications.filter(n => !n.read).length;
        if (unreadCount > 0) {
            notifBadge.classList.remove('hidden');
        } else {
            notifBadge.classList.add('hidden');
        }

        if (notifications.length === 0) {
            notifList.innerHTML = '<li class="empty-notif">No new notifications</li>';
            return;
        }

        notifList.innerHTML = '';
        // Insert most recent first
        [...notifications].reverse().forEach(n => {
            const li = document.createElement('li');
            li.innerText = n.text;
            if (!n.read) li.classList.add('unread');
            
            // Mark as read on click
            li.addEventListener('click', (e) => {
                e.stopPropagation(); // prevent dropdown from closing if inside dropdown
                n.read = true;
                renderNotifications();
            });
            notifList.appendChild(li);
        });
    }

    // Removed click behavior for accountProfileBtn because it is now CSS hover-based
    // Removed document click listener for accountDropdown closing because it is CSS hover-based

    // ---- Expense Categories Live Total ----
    const expInputs = document.querySelectorAll('.exp-input');
    const expTotalLive = document.getElementById('exp-total-live');
    function updateExpTotal() {
        let total = 0;
        expInputs.forEach(el => { total += parseFloat(el.value) || 0; });
        if (expTotalLive) expTotalLive.textContent = `Total: ${formatCurrency(total)}`;
    }
    expInputs.forEach(el => el.addEventListener('input', updateExpTotal));

    // ---- Multi-Goal Builder ----
    const addGoalBtn = document.getElementById('add-goal-btn');
    const goalsContainer = document.getElementById('goals-container');
    let goalCount = 1;

    // Bind existing goals
    document.querySelectorAll('.goal-entry').forEach(entry => {
        const selectEl = entry.querySelector('.goal-name-select');
        const customEl = entry.querySelector('.goal-name-custom');
        if (selectEl && customEl) {
            selectEl.addEventListener('change', () => {
                if (selectEl.value === 'Other') {
                    customEl.classList.remove('hidden');
                    customEl.setAttribute('required', 'true');
                } else {
                    customEl.classList.add('hidden');
                    customEl.removeAttribute('required');
                }
            });
        }
    });

    if (addGoalBtn) {
        addGoalBtn.addEventListener('click', () => {
            const idx = goalCount++;
            const div = document.createElement('div');
            div.className = 'goal-entry form-grid';
            div.dataset.index = idx;
            div.innerHTML = `
                <div class="input-group goal-name-group">
                    <label>Goal Name</label>
                    <select class="goal-name-select" required>
                        <option value="" disabled selected>Select a goal</option>
                        <option value="Buy a Car">🚗 Buy a Car</option>
                        <option value="Buy a House">🏠 Buy a House</option>
                        <option value="Travel / Vacation">✈️ Travel / Vacation</option>
                        <option value="Emergency Fund">🛡️ Emergency Fund</option>
                        <option value="Wedding">💍 Wedding</option>
                        <option value="Start a Business">🚀 Start a Business</option>
                        <option value="Retirement Planning">🏖️ Retirement Planning</option>
                        <option value="Gadget Purchase (Phone/Laptop)">💻 Gadget Purchase</option>
                        <option value="Other">✏️ Other (Enter manually)</option>
                    </select>
                    <input type="text" class="goal-name-custom hidden" placeholder="Enter custom goal" style="margin-top: 0.75rem;">
                </div>
                <div class="input-group">
                    <label>Target Amount</label>
                    <input type="text" class="goal-amount" placeholder="e.g., 5 Lakh">
                </div>
                <div class="input-group" style="position:relative;">
                    <label>Years to Achieve</label>
                    <input type="number" class="goal-years" placeholder="e.g., 3" step="0.1">
                    <button type="button" class="remove-goal-btn" title="Remove Goal">&times;</button>
                </div>
            `;
            div.querySelector('.remove-goal-btn').addEventListener('click', () => div.remove());
            
            const selectEl = div.querySelector('.goal-name-select');
            const customEl = div.querySelector('.goal-name-custom');
            selectEl.addEventListener('change', () => {
                if (selectEl.value === 'Other') {
                    customEl.classList.remove('hidden');
                    customEl.setAttribute('required', 'true');
                } else {
                    customEl.classList.add('hidden');
                    customEl.removeAttribute('required');
                }
            });

            goalsContainer.appendChild(div);
        });
    }

    // ---- Advisor Form Submit ----
    advisorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('token');

        // Collect expense categories
        const expCats = {
            rent:          parseFloat(document.getElementById('exp-rent').value)         || 0,
            food:          parseFloat(document.getElementById('exp-food').value)         || 0,
            subscriptions: parseFloat(document.getElementById('exp-subs').value)         || 0,
            outings:       parseFloat(document.getElementById('exp-outing').value)       || 0,
            transport:     parseFloat(document.getElementById('exp-transport').value)    || 0,
            car:           parseFloat(document.getElementById('exp-car').value)          || 0,
            children:      parseFloat(document.getElementById('exp-children').value)     || 0,
            other:         parseFloat(document.getElementById('exp-other').value)        || 0,
        };

        // Collect multiple goals
        const goalEntries = document.querySelectorAll('.goal-entry');
        const goals = [];
        goalEntries.forEach(entry => {
            let name = '';
            const selectEl = entry.querySelector('.goal-name-select');
            if (selectEl) {
                name = selectEl.value === 'Other' ? entry.querySelector('.goal-name-custom')?.value.trim() : selectEl.value;
            } else {
                name = entry.querySelector('.goal-name')?.value.trim();
            }
            
            const amount = entry.querySelector('.goal-amount')?.value.trim();
            const years  = entry.querySelector('.goal-years')?.value.trim();
            if (name && amount && years) goals.push({ name, amount, years });
        });

        const payload = {
            income:             document.getElementById('income').value,
            expense_categories: expCats,
            risk_appetite:      document.getElementById('risk').value,
            goals:              goals,
        };

        // Store categories on window for dashboard tab use
        window.expenseCategories = expCats;

        loader.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (response.status === 401) {
                handleLogout();
                alert("Session expired. Please login again.");
                return;
            }

            const data = await response.json();

            if (data.status === 'success') {
                window.appState = data;
                populateDashboard(data);
                window.location.hash = '#dashboard/overview';

                setTimeout(() => {
                    addNotification("AI Blueprint generated successfully!");
                    if (data.savings_improvement && data.savings_improvement.suggested_cut > 0) {
                        setTimeout(() => addNotification(data.savings_improvement.message), 1500);
                    }
                }, 1000);
            } else {
                alert('Error: ' + JSON.stringify(data));
            }
        } catch (err) {
            console.error(err);
            alert('Failed to connect to AI engine. Make sure the backend is running.');
        } finally {
            loader.classList.add('hidden');
        }
    });

    resetBtn.addEventListener('click', () => {
        window.location.hash = '#input';
    });

    // ---- Dashboard Formatting Helper ----
    const formatCurrency = (num) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(num);
    };

    function populateDashboard(data) {
        const { financials, category, emergency, savings_improvement, goal, goals, action_plan, investments, recommendations } = data;
        const inDeficit = financials.in_deficit || financials.savings <= 0;

        // 1. Overview
        document.getElementById('res-income').innerText = formatCurrency(financials.income);
        document.getElementById('res-expenses').innerText = formatCurrency(financials.expenses);

        const savingsEl = document.getElementById('res-savings');
        savingsEl.innerText = formatCurrency(financials.savings);
        if (inDeficit) {
            savingsEl.style.color = 'var(--danger)';
        } else {
            savingsEl.style.color = '';
        }

        const healthBadge = document.getElementById('res-health');
        if (inDeficit) {
            healthBadge.innerText = '⚠️ Health: Critical — Deficit';
            healthBadge.style.background = 'rgba(239, 68, 68, 0.08)';
            healthBadge.style.color = 'var(--danger)';
            healthBadge.style.border = '1px solid rgba(239,68,68,0.2)';
        } else if (financials.health === 'Good') {
            healthBadge.innerText = `Health: ${financials.health}`;
            healthBadge.style.background = 'rgba(16, 185, 129, 0.1)';
            healthBadge.style.color = 'var(--accent)';
            healthBadge.style.border = '1px solid rgba(16, 185, 129, 0.2)';
        } else {
            healthBadge.innerText = `Health: ${financials.health}`;
            healthBadge.style.background = 'rgba(239, 68, 68, 0.08)';
            healthBadge.style.color = 'var(--danger)';
            healthBadge.style.border = '1px solid rgba(239, 68, 68, 0.2)';
        }

        // Deficit Critical Warning Banner (overview section)
        let deficitWarning = document.getElementById('deficit-critical-banner');
        if (inDeficit) {
            if (!deficitWarning) {
                deficitWarning = document.createElement('div');
                deficitWarning.id = 'deficit-critical-banner';
                deficitWarning.className = 'deficit-critical-banner';
                const overviewSection = document.getElementById('sec-overview');
                overviewSection.insertBefore(deficitWarning, overviewSection.firstChild);
            }
            const deficit = Math.abs(financials.savings);
            deficitWarning.innerHTML = `
                <div class="deficit-banner-icon">🚨</div>
                <div class="deficit-banner-body">
                    <strong>CRITICAL: You are running a monthly deficit of ${formatCurrency(deficit)}</strong>
                    <p>Your expenses exceed your income. Financial goals are currently not achievable. Immediate expense reduction required.</p>
                </div>
            `;
        } else if (deficitWarning) {
            deficitWarning.remove();
        }

        // 2. ML Category
        document.getElementById('ml-category').innerText = category;
        document.getElementById('res-savings-rate').innerText = `${financials.savings_rate_percent}%`;

        // 3. Emergency Fund
        document.getElementById('res-emergency-target').innerText = formatCurrency(emergency.target_amount);
        document.getElementById('res-emergency-msg').innerText = emergency.message;
        const eStatus = document.getElementById('res-emergency-status');
        eStatus.innerText = emergency.status;
        if (emergency.status === 'Adequate') {
            eStatus.style.background = 'rgba(16, 185, 129, 0.1)';
            eStatus.style.color = 'var(--accent)';
        } else {
            eStatus.style.background = 'rgba(245, 158, 11, 0.1)';
            eStatus.style.color = 'var(--warning)';
        }

        // 4. Savings Improvement Banner — suppress if in deficit (use deficit banner instead)
        if (savings_improvement.suggested_cut > 0 && !inDeficit) {
            document.getElementById('improvement-banner').classList.remove('hidden');
            document.getElementById('res-improvement-msg').innerText = savings_improvement.message;
        } else {
            document.getElementById('improvement-banner').classList.add('hidden');
        }

        // 5. Action Plan
        const actionList = document.getElementById('action-plan-list');
        actionList.innerHTML = '';
        if (action_plan) {
            action_plan.forEach(step => {
                const li = document.createElement('li');
                li.innerText = step;
                actionList.appendChild(li);
            });
        }

        // 6. Investments Table
        const invTbody = document.getElementById('investments-tbody');
        invTbody.innerHTML = '';
        if (investments) {
            investments.forEach(inv => {
                const tr = document.createElement('tr');
                const suitableHtml = inv.suitable
                    ? `<span class="suitable-badge">Yes</span>`
                    : `<span class="not-suitable-badge">No</span>`;
                tr.innerHTML = `
                    <td><strong>${inv.name}</strong></td>
                    <td>${inv.risk}</td>
                    <td>${inv.return}</td>
                    <td>${suitableHtml}</td>
                `;
                invTbody.appendChild(tr);
            });
        }

        // 7. Recommendations
        const recList = document.getElementById('recommendations-list');
        recList.innerHTML = '';
        recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.innerText = rec;
            recList.appendChild(li);
        });

        // 8. Multi-Goals Tab
        renderGoalsTab(goals || (goal ? [goal] : []));

        // 9. Expenses Tab
        const cats = financials.expense_categories || window.expenseCategories || {};
        renderExpensesTab(cats, financials);

        // 10. Budget Chart
        setupChart(financials);
    }

    // ---- Goals Tab Renderer ----
    function renderGoalsTab(goals) {
        const container = document.getElementById('goals-results-container');
        container.innerHTML = '';

        // Check global deficit state
        const inDeficit = window.appState && (window.appState.financials.in_deficit || window.appState.financials.savings <= 0);

        if (inDeficit) {
            container.innerHTML = `
                <div class="glass-panel goal-deficit-block" style="grid-column:1/-1;">
                    <div class="goal-deficit-icon">🚨</div>
                    <h3 style="color:var(--danger);margin-bottom:0.5rem;">Goals Not Achievable</h3>
                    <p style="color:var(--text-muted);line-height:1.7;">
                        Your expenses exceed your income. Financial goals cannot be calculated or achieved in a deficit state.<br>
                        <strong style="color:#b91c1c;">Resolve your monthly deficit first before planning for any financial goal.</strong>
                    </p>
                </div>
            `;
            // Still show goal cards below but in blocked state
            if (goals && goals.length > 0) {
                goals.forEach(g => {
                    const card = document.createElement('div');
                    card.className = 'glass-panel dash-card goal-card goal-card-blocked';
                    card.innerHTML = `
                        <h3>🎯 ${g.name || 'Goal'}</h3>
                        <div class="goal-amount-display" style="color:var(--text-muted);">${formatCurrency(g.goal_amount)}</div>
                        <p class="goal-message" style="color:var(--danger);">Goal not achievable with current financial state</p>
                        <div class="required-sip blocked-sip">
                            <span>Required SIP:</span>
                            <h4 style="color:var(--text-muted);">N/A — Deficit Active</h4>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
            return;
        }

        if (!goals || goals.length === 0) {
            container.innerHTML = '<div class="glass-panel" style="text-align:center;padding:3rem;"><p style="color:var(--text-muted);">No goals submitted.</p></div>';
            return;
        }
        goals.forEach(g => {
            const card = document.createElement('div');
            card.className = 'glass-panel dash-card goal-card';
            const blocked = g.blocked_by_deficit;
            const feasibleColor = blocked ? 'var(--danger)' : (g.feasible ? 'var(--accent)' : 'var(--warning)');
            const sipDisplay = blocked
                ? `<h4 style="color:var(--text-muted);">N/A</h4>`
                : `${formatCurrency(g.monthly_required)} <small>/ mo</small>`;
            card.innerHTML = `
                <h3>🎯 ${g.name || 'Goal'}</h3>
                <div class="goal-amount-display">${formatCurrency(g.goal_amount)}</div>
                <p class="goal-message" style="color:${feasibleColor};">${g.message}</p>
                <div class="required-sip ${blocked ? 'blocked-sip' : ''}">
                    <span>Required SIP:</span>
                    <h4 ${blocked ? '' : 'style="color:var(--accent);font-size:1.5rem;"'}>${sipDisplay}</h4>
                </div>
            `;
            container.appendChild(card);
        });
    }

    // ---- Expenses Tab Renderer ----
    let expenseChartInstance = null;
    function renderExpensesTab(cats, financials) {
        const labels = Object.keys(cats).filter(k => cats[k] > 0);
        const values = labels.map(k => cats[k]);
        const total = values.reduce((a, b) => a + b, 0);
        const income = financials.income;
        const savings = financials.savings;

        // --- Alerts ---
        const alertsContainer = document.getElementById('exp-alerts-container');
        alertsContainer.innerHTML = '';
        const alerts = [];
        const inDeficit = savings <= 0;

        // Critical deficit alert — highest priority
        if (inDeficit) {
            alerts.push({
                msg: `🚨 <strong>CRITICAL DEFICIT:</strong> You are running a monthly deficit of ${formatCurrency(Math.abs(savings))}. You are spending more than you earn. Immediate expense reduction is required.`,
                type: 'critical'
            });
        } else if (total > income * 0.70) {
            alerts.push({ msg: `⚠️ Your expenses (${formatCurrency(total)}) exceed 70% of your income. This is a financial red flag!`, type: 'danger' });
        }

        if (!inDeficit && savings < income * 0.20) {
            alerts.push({ msg: `💡 Savings rate is below the recommended 20% threshold. Aim to save at least ${formatCurrency(income * 0.20)} per month.`, type: 'warning' });
        }

        // Highlight any category that is >40% of total expenses
        labels.forEach(k => {
            if (total > 0 && cats[k] / total > 0.40) {
                alerts.push({ msg: `🔴 <strong>Overspending:</strong> "${k}" accounts for ${Math.round(cats[k]/total*100)}% of your total expenses — this category is significantly above the healthy threshold.`, type: 'warning' });
            }
        });

        alerts.forEach(a => {
            const div = document.createElement('div');
            div.className = `glass-panel expense-alert expense-alert-${a.type}`;
            div.innerHTML = `<p>${a.msg}</p>`;
            alertsContainer.appendChild(div);
        });

        // --- Pie Chart ---
        const ctx = document.getElementById('expenseChart').getContext('2d');
        if (expenseChartInstance) expenseChartInstance.destroy();
        const palette = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4','#84cc16'];
        if (labels.length > 0) {
            expenseChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{ data: values, backgroundColor: palette.slice(0, labels.length), borderColor: '#ffffff', borderWidth: 2, hoverOffset: 6 }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#334155', padding: 16, font: { size: 12 } } } } }
            });
        } else {
            ctx.canvas.parentElement.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem;">No expense data entered.</p>';
        }

        // --- Insights ---
        const insightsList = document.getElementById('exp-insights-list');
        insightsList.innerHTML = '';
        const sorted = [...labels].sort((a, b) => cats[b] - cats[a]);
        sorted.forEach((k, i) => {
            const pct = total > 0 ? Math.round(cats[k] / total * 100) : 0;
            const bar = document.createElement('div');
            bar.className = 'insight-row';
            bar.innerHTML = `
                <div class="insight-label">${i === 0 ? '🔴' : '🟡'} ${k}</div>
                <div class="insight-bar-wrap"><div class="insight-bar" style="width:${pct}%; background:${palette[i % palette.length]};"></div></div>
                <div class="insight-pct">${pct}% &bull; ${formatCurrency(cats[k])}</div>
            `;
            insightsList.appendChild(bar);
        });
        if (sorted.length === 0) insightsList.innerHTML = '<p style="color:var(--text-muted);">No category data.</p>';

        // --- Trend Simulation ---
        const trendEl = document.getElementById('exp-trend-content');
        const inflationRate = 0.06; // 6% annual inflation
        const next1 = total * (1 + inflationRate);
        const next3 = total * Math.pow(1 + inflationRate, 3);
        const next5 = total * Math.pow(1 + inflationRate, 5);
        trendEl.innerHTML = `
            <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:0.75rem;">Simulated at 6% annual inflation:</p>
            <div class="stat"><span class="label">Today</span><span class="value">${formatCurrency(total)}</span></div>
            <div class="stat"><span class="label">After 1 Year</span><span class="value" style="color:var(--warning);">${formatCurrency(next1)}</span></div>
            <div class="stat"><span class="label">After 3 Years</span><span class="value" style="color:var(--warning);">${formatCurrency(next3)}</span></div>
            <div class="stat"><span class="label">After 5 Years</span><span class="value" style="color:var(--danger);">${formatCurrency(next5)}</span></div>
        `;

        // --- Advisory ---
        const advList = document.getElementById('exp-advisory-list');
        advList.innerHTML = '<p style="color:var(--text-muted);font-size:0.8rem;margin-bottom:0.5rem;">Personalized Tips:</p>';
        const tips = [];
        if (cats['Food & Groceries'] && cats['Food & Groceries'] / income > 0.30) tips.push('Your food spending exceeds the recommended 30% of income. Try meal planning.');
        if (cats['Subscriptions'] && cats['Subscriptions'] > 1500) tips.push('You spend heavily on subscriptions. Audit and cancel unused ones.');
        if (cats['Outings/Entertainment'] && cats['Outings/Entertainment'] / total > 0.15) tips.push('Entertainment is >15% of expenses. Set a monthly outing budget.');
        if (cats['House Rent'] && cats['House Rent'] / income > 0.40) tips.push('Your rent exceeds 40% of income. Consider a more affordable option.');
        if (tips.length === 0) tips.push('Your spending structure looks balanced. Keep it up!');
        tips.forEach(t => {
            const p = document.createElement('p');
            p.className = 'advisory-tip';
            p.textContent = `• ${t}`;
            advList.appendChild(p);
        });

        // --- Expense Trend Line Chart ---
        const trendCanvas = document.getElementById('expenseTrendChart');
        if (trendCanvas) {
            if (window._expenseTrendChartInstance) {
                window._expenseTrendChartInstance.destroy();
            }
            const trendCtx = trendCanvas.getContext('2d');
            const trendLabels = ['Today', 'After 1 Year', 'After 3 Years', 'After 5 Years'];
            const trendValues = [total, next1, next3, next5];
            window._expenseTrendChartInstance = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: trendLabels,
                    datasets: [{
                        label: 'Projected Monthly Expenses',
                        data: trendValues,
                        borderColor: 'rgba(59, 130, 246, 0.9)',
                        backgroundColor: 'rgba(59, 130, 246, 0.08)',
                        pointBackgroundColor: ['#10b981', '#f59e0b', '#f59e0b', '#ef4444'],
                        pointBorderColor: '#ffffff',
                        pointRadius: 7,
                        pointHoverRadius: 10,
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2.5,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: ctx => ' ' + formatCurrency(ctx.parsed.y)
                            },
                            backgroundColor: '#ffffff',
                            titleColor: '#0f172a',
                            bodyColor: '#475569',
                            borderColor: 'rgba(30, 58, 138, 0.1)',
                            borderWidth: 1,
                            padding: 10,
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(30, 58, 138, 0.05)' },
                            ticks: { color: '#475569', font: { size: 12 } }
                        },
                        y: {
                            grid: { color: 'rgba(30, 58, 138, 0.05)' },
                            ticks: {
                                color: '#475569',
                                font: { size: 11 },
                                callback: val => '₹' + (val >= 100000 ? (val/100000).toFixed(1) + 'L' : (val/1000).toFixed(0) + 'K')
                            },
                            beginAtZero: false,
                        }
                    }
                }
            });
        }
    }

    function setupChart(financials) {
        const ctx = document.getElementById('budgetChart').getContext('2d');
        
        if(budgetChartInstance) {
            budgetChartInstance.destroy();
        }

        const actualNeedsWants = financials.expenses;
        const actualSavings = financials.savings > 0 ? financials.savings : 0;
        
        budgetChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Actual Expenses', 'Actual Savings'],
                datasets: [{
                    label: 'Actual Pattern',
                    data: [actualNeedsWants, actualSavings],
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)', // Red/Expenses
                        'rgba(16, 185, 129, 0.8)' // Green/Savings
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#334155' }
                    }
                }
            }
        });
    }

    // ---- Chat Logic ----
    chatToggle.addEventListener('click', () => {
        chatWindow.classList.toggle('hidden');
    });
    chatClose.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
    });

    const appendMessage = (text, sender) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${sender === 'user' ? 'user-msg' : 'ai-msg'}`;
        const formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        msgDiv.innerHTML = `<p>${formatted}</p>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    };

    const showTyping = () => {
        const bubble = document.createElement('div');
        bubble.className = 'chat-msg ai-msg typing-bubble';
        bubble.id = 'typing-indicator';
        bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const removeTyping = () => {
        const t = document.getElementById('typing-indicator');
        if (t) t.remove();
    };

    const handleChatSend = async () => {
        const text = chatInput.value.trim();
        if(!text) return;
        
        appendMessage(text, 'user');
        chatInput.value = '';
        chatSend.disabled = true;
        showTyping();
        
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            removeTyping();
            if (data.status === 'success') {
                appendMessage(data.reply, 'ai');
            } else {
                appendMessage('Oops, I had trouble processing that.', 'ai');
            }
        } catch (err) {
            console.error(err);
            removeTyping();
            appendMessage('AI service temporarily unavailable. Please try again.', 'ai');
        } finally {
            chatSend.disabled = false;
        }
    };

    chatSend.addEventListener('click', handleChatSend);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleChatSend();
        }
    });


    // ---- Landing Page Interactions ----
    if (navAuthBtn) {
        navAuthBtn.addEventListener('click', () => {
            window.location.hash = '#login';
        });
    }

    const heroCta = document.getElementById('hero-cta-btn');
    if (heroCta) {
        heroCta.addEventListener('click', () => {
            window.location.hash = '#login';
        });
    }

    // Smooth Scroll for landing page links
    document.querySelectorAll('.landing-navbar a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetEl = document.querySelector(targetId);
            if (targetEl) {
                targetEl.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    //    // ---- Organization Forms & Dashboard ----

    const secOrgInput = document.getElementById('sec-org-input');
    const secOrgDashboard = document.getElementById('sec-org-dashboard');
    const orgCsvForm = document.getElementById('org-csv-upload-form');
    const orgManualForm = document.getElementById('org-manual-form');
    const orgLogoutBtn = document.getElementById('org-logout-btn');
    const resetAnalysisBtn = document.getElementById('reset-analysis-btn');

    if (orgLogoutBtn) orgLogoutBtn.addEventListener('click', handleLogout);

    if (orgCsvForm) {
        orgCsvForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('org-csv-file');
            if(!fileInput.files.length) return alert('Select a file.');
            const file = fileInput.files[0];
            const reader = new FileReader();
            reader.onload = async function(evt) {
                const b64 = evt.target.result.split(',')[1];
                const token = localStorage.getItem('token');
                const res = await fetch(`${API_BASE}/org/upload_csv`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: file.name, file_base64: b64, type: 'text/csv' })
                });
                if(res.ok) { alert('Uploaded!'); loadOrgDashboard(); }
                else { const err = await res.json(); alert('Failed: ' + err.detail); }
            };
            reader.readAsDataURL(file);
        });
    }

    if (orgManualForm) {
        orgManualForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                revenue: parseFloat(document.getElementById('org-man-rev').value),
                total_cost: parseFloat(document.getElementById('org-man-cost').value),
                profit: parseFloat(document.getElementById('org-man-profit').value),
                growth_rate: parseFloat(document.getElementById('org-man-growth').value || 0),
            };
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE}/org/input_manual`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if(res.ok) loadOrgDashboard();
            else { const err = await res.json(); alert('Failed: ' + err.detail); }
        });
    }

    if (resetAnalysisBtn) {
        resetAnalysisBtn.addEventListener('click', async () => {
            if(!confirm('Are you sure you want to permanently delete all organization data?')) return;
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE}/org/reset_analysis`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if(res.ok) {
                alert('Analysis reset!');
                loadOrgDashboard();
            }
        });
    }

    // Toggle sub-tabs
    document.querySelectorAll('.org-sub-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.org-sub-tab').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.org-tab-content').forEach(c => c.classList.add('hidden'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.remove('hidden');
        });
    });

    // We export or define loadOrgDashboard here
    window.loadOrgDashboard = async function() {
        secOrgInput.classList.add('hidden');
        secOrgDashboard.classList.add('hidden');
        dashboardContainer.classList.add('hidden');
        
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(`${API_BASE}/org/dashboard`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if(!data.data && data.message === "No data provided yet") {
                secOrgInput.classList.remove('hidden');
            } else {
                secOrgDashboard.classList.remove('hidden');
                // Basic binding for brevity (could be expanded)
                if(data.data) {
                    const d = data.data;
                    document.getElementById('org-total-rev').innerText = '$' + (d.total_revenue_avg || 0).toLocaleString();
                    document.getElementById('org-total-exp').innerText = '$' + (d.total_cost_avg || 0).toLocaleString();
                    document.getElementById('org-profit').innerText = '$' + (d.total_profit_avg || 0).toLocaleString();
                    document.getElementById('org-record-count').innerText = d.records_count || 1;
                    
                    const health = typeof d.predicted_health_score === 'number' ? Math.round(d.predicted_health_score) : 50;
                    document.getElementById('org-avg-health').innerText = health + '/100';
                    document.getElementById('org-health-circle').innerText = health;
                    document.getElementById('org-health-badge').innerText = 'Health: ' + health;
                    document.getElementById('org-health-badge').classList.remove('hidden');
                }
            }
        } catch (e) {
            console.error('Error fetching org dash', e);
        }
    };
    
    init();
});
