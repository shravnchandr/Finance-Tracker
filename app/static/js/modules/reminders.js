async function loadReminders() {
    try {
        const response = await fetch('/api/reminders');
        const reminders = await response.json();
        const list = document.getElementById('reminderList');
        if (!list) return;

        if (reminders.length === 0) {
            list.innerHTML = '<p>No reminders yet.</p>';
            return;
        }

        list.innerHTML = reminders.map(rem => `
            <div class="reminder-item ${rem.is_completed ? 'completed' : ''}">
                <input type="checkbox" class="reminder-checkbox" 
                       ${rem.is_completed ? 'checked' : ''} 
                       onchange="toggleReminder(${rem.id}, this.checked)">
                <div class="reminder-content">
                    <div class="reminder-title">${rem.title}</div>
                    ${rem.due_date ? `<div class="reminder-date">Due: ${rem.due_date}</div>` : ''}
                </div>
                <button class="btn-small btn-delete" onclick="deleteReminder(${rem.id})">Delete</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

const reminderForm = document.getElementById('reminderForm');
if (reminderForm) {
    reminderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('reminderTitle').value;
        const dueDate = document.getElementById('reminderDueDate').value;

        try {
            const response = await fetch('/api/reminders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, due_date: dueDate || null })
            });

            if (response.ok) {
                document.getElementById('reminderForm').reset();
                loadReminders();
            } else {
                alert('Failed to add reminder');
            }
        } catch (error) {
            console.error('Error adding reminder:', error);
        }
    });
}

async function toggleReminder(id, isCompleted) {
    try {
        await fetch(`/api/reminders/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_completed: isCompleted })
        });
        loadReminders();
    } catch (error) {
        console.error('Error toggling reminder:', error);
    }
}

async function deleteReminder(id) {
    if (!confirm('Delete this reminder?')) return;
    try {
        await fetch(`/api/reminders/${id}`, { method: 'DELETE' });
        loadReminders();
    } catch (error) {
        console.error('Error deleting reminder:', error);
    }
}
