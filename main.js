// --- DOM Elements ---
const authContainer = document.getElementById('auth-container');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const appContent = document.getElementById('app-content');
const messageBox = document.getElementById('message-box');
const welcomeMessage = document.getElementById('welcome-message');
const tabs = {
    login: document.getElementById('tab-login'),
    register: document.getElementById('tab-register')
};
const transactionForm = document.getElementById('transaction-form');
const categorySelect = document.getElementById('trans-category');
const incomeTypeRadio = document.getElementById('type-income');
const categoryModal = document.getElementById('category-modal');
const newCategoryForm = document.getElementById('new-category-form');

// Summary Elements
const summaryButton = document.getElementById('summary-button');
const downloadButton = document.getElementById('download-button');
const dateRangeInputs = document.getElementById('date-range-inputs');
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const summaryModal = document.getElementById('summary-modal');
const summaryBalanceDisplay = document.getElementById('summary-balance');
const summaryCategoryDisplay = document.getElementById('summary-category-display');
const summaryDateDisplay = document.getElementById('summary-date-display');
const topIncomeList = document.getElementById('top-income-list');
const topExpenseList = document.getElementById('top-expense-list');
const balanceChartCanvas = document.getElementById('balanceChart');


// Global storage for ALL categories
let allCategories = []; 
let userRole = null;
let dailyBalanceChart = null; // Chart instance

// --- Utility Functions ---

function showMessage(type, content) {
    messageBox.textContent = content;
    messageBox.className = 'p-3 rounded-lg text-sm transition duration-300'; // Reset classes
    messageBox.style.display = 'block';

    if (type === 'success') {
        messageBox.classList.add('bg-green-100', 'text-green-800');
    } else if (type === 'error') {
        messageBox.classList.add('bg-red-100', 'text-red-800');
    } else { // info
        messageBox.classList.add('bg-blue-100', 'text-blue-800');
    }
}

function clearMessage() {
    messageBox.style.display = 'none';
}

function showForm(formId) {
    clearMessage();
    if (formId === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        tabs.login.classList.add('border-emerald-600', 'text-emerald-600');
        tabs.register.classList.remove('border-emerald-600', 'text-emerald-600');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        tabs.register.classList.add('border-emerald-600', 'text-emerald-600');
        tabs.login.classList.remove('border-emerald-600', 'text-emerald-600');
    }
}

// --- Category Management UI ---

function showCategoryModal() {
    categoryModal.classList.remove('hidden');
}

function hideCategoryModal() {
    categoryModal.classList.add('hidden');
    newCategoryForm.reset();
}

// Function to populate the select dropdown with ALL categories
function populateCategories() {
    categorySelect.innerHTML = ''; // Clear existing options

    // Default placeholder option
    const allOption = document.createElement('option');
    allOption.textContent = `--- Select Category ---`;
    allOption.value = '';
    allOption.disabled = true;
    allOption.selected = true;
    categorySelect.appendChild(allOption);
    
    if (allCategories.length === 0) {
        const option = document.createElement('option');
        option.textContent = `No categories. Create one!`;
        option.value = '';
        option.disabled = true;
        categorySelect.appendChild(option);
    } else {
        allCategories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name;
            categorySelect.appendChild(option);
        });
    }
}

// --- State Management ---

async function showAppState(isLoggedIn, username, role) {
    if (isLoggedIn) {
        // Set global role
        userRole = role;
        
        // Switch view from Auth to App
        authContainer.classList.add('hidden');
        appContent.classList.remove('hidden');
        
        const roleDisplay = role ? `<span class="font-bold text-emerald-700">(${role.toUpperCase()})</span>` : '';
        welcomeMessage.innerHTML = `Welcome back, <span class="font-bold">${username}</span>. Your role: ${roleDisplay}.`;
        
        // Disable income selection for standard users in the transaction form
        if (role !== 'admin') {
            incomeTypeRadio.disabled = true;
            document.querySelector('label[for="type-income"]').classList.add('opacity-50', 'cursor-not-allowed');
            document.getElementById('type-expense').checked = true;
            summaryButton.classList.add('hidden'); // Hide summary button from standard user
            downloadButton.classList.add('hidden'); // <-- ADDED: Hide download button from standard user
            dateRangeInputs.classList.add('hidden'); // Hide date range inputs
        } else {
            incomeTypeRadio.disabled = false;
            document.querySelector('label[for="type-income"]').classList.remove('opacity-50', 'cursor-not-allowed');
            summaryButton.classList.remove('hidden'); // Show summary button for admin
            downloadButton.classList.remove('hidden'); // <-- ADDED: Show download button for admin
            dateRangeInputs.classList.remove('hidden'); // Show date range inputs
        }
        
        // Fetch and populate all categories
        await fetchCategories();

    } else {
        // Switch view from App to Auth
        appContent.classList.add('hidden');
        authContainer.classList.remove('hidden');

        // Reset state
        userRole = null;
        allCategories = []; 
        
        showForm('login'); // Default to login form
        
        tabs.login.classList.add('border-emerald-600', 'text-emerald-600');
    }
}

