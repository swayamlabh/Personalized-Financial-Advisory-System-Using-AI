document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('advisor-form');
    const inputSection = document.getElementById('input-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const loader = document.getElementById('loader');
    const resetBtn = document.getElementById('reset-btn');
    let budgetChartInstance = null;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            income: document.getElementById('income').value,
            expenses: document.getElementById('expenses').value,
            risk_appetite: document.getElementById('risk').value,
            goal_name: document.getElementById('goal-name').value,
            goal_amount: document.getElementById('goal-amount').value,
            goal_years: document.getElementById('goal-years').value
        };

        // Show Loader
        loader.classList.remove('hidden');

        try {
            const response = await fetch('http://localhost:8000/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                populateDashboard(data, payload.goal_name);
                
                // Transition UI
                inputSection.classList.add('hidden');
                dashboardSection.classList.remove('hidden');
            } else {
                alert('Error: ' + JSON.stringify(data));
            }
        } catch (err) {
            console.error(err);
            alert('Failed to connect to AI engine. Make sure the backend is running on localhost:8000.');
        } finally {
            loader.classList.add('hidden');
        }
    });

    resetBtn.addEventListener('click', () => {
        dashboardSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
        // Reset inputs optionally
        // form.reset();
    });

    const formatCurrency = (num) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(num);
    };

    function populateDashboard(data, goalName) {
        const { financials, category, goal, recommendations } = data;

        // Overview
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

        // ML Category
        document.getElementById('ml-category').innerText = category;
        document.getElementById('res-savings-rate').innerText = `${financials.savings_rate_percent}%`;

        // Goal
        document.getElementById('res-goal-name').innerText = `Goal: ${goalName}`;
        document.getElementById('res-goal-amount').innerText = formatCurrency(goal.goal_amount);
        document.getElementById('res-goal-message').innerText = goal.message;
        document.getElementById('res-goal-monthly').innerHTML = `${formatCurrency(goal.monthly_required)} <small>/ mo</small>`;

        // Recommendations
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

        // Actual breakdown
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
});
