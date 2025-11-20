let expenseCategories = [];
let incomeCategories = [];

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
        if (typeof USER_ROLE !== 'undefined' && USER_ROLE === 'admin') {
            displayCategoriesInManager(categories);
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function displayCategoriesInManager(categories) {
    const expenseList = document.getElementById('expenseCategoryList');
    const incomeList = document.getElementById('incomeCategoryList');

    if (!expenseList || !incomeList) return;

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
    if (!categorySelect) return;

    // Ensure currentType is defined or default to 'expense'
    const type = (typeof currentType !== 'undefined') ? currentType : 'expense';
    const categories = type === 'expense' ? expenseCategories : incomeCategories;

    categorySelect.innerHTML = '<option value="">Select Category</option>';
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        categorySelect.appendChild(option);
    });

    // Update filter category options with ALL categories
    const filterCategory = document.getElementById('filterCategory');
    if (filterCategory) {
        filterCategory.innerHTML = '<option value="all">All Categories</option>';
        [...expenseCategories, ...incomeCategories].forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            filterCategory.appendChild(option);
        });
    }
}
