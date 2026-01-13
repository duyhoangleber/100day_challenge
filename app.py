from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database file
DB_FILE = '100day_challenge.db'

def init_db():
    """Initialize database with tasks table"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tasks list table - common tasks for all days
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Daily tasks - track completion of each task for each day
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_number INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES tasks_list(id),
            UNIQUE(day_number, task_id)
        )
    ''')
    
    # Day notes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS day_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_number INTEGER NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(day_number)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Main calendar view"""
    return render_template('index.html')

@app.route('/api/tasks-list', methods=['GET'])
def get_tasks_list():
    """Get all tasks in the list"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, task_name, task_order FROM tasks_list ORDER BY task_order, id')
    tasks = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': task['id'],
        'task_name': task['task_name'],
        'task_order': task['task_order']
    } for task in tasks])

@app.route('/api/tasks-list', methods=['POST'])
def add_task():
    """Add a new task to the list"""
    data = request.json
    task_name = data.get('task_name', '').strip()
    
    if not task_name:
        return jsonify({'error': 'task_name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(task_order) as max_order FROM tasks_list')
    max_order = cursor.fetchone()['max_order'] or 0
    
    cursor.execute('''
        INSERT INTO tasks_list (task_name, task_order)
        VALUES (?, ?)
    ''', (task_name, max_order + 1))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': task_id, 'task_name': task_name, 'task_order': max_order + 1})

@app.route('/api/tasks-list/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task name"""
    data = request.json
    task_name = data.get('task_name', '').strip()
    
    if not task_name:
        return jsonify({'error': 'task_name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks_list SET task_name = ? WHERE id = ?', (task_name, task_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/tasks-list/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task from the list"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks_list WHERE id = ?', (task_id,))
    cursor.execute('DELETE FROM daily_tasks WHERE task_id = ?', (task_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/days/<int:day_number>', methods=['GET'])
def get_day_tasks(day_number):
    """Get tasks status for a specific day"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tasks
    cursor.execute('SELECT id, task_name FROM tasks_list ORDER BY task_order, id')
    all_tasks = cursor.fetchall()
    
    # Get completed tasks for this day
    cursor.execute('''
        SELECT task_id FROM daily_tasks 
        WHERE day_number = ? AND completed = 1
    ''', (day_number,))
    completed_tasks = {row['task_id'] for row in cursor.fetchall()}
    
    # Get notes for this day
    cursor.execute('SELECT notes FROM day_notes WHERE day_number = ?', (day_number,))
    notes_row = cursor.fetchone()
    notes = notes_row['notes'] if notes_row else ''
    
    conn.close()
    
    tasks = [{
        'id': task['id'],
        'task_name': task['task_name'],
        'completed': task['id'] in completed_tasks
    } for task in all_tasks]
    
    return jsonify({'tasks': tasks, 'notes': notes})

@app.route('/api/days/summary', methods=['GET'])
def get_days_summary():
    """Get summary of tasks for all days"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total number of tasks
    cursor.execute('SELECT COUNT(*) as total FROM tasks_list')
    total_tasks = cursor.fetchone()['total'] or 0
    
    # Get completed tasks count for each day
    cursor.execute('''
        SELECT day_number, COUNT(*) as completed_count
        FROM daily_tasks
        WHERE completed = 1
        GROUP BY day_number
    ''')
    completed_by_day = {row['day_number']: row['completed_count'] for row in cursor.fetchall()}
    
    conn.close()
    
    summary = {}
    for day in range(1, 101):
        summary[day] = {
            'completed': completed_by_day.get(day, 0),
            'total': total_tasks
        }
    
    return jsonify(summary)

@app.route('/api/days/<int:day_number>/task/<int:task_id>', methods=['POST'])
def toggle_day_task(day_number, task_id):
    """Toggle task completion for a specific day"""
    data = request.json
    completed = data.get('completed', False)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO daily_tasks (day_number, task_id, completed)
        VALUES (?, ?, ?)
    ''', (day_number, task_id, 1 if completed else 0))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/days/<int:day_number>/notes', methods=['POST'])
def update_day_notes(day_number):
    """Update notes for a specific day"""
    data = request.json
    notes = data.get('notes', '')
    
    start_date = datetime.now().date()
    task_date = start_date + timedelta(days=day_number - 1)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO day_notes (day_number, date, notes)
        VALUES (?, ?, ?)
    ''', (day_number, task_date.isoformat(), notes))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total number of tasks
    cursor.execute('SELECT COUNT(*) as total FROM tasks_list')
    total_tasks = cursor.fetchone()['total'] or 0
    
    if total_tasks == 0:
        conn.close()
        return jsonify({
            'completed_days': 0,
            'total_days': 100,
            'remaining': 100,
            'percentage': 0
        })
    
    # Count days with all tasks completed
    cursor.execute('''
        SELECT dt.day_number, 
               COUNT(DISTINCT dt.task_id) as completed_count
        FROM daily_tasks dt
        WHERE dt.completed = 1
        GROUP BY dt.day_number
        HAVING completed_count = ?
    ''', (total_tasks,))
    
    completed_days = len(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        'completed_days': completed_days,
        'total_days': 100,
        'remaining': 100 - completed_days,
        'percentage': round((completed_days / 100 * 100), 1) if completed_days > 0 else 0
    })

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

