const API_BASE = 'http://localhost:8000/api';

document.addEventListener('DOMContentLoaded', () => {
    // ---- DOM Elements ----
    
    // Sections
    const authSection = document.getElementById('auth-section');
    const inputSection = document.getElementById('input-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const loader = document.getElementById('loader');
    
    // Auth
    const loginContainer = document.getElementById('login-container');
    const signupContainer = document.getElementById('signup-container');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const showSignupBtn = document.getElementById('show-signup');
    const showLoginBtn = document.getElementById('show-login');
    const logoutBtn = document.getElementById('logout-btn');
    const dashboardLogoutBtn = document.getElementById('dashboard-logout-btn');
    
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

    let budgetChartInstance = null;
    
    // ---- Initialize ----
    function init() {
        const token = localStorage.getItem('token');
        if (token) {
            showInputScreen();
        } else {
            showAuthScreen();
        }
    }
    
    // ---- Navigation Helpers ----
    function showAuthScreen() {
        authSection.classList.remove('hidden');
        inputSection.classList.add('hidden');
        dashboardSection.classList.add('hidden');
        chatWidget.classList.add('hidden');
    }
    
    function showInputScreen() {
        authSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
        dashboardSection.classList.add('hidden');
        chatWidget.classList.add('hidden');
    }
    
    function showDashboardScreen() {
        inputSection.classList.add('hidden');
        dashboardSection.classList.remove('hidden');
        chatWidget.classList.remove('hidden');
    }

    // ---- Auth Logic ----
    showSignupBtn.addEventListener('click', () => {
        loginContainer.classList.add('hidden');
        signupContainer.classList.remove('hidden');
    });

    showLoginBtn.addEventListener('click', () => {
        signupContainer.classList.add('hidden');
        loginContainer.classList.remove('hidden');
    });
    
    async function handleAuth(url, payload) {
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok && data.success) {
                localStorage.setItem('token', data.token);
                showInputScreen();
            } else {
                alert(data.error || 'Authentication failed');
            }
        } catch (err) {
            console.error(err);
            alert('Failed to connect to server.');
        }
    }

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const payload = {
            email: document.getElementById('login-email').value,
            password: document.getElementById('login-password').value
        };
        handleAuth('/login', payload);
    });

    signupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('signup-name').value,
            email: document.getElementById('signup-email').value,
            password: document.getElementById('signup-password').value
        };
        handleAuth('/signup', payload);
    });
    
    function handleLogout() {
        localStorage.removeItem('token');
        showAuthScreen();
        // Clear forms
        loginForm.reset();
        signupForm.reset();
        advisorForm.reset();
        chatMessages.innerHTML = `
            <div class="chat-msg ai-msg">
                <p>Hello! I'm your AI Coach. Feel free to ask me anything about your analysis or how to improve your finances.</p>
            </div>
        `;
    }
    
    logoutBtn.addEventListener('click', handleLogout);
    dashboardLogoutBtn.addEventListener('click', handleLogout);

    // ---- Advisor Logic ----
    advisorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('token');
        
        const payload = {
            income: document.getElementById('income').value,
            expenses: document.getElementById('expenses').value,
            risk_appetite: document.getElementById('risk').value,
            goal_name: document.getElementById('goal-name').value,
            goal_amount: document.getElementById('goal-amount').value,
            goal_years: document.getElementById('goal-years').value
        };

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
                populateDashboard(data, payload.goal_name);
                showDashboardScreen();
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
        showInputScreen();
    });

    // ---- Dashboard Formatting Helper ----
    const formatCurrency = (num) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(num);
    };

    function populateDashboard(data, goalName) {
        const { financials, category, emergency, savings_improvement, goal, action_plan, investments, recommendations } = data;

        // 1. Overview
        document.getElementById('res-income').innerText = formatCurrency(financials.income);
        document.getElementById('res-expenses').innerText = formatCurrency(financials.expenses);
        document.getElementById('res-savings').innerText = formatCurrency(financials.savings);
        
        const healthBadge = document.getElementById('res-health');
        healthBadge.innerText = `Health: ${financials.health}`;
        if(financials.health === 'Good') {
            healthBadge.style.background = 'rgba(16, 185, 129, 0.2)';
            healthBadge.style.color = 'var(--accent)';
        } else {
            healthBadge.style.background = 'rgba(239, 68, 68, 0.2)';
            healthBadge.style.color = 'var(--danger)';
        }

        // 2. ML Category
        document.getElementById('ml-category').innerText = category;
        document.getElementById('res-savings-rate').innerText = `${financials.savings_rate_percent}%`;

        // 3. Goal
        document.getElementById('res-goal-name').innerText = `Goal: ${goalName}`;
        document.getElementById('res-goal-amount').innerText = formatCurrency(goal.goal_amount);
        document.getElementById('res-goal-message').innerText = goal.message;
        document.getElementById('res-goal-monthly').innerHTML = `${formatCurrency(goal.monthly_required)} <small>/ mo</small>`;

        // 4. Emergency Fund
        document.getElementById('res-emergency-target').innerText = formatCurrency(emergency.target_amount);
        document.getElementById('res-emergency-msg').innerText = emergency.message;
        const eStatus = document.getElementById('res-emergency-status');
        eStatus.innerText = emergency.status;
        if(emergency.status === 'Adequate') {
            eStatus.style.background = 'rgba(16, 185, 129, 0.2)';
            eStatus.style.color = 'var(--accent)';
        } else {
            eStatus.style.background = 'rgba(245, 158, 11, 0.2)';
            eStatus.style.color = 'var(--warning)';
        }

        // 5. Savings Improvement (Banner)
        if(savings_improvement.suggested_cut > 0) {
            document.getElementById('improvement-banner').classList.remove('hidden');
            document.getElementById('res-improvement-msg').innerText = savings_improvement.message;
        } else {
            document.getElementById('improvement-banner').classList.add('hidden');
        }

        // 6. Action Plan
        const actionList = document.getElementById('action-plan-list');
        actionList.innerHTML = '';
        if(action_plan) {
            action_plan.forEach(step => {
                const li = document.createElement('li');
                li.innerText = step;
                actionList.appendChild(li);
            });
        }

        // 7. Investments Table
        const invTbody = document.getElementById('investments-tbody');
        invTbody.innerHTML = '';
        if(investments) {
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

        // 8. Recommendations
        const recList = document.getElementById('recommendations-list');
        recList.innerHTML = '';
        recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.innerText = rec;
            recList.appendChild(li);
        });

        // Setup Chart
        setupChart(financials);
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
                    borderColor: 'rgba(30, 41, 59, 1)',
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
                        labels: { color: '#f8fafc' }
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
        msgDiv.innerHTML = `<p>${text}</p>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const handleChatSend = async () => {
        const text = chatInput.value.trim();
        if(!text) return;
        
        appendMessage(text, 'user');
        chatInput.value = '';
        
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
            if (data.status === 'success') {
                appendMessage(data.reply, 'ai');
            } else {
                appendMessage('Oops, I had trouble processing that.', 'ai');
            }
        } catch (err) {
            console.error(err);
            appendMessage('Network error communicating with AI server.', 'ai');
        }
    };

    chatSend.addEventListener('click', handleChatSend);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleChatSend();
        }
    });

    // Boot
    init();
});
