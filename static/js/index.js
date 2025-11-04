// const USER_ROLE = "{{ role }}";
const USER_ROLE = document.body.getAttribute('user-role');

let expenseCategories = [];
let incomeCategories = [];

let editingTransactionId = null;
let currentType = 'expense';
let currentAttachmentPath = null;

// Hide stats and download button for regular users
if (USER_ROLE === 'user') {
    document.getElementById('dashboardStats').classList.add('hidden');
    document.getElementById('downloadBtn').classList.add('hidden');
} else {
    // Show category manager for admins
    document.getElementById('dashboardStats').classList.add('hidden');
    document.getElementById('categoryManager').style.display = 'block';
    document.getElementById('categoryStats').style.display = 'block';
}

// Set today's date as default
document.getElementById('date').valueAsDate = new Date();

// Load categories first, then other data
loadCategories().then(() => {
    updateCategoryOptions();
    loadTransactions();
    if (USER_ROLE === 'admin') {
        loadStats();
        loadCategoryStats();
    }
});

function selectType(type) {
    currentType = type;
    document.getElementById('transactionType').value = type;
    
    document.querySelectorAll('.type-option').forEach(opt => {
        opt.classList.remove('active');
    });
    
    const clickedElement = event.target.closest('.type-option');
    if (clickedElement) {
        clickedElement.classList.add('active');
    }
    updateCategoryOptions();
}

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        
        expenseCategories = categories
            .filter(cat => cat.type === 'expense')
            .map(cat => cat.name);
        
        incomeCategories = categories
            .filter(cat => cat.type === 'income')
            .map(cat => cat.name);
        
        // Update category manager display for admins
        if (USER_ROLE === 'admin') {
            displayCategoriesInManager(categories);
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function displayCategoriesInManager(categories) {
    const expenseList = document.getElementById('expenseCategoryList');
    const incomeList = document.getElementById('incomeCategoryList');
    
    const expenseCats = categories.filter(cat => cat.type === 'expense');
    const incomeCats = categories.filter(cat => cat.type === 'income');
    
    expenseList.innerHTML = expenseCats.map(cat => `
        <div class="category-item">
            <div>
                <span class="cat-name">${cat.name}</span>
            </div>
            <button class="btn-delete-cat" onclick="deleteCategory(${cat.id}, '${cat.name.replace(/'/g, "\\'")}')">Delete</button>
        </div>
    `).join('');
    
    incomeList.innerHTML = incomeCats.map(cat => `
        <div class="category-item">
            <div>
                <span class="cat-name">${cat.name}</span>
            </div>
            <button class="btn-delete-cat" onclick="deleteCategory(${cat.id}, '${cat.name.replace(/'/g, "\\'")}')">Delete</button>
        </div>
    `).join('');
}

async function addCategory() {
    const name = document.getElementById('newCategoryName').value.trim();
    const icon = document.getElementById('newCategoryIcon').value.trim();
    const type = document.getElementById('newCategoryType').value;
    
    if (!name) {
        alert('Please enter a category name');
        return;
    }
    
    const fullName = icon ? `${icon} ${name}` : name;
    
    try {
        const response = await fetch('/api/categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: fullName, type: type, icon: icon })
        });
        
        if (response.ok) {
            document.getElementById('newCategoryName').value = '';
            document.getElementById('newCategoryIcon').value = '';
            await loadCategories();
            updateCategoryOptions();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to add category');
        }
    } catch (error) {
        alert('Error adding category');
    }
}