// Initialize state on load
document.addEventListener('DOMContentLoaded', () => {
    const initialUser = document.body.getAttribute('data-logged-in-user');
    const initialRole = document.body.getAttribute('data-logged-in-role');
    
    if (initialUser) {
        showAppState(true, initialUser, initialRole);
    } else {
        showForm('login'); 
        tabs.login.classList.add('border-emerald-600', 'text-emerald-600');
    }
});

// --- API Handlers (Authentication, Category, Transaction) ---

async function fetchCategories() {
    clearMessage();
    try {
        // Using relative path, Flask will handle the endpoint
        const response = await fetch('categories'); 
        
        if (response.ok) {
            allCategories = await response.json(); // Store all categories
            populateCategories(); // Populate dropdown with all categories
            
        } else {
            showMessage('error', 'Failed to load categories.');
        }
    } catch (error) {
        console.error('Fetch categories error:', error);
        showMessage('error', 'Network error while fetching categories.');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    clearMessage();

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch('login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('success', data.message);
            document.getElementById('login-form').reset();
            // Pass the role back to showAppState
            showAppState(true, username, data.role); 
        } else {
            showMessage('error', data.message || 'Login failed.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('error', 'Network error. Could not connect to the server.');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    clearMessage();

    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value;
    const secret_key = document.getElementById('reg-secret').value;

    if (!username || !password || !secret_key) {
        return showMessage('error', 'Please fill in all fields.');
    }

    try {
        const response = await fetch('register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, secret_key })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('success', data.message + ' You can now log in.');
            document.getElementById('register-form').reset();
            showForm('login'); // Switch to login form
        } else {
            showMessage('error', data.message || 'Registration failed.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('error', 'Network error. Could not connect to the server.');
    }
}

async function handleNewCategory(event) {
    event.preventDefault();
    
    const name = document.getElementById('new-cat-name').value.trim();
    
    if (!name) {
        return showMessage('error', 'Category name cannot be empty.');
    }
    
    try {
        // Only sending name
        const response = await fetch('categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }) 
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('success', data.message);
            
            // Add new category to local state
            allCategories.push({ id: data.id, name: data.name });
            
            populateCategories(); // Update dropdown
            categorySelect.value = data.id; // Select the newly created category
            
            hideCategoryModal();
        } else {
            showMessage('error', data.message || 'Failed to create category.');
        }
    } catch (error) {
        console.error('New category error:', error);
        showMessage('error', 'Network error during category creation.');
    }
}

async function handleTransaction(event) {
    event.preventDefault();
    clearMessage();
    
    const amount = document.getElementById('trans-amount').value;
    const type = document.querySelector('input[name="trans-type"]:checked').value;
    const category_id = categorySelect.value;
    const note = document.getElementById('trans-note').value.trim();
    
    if (!amount || !category_id) {
        return showMessage('error', 'Please enter an amount and select a category.');
    }
    
    try {
        const response = await fetch('transactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount: amount,
                type: type,
                category_id: category_id,
                note: note
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            showMessage('success', data.message + ` (ID: ${data.id})`);
            transactionForm.reset();
            populateCategories(); 
        } else {
            showMessage('error', data.message || 'Failed to record transaction. Check permissions if recording Income.');
        }
    } catch (error) {
        console.error('Transaction error:', error);
        showMessage('error', 'Network error during transaction recording.');
    }
}

// NEW: Summary Handler
async function handleSummary() {
    clearMessage();
    
    let url = 'summary';
    const params = new URLSearchParams();
    
    const selectedCategoryId = categorySelect.value;
    const selectedCategoryName = categorySelect.options[categorySelect.selectedIndex].text;
    
    // 1. Add Category Filter
    if (selectedCategoryId && selectedCategoryName !== '--- Select Category ---') {
        params.append('category_id', selectedCategoryId);
    }
    
    // 2. Add Date Filters
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;

    if (startDate) {
        params.append('start_date', startDate);
    }
    if (endDate) {
        params.append('end_date', endDate);
    }
    
    const queryString = params.toString();
    if (queryString) {
        url += `?${queryString}`;
    }

    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok) {
            // --- 1. Update Header ---
            const dateDisplay = (startDate || endDate) 
                ? `${startDate || 'Start'} to ${endDate || 'End'}`
                : 'All Time';
                
            summaryCategoryDisplay.textContent = `For Category: ${data.category_name}`;
            summaryDateDisplay.textContent = `Date Range: ${dateDisplay}`;

            // --- 2. Update Balance ---
            let balance = parseFloat(data.balance).toFixed(2);
            summaryBalanceDisplay.textContent = `₹${balance}`;
            
            // Color-code the balance
            summaryBalanceDisplay.classList.remove('text-red-600', 'text-emerald-600', 'text-gray-900');
            if (parseFloat(data.balance) < 0) {
                summaryBalanceDisplay.classList.add('text-red-600');
            } else if (parseFloat(data.balance) > 0) {
                summaryBalanceDisplay.classList.add('text-emerald-600');
            } else {
                    summaryBalanceDisplay.classList.add('text-gray-900');
            }
            
            // --- 3. Draw Chart ---
            drawDailyChart(data.daily_summary);
            
            // --- 4. Update Top Categories ---
            populateCategoryList(topIncomeList, data.top_income_categories, 'income');
            populateCategoryList(topExpenseList, data.top_expense_categories, 'expense');

            // Show Modal
            summaryModal.classList.remove('hidden');

        } else {
            showMessage('error', data.message || 'Failed to calculate summary.');
        }
    } catch (error) {
        console.error('Summary error:', error);
        showMessage('error', 'Network error during summary calculation.');
    }
}

// --- CSV Download Logic ---

async function downloadCSV() {
    clearMessage(); // Clear any previous messages
    
    let url = 'transactions_csv';
    const params = new URLSearchParams();
    
    // Get category and date filters from form inputs
    const selectedCategoryId = categorySelect.value;
    const selectedCategoryName = categorySelect.options[categorySelect.selectedIndex].text;

    if (selectedCategoryId && selectedCategoryName !== '--- Select Category ---') {
        params.append('category_id', selectedCategoryId);
    }
    
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;

    if (startDate) {
        params.append('start_date', startDate);
    }
    if (endDate) {
        params.append('end_date', endDate);
    }
    
    const queryString = params.toString();
    if (queryString) {
        url += `?${queryString}`;
    }
    
    // Use window.location.href to trigger the browser to download the file 
    // sent by the server endpoint (Flask route /transactions_csv).
    window.location.href = url;
    
    // Show a success message (or at least an attempt message)
    showMessage('info', 'CSV download initiated. Check your downloads folder.');
}

// Helper function to draw the Chart.js line plot
function drawDailyChart(summaryData) {
    // Destroy existing chart if it exists
    if (dailyBalanceChart) {
        dailyBalanceChart.destroy();
    }

    const dates = summaryData.map(d => d.date);
    const incomes = summaryData.map(d => d.total_income);
    const expenses = summaryData.map(d => d.total_expense);

    const ctx = balanceChartCanvas.getContext('2d');
    dailyBalanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Income',
                data: incomes,
                borderColor: '#059669', // Emerald 600
                backgroundColor: 'rgba(5, 150, 105, 0.1)',
                tension: 0.3,
                fill: false
            }, {
                label: 'Expense',
                data: expenses,
                borderColor: '#ef4444', // Red 500
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.3,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Amount (₹)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                // Format as Indian Rupee (₹)
                                label += `₹${context.parsed.y.toFixed(2)}`;
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// Helper function to populate the Top Categories lists
function populateCategoryList(ulElement, categories, type) {
    ulElement.innerHTML = '';
    
    if (categories.length === 0) {
        const message = type === 'income' 
            ? 'No income transactions found in this range.'
            : 'No expense transactions found in this range.';
        ulElement.innerHTML = `<li class="text-gray-500 italic">${message}</li>`;
        return;
    }

    categories.forEach(cat => {
        const li = document.createElement('li');
        li.className = 'flex justify-between items-center py-1 border-b border-opacity-50 last:border-b-0';
        
        const amountClass = type === 'income' ? 'text-emerald-700' : 'text-red-700';

        li.innerHTML = `
            <span class="font-medium text-gray-800">${cat.name}</span>
            <span class="font-mono ${amountClass} font-semibold">₹${cat.total_amount.toFixed(2)}</span>
        `;
        ulElement.appendChild(li);
    });
}


async function handleLogout() {
    try {
        const response = await fetch('logout', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showMessage('info', data.message);
            showAppState(false, null, null);
        } else {
            showMessage('error', data.message || 'Logout failed.');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showMessage('error', 'Network error during logout.');
    }
}