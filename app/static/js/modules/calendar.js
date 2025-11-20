let currentCalendarDate = new Date();

function changeMonth(delta) {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() + delta);
    loadCalendar();
}

async function loadCalendar() {
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();

    const monthYearEl = document.getElementById('calendarMonthYear');
    if (monthYearEl) {
        monthYearEl.textContent = new Date(year, month).toLocaleString('default', { month: 'long', year: 'numeric' });
    }

    const grid = document.getElementById('calendarGrid');
    if (!grid) return;

    // 1. Render Grid Structure immediately
    let gridHtml = '';

    // Add day headers
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => {
        gridHtml += `<div class="calendar-day-header">${day}</div>`;
    });

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();

    // Previous month filler
    for (let i = 0; i < startingDay; i++) {
        gridHtml += '<div class="calendar-day other-month"></div>';
    }

    // Days of current month
    const today = new Date();
    for (let i = 1; i <= daysInMonth; i++) {
        const isToday = i === today.getDate() && month === today.getMonth() && year === today.getFullYear();
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;

        gridHtml += `
            <div class="calendar-day ${isToday ? 'today' : ''}" data-date="${dateStr}">
                <div class="calendar-date">${i}</div>
                <div class="events-container"></div>
            </div>
        `;
    }

    grid.innerHTML = gridHtml;

    // 2. Fetch and Render Events asynchronously
    try {
        const response = await fetch('/api/calendar/events');
        const events = await response.json();

        events.forEach(event => {
            // Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM formats
            const eventDate = event.start_time.split('T')[0];
            const dayEl = grid.querySelector(`.calendar-day[data-date="${eventDate}"] .events-container`);

            if (dayEl) {
                const eventEl = document.createElement('div');
                eventEl.className = 'calendar-event';
                eventEl.style.backgroundColor = `${event.color}20`;
                eventEl.style.color = event.color;
                eventEl.style.border = `1px solid ${event.color}`;
                eventEl.title = `${event.type.toUpperCase()}: ${event.title}\n${event.description || ''}`;
                eventEl.textContent = event.title;

                // Add icon based on type
                if (event.type === 'reminder') eventEl.textContent = '🔔 ' + event.title;
                if (event.type === 'note') eventEl.textContent = '📝 ' + event.title;

                dayEl.appendChild(eventEl);
            }
        });
    } catch (error) {
        console.error('Error loading events:', error);
    }
}

// Event Form
const eventForm = document.getElementById('eventForm');
if (eventForm) {
    eventForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('eventTitle').value;
        const description = document.getElementById('eventDescription').value;
        const start = document.getElementById('eventStart').value;
        const end = document.getElementById('eventEnd').value;
        const color = document.getElementById('eventColor').value;

        try {
            const response = await fetch('/api/calendar/events', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description, start_time: start, end_time: end, color })
            });

            if (response.ok) {
                document.getElementById('eventForm').reset();
                loadCalendar();
            } else {
                alert('Failed to add event');
            }
        } catch (error) {
            console.error('Error adding event:', error);
        }
    });
}