async function deleteCategory(id, name) {
    if (!confirm(`Delete category "${name}"?\n\nNote: You can only delete categories that are not in use.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadCategories();
            updateCategoryOptions();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to delete category');
        }
    } catch (error) {
        alert('Error deleting category');
    }
}

function updateCategoryOptions() {
    const categorySelect = document.getElementById('category');
    const categories = currentType === 'expense' ? expenseCategories : incomeCategories;
    
    categorySelect.innerHTML = '<option value="">Select Category</option>';
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        categorySelect.appendChild(option);
    });

    // Update filter category options with ALL categories
    const filterCategory = document.getElementById('filterCategory');
    filterCategory.innerHTML = '<option value="all">All Categories</option>';
    [...expenseCategories, ...incomeCategories].forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        filterCategory.appendChild(option);
    });
}

// Form submission
document.getElementById('transactionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const transType = document.getElementById('transactionType').value;
    const amount = document.getElementById('amount').value;
    const category = document.getElementById('category').value;
    const description = document.getElementById('description').value;
    const date = document.getElementById('date').value;
    const attachment = document.getElementById('attachment').files[0];

    if (!amount || !category || !date) {
        alert('Please fill in all required fields');
        return;
    }
    
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('amount', amount);
    formData.append('type', transType);
    formData.append('category', category);
    formData.append('description', description);
    formData.append('date', date);
    
    if (attachment) {
        formData.append('attachment', attachment);
    }

    try {
        let response;
        if (editingTransactionId) {
            response = await fetch(`/api/transactions/${editingTransactionId}`, {
                method: 'PUT',
                body: formData
            });
        } else {
            response = await fetch('/api/transactions', {
                method: 'POST',
                body: formData
            });
        }

        if (response.ok) {
            editingTransactionId = null;
            currentAttachmentPath = null;
            document.getElementById('transactionForm').reset();
            document.getElementById('date').valueAsDate = new Date();
            document.getElementById('transactionType').value = 'expense';
            document.getElementById('currentAttachment').style.display = 'none';
            currentType = 'expense';
            
            document.querySelectorAll('.type-option').forEach(opt => opt.classList.remove('active'));
            document.querySelector('.type-option.expense').classList.add('active');
            
            document.querySelector('.btn').textContent = 'Add Transaction';
            document.getElementById('formTitle').textContent = 'Add Transaction';
            
            updateCategoryOptions();
            await loadTransactions();
            if (USER_ROLE === 'admin') {
                await loadStats();
                await loadCategoryStats();
            }
        } else {
            const errorData = await response.json();
            alert('Error: ' + (errorData.error || 'Failed to save transaction'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving transaction. Please try again.');
    }
});

// Filter listeners
document.getElementById('filterType').addEventListener('change', loadTransactions);
document.getElementById('filterCategory').addEventListener('change', loadTransactions);
document.getElementById('startDate').addEventListener('change', loadTransactions);
document.getElementById('endDate').addEventListener('change', loadTransactions);

async function loadTransactions() {
    const type = document.getElementById('filterType').value;
    const category = document.getElementById('filterCategory').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    let url = '/api/transactions?';
    if (type !== 'all') url += `type=${type}&`;
    if (category !== 'all') url += `category=${category}&`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}`;

    const response = await fetch(url);
    const transactions = await response.json();

    const transactionList = document.getElementById('transactionList');
    
    if (transactions.length === 0) {
        transactionList.innerHTML = '<div class="empty-state"><p>No transactions found</p></div>';
        return;
    }

    transactionList.innerHTML = transactions.map(trans => {
        const escapedDescription = (trans.description || 'No description').replace(/'/g, '&#39;').replace(/"/g, '&quot;');
        const transData = {
            id: trans.id,
            amount: trans.amount,
            type: trans.type,
            category: trans.category,
            description: trans.description || '',
            date: trans.date,
            attachment_filename: trans.attachment_filename,
            attachment_path: trans.attachment_path
        };
        
        const userBadge = USER_ROLE === 'admin' ? `<span class="user-badge">${trans.username}</span>` : '';
        
        const attachmentBadge = trans.attachment_filename ? 
            `<span class="attachment-badge" onclick="viewAttachment('${trans.attachment_path}', '${trans.attachment_filename}')" title="View attachment">📎 ${trans.attachment_filename}</span>` : '';
        
        return `
        <div class="transaction-item ${trans.type}">
            <div class="transaction-info">
                <h4>
                    <span class="type-badge ${trans.type}">${trans.type}</span>
                    <span class="category-badge" style="color:#FFb59A">${trans.category}</span>
                    ${userBadge}
                    ${attachmentBadge}
                </h4>
                <p>${escapedDescription}</p>
                <p style="font-size: 0.813rem; margin-top: 4px;">${new Date(trans.date).toLocaleDateString()}</p>
            </div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div class="transaction-amount ${trans.type}">
                    ${trans.type === 'income' ? '+' : '-'}₹${trans.amount.toFixed(2)}
                </div>
                <div class="transaction-actions">
                    <button class="btn-small btn-edit" onclick='editTransaction(${JSON.stringify(transData)})'>Edit</button>
                    <button class="btn-small btn-delete" onclick="deleteTransaction(${trans.id})">Delete</button>
                </div>
            </div>
        </div>
    `;
    }).join('');
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) return;
        
        const stats = await response.json();

        document.getElementById('totalIncome').textContent = `₹${stats.total_income.toFixed(2)}`;
        document.getElementById('totalExpenses').textContent = `₹${stats.total_expenses.toFixed(2)}`;
        document.getElementById('balance').textContent = `₹${stats.balance.toFixed(2)}`;

        const allTransactions = await fetch('/api/transactions');
        const transactions = await allTransactions.json();
        document.getElementById('totalItems').textContent = transactions.length;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function editTransaction(trans) {
    editingTransactionId = trans.id;
    currentType = trans.type;
    currentAttachmentPath = trans.attachment_path;
    
    document.getElementById('amount').value = trans.amount;
    document.getElementById('transactionType').value = trans.type;
    document.getElementById('description').value = trans.description || '';
    document.getElementById('date').value = trans.date;
    
    // Show current attachment if exists
    if (trans.attachment_filename) {
        document.getElementById('currentAttachment').style.display = 'block';
        document.getElementById('attachmentName').textContent = trans.attachment_filename;
    } else {
        document.getElementById('currentAttachment').style.display = 'none';
    }
    
    document.querySelectorAll('.type-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector(`.type-option.${trans.type}`).classList.add('active');
    
    updateCategoryOptions();
    
    setTimeout(() => {
        document.getElementById('category').value = trans.category;
    }, 100);
    
    document.querySelector('.btn').textContent = 'Update Transaction';
    document.getElementById('formTitle').textContent = 'Edit Transaction';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function viewAttachment(path, filename) {
    if (path) {
        window.open(`/api/attachments/${path}`, '_blank');
    }
}

async function removeAttachment() {
    if (!editingTransactionId) return;
    
    if (!confirm('Remove attachment from this transaction?')) return;
    
    try {
        const response = await fetch(`/api/transactions/${editingTransactionId}/attachment`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            document.getElementById('currentAttachment').style.display = 'none';
            currentAttachmentPath = null;
            alert('Attachment removed successfully');
        } else {
            alert('Error removing attachment');
        }
    } catch (error) {
        alert('Error removing attachment');
    }
}

async function deleteTransaction(id) {
    if (confirm('Are you sure you want to delete this transaction?')) {
        try {
            const response = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
            if (response.ok) {
                loadTransactions();
                if (USER_ROLE === 'admin') {
                    loadStats();
                    loadCategoryStats();
                }
            } else {
                alert('Error deleting transaction');
            }
        } catch (error) {
            alert('Error deleting transaction');
        }
    }
}

async function downloadCSV() {
    const type = document.getElementById('filterType').value;
    const category = document.getElementById('filterCategory').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    let url = '/api/download-csv?';
    if (type !== 'all') url += `type=${type}&`;
    if (category !== 'all') url += `category=${category}&`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}`;

    window.location.href = url;
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}


function switchStatsTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.stats-tab').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update content
    document.querySelectorAll('.stats-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tab + 'StatsContent').classList.add('active');
}

async function loadCategoryStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) return;
        
        const stats = await response.json();
        
        // Display expense category stats
        displayCategoryStats(stats.expense_by_category, 'expense', stats.total_expenses);
        
        // Display income category stats
        displayCategoryStats(stats.income_by_category, 'income', stats.total_income);
        
        // Display comparison
        displayComparison(stats.expense_by_category, stats.income_by_category, stats.total_expenses, stats.total_income);
        
    } catch (error) {
        console.error('Error loading category stats:', error);
    }
}

function displayCategoryStats(categories, type, total) {
    const gridId = type === 'expense' ? 'expenseStatsGrid' : 'incomeStatsGrid';
    const grid = document.getElementById(gridId);
    
    if (!categories || categories.length === 0) {
        grid.innerHTML = `<div class="no-data">No ${type} data available</div>`;
        return;
    }
    
    grid.innerHTML = categories.map(cat => {
        const percentage = total > 0 ? ((cat.total / total) * 100).toFixed(1) : 0;
        
        return `
            <div class="category-stat-card ${type}">
                <div class="category-stat-header">
                    <span class="category-stat-name">${cat.category}</span>
                    <span class="category-stat-percentage">${percentage}%</span>
                </div>
                <div class="category-stat-amount ${type}">
                    ₹${cat.total.toFixed(2)}
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${type}" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

function displayComparison(expenseCategories, incomeCategories, totalExpenses, totalIncome) {
    const grid = document.getElementById('comparisonGrid');
    
    const balance = totalIncome - totalExpenses;
    const savingsRate = totalIncome > 0 ? ((balance / totalIncome) * 100).toFixed(1) : 0;
    
    let html = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px;">
            <div class="stat-card income">
                <h3>Total Income</h3>
                <div class="value">₹${totalIncome.toFixed(2)}</div>
            </div>
            <div class="stat-card expense">
                <h3>Total Expenses</h3>
                <div class="value">₹${totalExpenses.toFixed(2)}</div>
            </div>
            <div class="stat-card balance">
                <h3>Net Balance</h3>
                <div class="value">₹${balance.toFixed(2)}</div>
            </div>
            <div class="stat-card">
                <h3>Savings Rate</h3>
                <div class="value">${savingsRate}%</div>
            </div>
        </div>
        
        <h3 style="margin-bottom: 16px; color: var(--on-surface); font-weight: 500;">Top Spending Categories</h3>
        <div class="category-stats-grid">
    `;
    
    const topExpenses = expenseCategories.slice(0, 6);
    html += topExpenses.map(cat => {
        const percentage = totalExpenses > 0 ? ((cat.total / totalExpenses) * 100).toFixed(1) : 0;
        return `
            <div class="category-stat-card expense">
                <div class="category-stat-header">
                    <span class="category-stat-name">${cat.category}</span>
                    <span class="category-stat-percentage">${percentage}%</span>
                </div>
                <div class="category-stat-amount expense">
                    ₹${cat.total.toFixed(2)}
                </div>
                <div class="progress-bar">
                    <div class="progress-fill expense" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }).join('');
    
    html += '</div>';
    
    html += '<h3 style="margin: 32px 0 16px; color: var(--on-surface); font-weight: 500;">Top Income Sources</h3>';
    html += '<div class="category-stats-grid">';
    
    const topIncome = incomeCategories.slice(0, 6);
    html += topIncome.map(cat => {
        const percentage = totalIncome > 0 ? ((cat.total / totalIncome) * 100).toFixed(1) : 0;
        return `
            <div class="category-stat-card income">
                <div class="category-stat-header">
                    <span class="category-stat-name">${cat.category}</span>
                    <span class="category-stat-percentage">${percentage}%</span>
                </div>
                <div class="category-stat-amount income">
                    ₹${cat.total.toFixed(2)}
                </div>
                <div class="progress-bar">
                    <div class="progress-fill income" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }).join('');
    
    html += '</div>';
    
    grid.innerHTML = html;
}