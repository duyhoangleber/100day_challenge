let tasksList = [];
let currentDayNumber = null;
let editingTaskId = null;
let daysSummary = {};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    loadTasksList();
    loadDaysSummary();
    renderCalendar();
    updateStats();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Add task button
    document.getElementById('addTaskBtn').addEventListener('click', function() {
        showAddTaskForm();
    });
    
    // Save edit task button
    document.getElementById('saveEditTaskBtn').addEventListener('click', function() {
        saveEditTask();
    });
    
    // Close edit task modal
    document.getElementById('closeEditTaskModal').addEventListener('click', function() {
        hideEditTaskModal();
    });
    
    // Cancel edit task button
    document.getElementById('cancelEditTaskBtn').addEventListener('click', function() {
        hideEditTaskModal();
    });
    
    // Enter key in edit task input
    document.getElementById('editTaskInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            saveEditTask();
        }
    });
    
    // Close day modal
    document.getElementById('closeDayModal').addEventListener('click', function() {
        document.getElementById('dayTasksModal').style.display = 'none';
    });
    
    // Save day tasks
    document.getElementById('saveDayTasks').addEventListener('click', function() {
        saveDayTasks();
    });
    
    // Click outside modal to close
    window.onclick = function(event) {
        const dayModal = document.getElementById('dayTasksModal');
        const editModal = document.getElementById('editTaskModal');
        if (event.target === dayModal) {
            dayModal.style.display = 'none';
        }
        if (event.target === editModal) {
            editModal.style.display = 'none';
        }
    };
}

// Load tasks list
async function loadTasksList() {
    try {
        const response = await fetch('/api/tasks-list');
        tasksList = await response.json();
        renderTasksList();
        // Reload days summary when tasks list changes
        await loadDaysSummary();
        renderCalendar();
    } catch (error) {
        console.error('Error loading tasks list:', error);
    }
}

// Render tasks list
function renderTasksList() {
    const container = document.getElementById('tasksList');
    container.innerHTML = '';
    
    if (tasksList.length === 0) {
        container.innerHTML = '<p class="empty-message">No tasks yet. Click "Add Task" to get started!</p>';
        return;
    }
    
    tasksList.forEach(task => {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        taskItem.dataset.taskId = task.id;
        
        taskItem.innerHTML = `
            <span class="task-name" data-task-id="${task.id}">${escapeHtml(task.task_name)}</span>
            <button class="btn-delete-task" data-task-id="${task.id}" title="Delete">×</button>
        `;
        
        // Click on task name to edit
        taskItem.querySelector('.task-name').addEventListener('click', function() {
            editTask(task.id);
        });
        
        // Delete task
        taskItem.querySelector('.btn-delete-task').addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering edit
            deleteTask(task.id);
        });
        
        container.appendChild(taskItem);
    });
}

// Show add task form (using modal)
function showAddTaskForm() {
    editingTaskId = null;
    document.getElementById('editTaskModalTitle').textContent = 'Add New Task';
    document.getElementById('editTaskInput').value = '';
    document.getElementById('editTaskModal').style.display = 'block';
    setTimeout(() => {
        document.getElementById('editTaskInput').focus();
    }, 100);
}

// Show edit task modal
function showEditTaskModal(taskId) {
    const task = tasksList.find(t => t.id === taskId);
    if (task) {
        editingTaskId = taskId;
        document.getElementById('editTaskModalTitle').textContent = 'Edit Task';
        document.getElementById('editTaskInput').value = task.task_name;
        document.getElementById('editTaskModal').style.display = 'block';
        setTimeout(() => {
            document.getElementById('editTaskInput').focus();
        }, 100);
    }
}

// Hide edit task modal
function hideEditTaskModal() {
    document.getElementById('editTaskModal').style.display = 'none';
    document.getElementById('editTaskInput').value = '';
    editingTaskId = null;
}

