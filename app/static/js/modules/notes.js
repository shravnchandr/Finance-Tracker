async function loadNotes() {
    try {
        const response = await fetch('/api/notes');
        const notes = await response.json();
        const grid = document.getElementById('notesGrid');
        if (!grid) return;

        if (notes.length === 0) {
            grid.innerHTML = '<p>No notes yet.</p>';
            return;
        }

        grid.innerHTML = notes.map(note => `
            <div class="note-card" style="background-color: ${note.color}">
                <div class="note-title">${note.title}</div>
                <div class="note-content">${note.content}</div>
                <div class="note-actions">
                    <button class="btn-small" onclick='editNote(${JSON.stringify(note).replace(/'/g, "&#39;")})'>Edit</button>
                    <button class="btn-small btn-delete" onclick="deleteNote(${note.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading notes:', error);
    }
}

function showAddNoteModal() {
    document.getElementById('noteModal').style.display = 'flex';
    document.getElementById('noteForm').reset();
    document.getElementById('noteId').value = '';
    document.getElementById('noteModalTitle').textContent = 'Add Note';
    document.getElementById('noteColor').value = '#ffffff';
}

function closeNoteModal() {
    document.getElementById('noteModal').style.display = 'none';
}

function selectNoteColor(color) {
    document.getElementById('noteColor').value = color;
    // Visual feedback could be added here
}

function editNote(note) {
    document.getElementById('noteModal').style.display = 'flex';
    document.getElementById('noteId').value = note.id;
    document.getElementById('noteTitleInput').value = note.title;
    document.getElementById('noteContentInput').value = note.content;
    document.getElementById('noteColor').value = note.color;
    document.getElementById('noteModalTitle').textContent = 'Edit Note';
}

const noteForm = document.getElementById('noteForm');
if (noteForm) {
    noteForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('noteId').value;
        const title = document.getElementById('noteTitleInput').value;
        const content = document.getElementById('noteContentInput').value;
        const color = document.getElementById('noteColor').value;

        const url = id ? `/api/notes/${id}` : '/api/notes';
        const method = id ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content, color })
            });

            if (response.ok) {
                closeNoteModal();
                loadNotes();
            } else {
                alert('Failed to save note');
            }
        } catch (error) {
            console.error('Error saving note:', error);
        }
    });
}

async function deleteNote(id) {
    if (!confirm('Delete this note?')) return;
    try {
        await fetch(`/api/notes/${id}`, { method: 'DELETE' });
        loadNotes();
    } catch (error) {
        console.error('Error deleting note:', error);
    }
}
