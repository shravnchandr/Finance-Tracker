// const USER_ROLE = "{{ role }}";
const USER_ROLE = document.body.getAttribute('user-role');

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

// --- Navigation Tabs ---
function switchNavTab(tabId) {
    // Update tab buttons
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick').includes(tabId)) {
            btn.classList.add('active');
        }
    });

    // Update content sections
    document.querySelectorAll('.nav-content').forEach(content => {
        content.classList.remove('active');
    });

    const sectionId = tabId === 'dashboard' ? 'dashboardSection' : tabId + 'Section';
    document.getElementById(sectionId).classList.add('active');

    // Load data if needed
    if (tabId === 'notes') loadNotes();
    if (tabId === 'reminders') loadReminders();
    if (tabId === 'calendar') loadCalendar();
}