// Save edit task
async function saveEditTask() {
    const taskName = document.getElementById('editTaskInput').value.trim();
    
    if (!taskName) {
        alert('Please enter a task name');
        return;
    }
    
    try {
        if (editingTaskId) {
            // Update existing task
            const response = await fetch(`/api/tasks-list/${editingTaskId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task_name: taskName })
            });
            
            if (response.ok) {
                await loadTasksList();
                hideEditTaskModal();
            } else {
                alert('Error updating task');
            }
        } else {
            // Add new task
            const response = await fetch('/api/tasks-list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task_name: taskName })
            });
            
            if (response.ok) {
                await loadTasksList();
                hideEditTaskModal();
            } else {
                alert('Error adding task');
            }
        }
    } catch (error) {
        console.error('Error saving task:', error);
        alert('Error saving task');
    }
}

// Edit task
function editTask(taskId) {
    showEditTaskModal(taskId);
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks-list/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadTasksList();
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        alert('Error deleting task');
    }
}

// Load days summary
async function loadDaysSummary() {
    try {
        const response = await fetch('/api/days/summary');
        daysSummary = await response.json();
    } catch (error) {
        console.error('Error loading days summary:', error);
    }
}

// Render calendar by weeks
function renderCalendar() {
    const calendar = document.getElementById('calendar');
    calendar.innerHTML = '';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Calculate start date (Monday of the week containing day 1)
    const startDate = new Date(today);
    const dayOfWeek = startDate.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Adjust to Monday
    startDate.setDate(today.getDate() + daysToMonday);
    
    // Group days into weeks
    const weeks = [];
    let currentWeek = [];
    
    for (let day = 1; day <= 100; day++) {
        const dayDate = new Date(today);
        dayDate.setDate(today.getDate() + (day - 1));
        
        const dayOfWeek = dayDate.getDay();
        const isMonday = dayOfWeek === 1;
        
        // Start new week on Monday or if it's the first day
        if (isMonday && currentWeek.length > 0) {
            weeks.push(currentWeek);
            currentWeek = [];
        }
        
        currentWeek.push({ day, date: dayDate });
        
        // Push last week if we've reached day 100
        if (day === 100) {
            weeks.push(currentWeek);
        }
    }
    
    // Render weeks
    weeks.forEach((week, weekIndex) => {
        const weekRow = document.createElement('div');
        weekRow.className = 'week-row';
        
        // Fill empty cells before first day if needed
        if (weekIndex === 0) {
            const firstDayDate = week[0].date;
            const firstDayOfWeek = firstDayDate.getDay();
            const daysToAdd = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1; // Days to Monday
            
            for (let i = 0; i < daysToAdd; i++) {
                const emptyCell = document.createElement('div');
                emptyCell.className = 'day-card empty';
                weekRow.appendChild(emptyCell);
            }
        }
        
        // Render days in week
        week.forEach(({ day, date }) => {
            const dayCard = createDayCard(day, date);
            weekRow.appendChild(dayCard);
        });
        
        // Fill empty cells after last day if needed
        if (weekIndex === weeks.length - 1) {
            const lastDayDate = week[week.length - 1].date;
            const lastDayOfWeek = lastDayDate.getDay();
            const daysToAdd = lastDayOfWeek === 0 ? 0 : 7 - lastDayOfWeek; // Days to Sunday
            
            for (let i = 0; i < daysToAdd; i++) {
                const emptyCell = document.createElement('div');
                emptyCell.className = 'day-card empty';
                weekRow.appendChild(emptyCell);
            }
        }
        
        calendar.appendChild(weekRow);
    });
}

// Create day card
function createDayCard(day, date) {
    const dayCard = document.createElement('div');
    dayCard.className = 'day-card';
    dayCard.dataset.day = day;
    
    // Check if this is today
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const isToday = date.toDateString() === today.toDateString();
    if (isToday) {
        dayCard.classList.add('today');
    }
    
    // Check if date is in the future
    const isFuture = date > today;
    
    // Check if date is more than 2 days in the past
    const twoDaysAgo = new Date(today);
    twoDaysAgo.setDate(today.getDate() - 2);
    const isTooOld = date < twoDaysAgo;
    
    // Check if this day can be edited
    const canEdit = !isFuture && !isTooOld;
    
    // Get task summary
    const summary = daysSummary[day] || { completed: 0, total: 0 };
    const hasTasks = summary.total > 0;
    
    // Calculate completion percentage
    let completionPercentage = 0;
    if (hasTasks) {
        completionPercentage = (summary.completed / summary.total) * 100;
    }
    
    // Add color class based on completion status
    // Future days stay white (default)
    if (!isFuture) {
        if (hasTasks) {
            if (completionPercentage === 100) {
                // 100% completed - green
                dayCard.classList.add('status-completed');
            } else if (completionPercentage > 50) {
                // > 50% completed - yellow/orange
                dayCard.classList.add('status-progress-high');
            } else if (completionPercentage > 0) {
                // < 50% completed - red/orange
                dayCard.classList.add('status-progress-low');
            } else {
                // 0% completed (has tasks but none done) - gray
                dayCard.classList.add('status-not-started');
            }
        } else {
            // No tasks defined - gray
            dayCard.classList.add('status-not-started');
        }
    }
    
    // Add disabled class if cannot edit
    if (!canEdit) {
        dayCard.classList.add('disabled');
    }
    
    // Day label (Mon, Tue, etc.)
    const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const dayLabel = dayLabels[date.getDay()];
    
    dayCard.innerHTML = `
        <div class="day-label">${dayLabel}</div>
        <div class="day-number">Day ${day}</div>
        <div class="day-date">${formatDate(date)}</div>
        ${hasTasks ? `<div class="day-progress">${summary.completed}/${summary.total}</div>` : ''}
        ${!canEdit ? '<div class="day-locked">🔒</div>' : ''}
    `;
    
    // Click to open day tasks modal (only if editable)
    dayCard.addEventListener('click', function() {
        if (canEdit) {
            openDayTasksModal(day);
        } else {
            let message = '';
            if (isFuture) {
                message = 'This day is in the future and cannot be edited yet.';
            } else if (isTooOld) {
                message = 'This day is more than 2 days in the past and cannot be edited.';
            }
            if (message) {
                alert(message);
            }
        }
    });
    
    return dayCard;
}

// Open day tasks modal
async function openDayTasksModal(day) {
    currentDayNumber = day;
    const modal = document.getElementById('dayTasksModal');
    const modalDayNumber = document.getElementById('modalDayNumber');
    
    modalDayNumber.textContent = day;
    
    // Load day tasks
    try {
        const response = await fetch(`/api/days/${day}`);
        const data = await response.json();
        
        renderDayTasks(data.tasks);
        document.getElementById('dayNotesTextarea').value = data.notes || '';
        
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error loading day tasks:', error);
        alert('Error loading day tasks');
    }
}

// Render day tasks with checkboxes
function renderDayTasks(tasks) {
    const container = document.getElementById('dayTasksList');
    container.innerHTML = '';
    
    if (tasks.length === 0) {
        container.innerHTML = '<p class="empty-message">No tasks defined yet. Add tasks in the header section.</p>';
        return;
    }
    
    tasks.forEach(task => {
        const taskItem = document.createElement('div');
        taskItem.className = 'day-task-item';
        
        taskItem.innerHTML = `
            <label class="checkbox-label">
                <input type="checkbox" 
                       class="task-checkbox" 
                       data-task-id="${task.id}" 
                       ${task.completed ? 'checked' : ''}>
                <span class="task-text ${task.completed ? 'completed' : ''}">${escapeHtml(task.task_name)}</span>
            </label>
        `;
        
        // Toggle completion on checkbox change
        taskItem.querySelector('.task-checkbox').addEventListener('change', function() {
            const checkbox = this;
            const taskText = taskItem.querySelector('.task-text');
            if (checkbox.checked) {
                taskText.classList.add('completed');
            } else {
                taskText.classList.remove('completed');
            }
        });
        
        container.appendChild(taskItem);
    });
}

// Save day tasks
async function saveDayTasks() {
    if (!currentDayNumber) return;
    
    const checkboxes = document.querySelectorAll('#dayTasksList .task-checkbox');
    const notes = document.getElementById('dayNotesTextarea').value;
    
    try {
        // Save each task status
        for (const checkbox of checkboxes) {
            const taskId = parseInt(checkbox.dataset.taskId);
            const completed = checkbox.checked;
            
            await fetch(`/api/days/${currentDayNumber}/task/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ completed: completed })
            });
        }
        
        // Save notes
        await fetch(`/api/days/${currentDayNumber}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ notes: notes })
        });
        
        document.getElementById('dayTasksModal').style.display = 'none';
        await loadDaysSummary();
        renderCalendar();
        updateStats();
    } catch (error) {
        console.error('Error saving day tasks:', error);
        alert('Error saving tasks');
    }
}

// Update statistics
async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('completed').textContent = stats.completed_days;
        document.getElementById('remaining').textContent = stats.remaining;
        document.getElementById('percentage').textContent = stats.percentage + '%';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Format date
function formatDate(date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}`;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
