from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration - use Supabase if DATABASE_URL is set, otherwise use SQLite for local dev
DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_SUPABASE = DATABASE_URL and 'supabase.co' in DATABASE_URL and not DATABASE_URL.startswith('db.xxx')

# SQLite fallback for local development
DB_FILE = '100day_challenge.db'

def get_db_connection():
    """Get database connection - Supabase PostgreSQL or SQLite fallback"""
    if USE_SUPABASE:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(DATABASE_URL)
            return conn, 'postgresql'
        except Exception as e:
            print(f"Warning: Could not connect to Supabase: {e}")
            print("Falling back to SQLite for local development")
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            return conn, 'sqlite'
    else:
        # Use SQLite for local development
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

def get_cursor(conn, db_type):
    """Get cursor with appropriate factory"""
    if db_type == 'postgresql':
        from psycopg2.extras import RealDictCursor
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def execute_query(cursor, query, params, db_type):
    """Execute query with correct placeholder style"""
    if db_type == 'postgresql':
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
    else:
        # Convert %s to ? for SQLite
        sqlite_query = query.replace('%s', '?')
        if params:
            cursor.execute(sqlite_query, params)
        else:
            cursor.execute(sqlite_query)

def init_db():
    """Initialize database with tasks table"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if db_type == 'postgresql':
            # PostgreSQL/Supabase schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks_list (
                    id SERIAL PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    task_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_tasks (
                    id SERIAL PRIMARY KEY,
                    day_number INTEGER NOT NULL,
                    task_id INTEGER NOT NULL,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY (task_id) REFERENCES tasks_list(id) ON DELETE CASCADE,
                    UNIQUE(day_number, task_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS day_notes (
                    id SERIAL PRIMARY KEY,
                    day_number INTEGER NOT NULL UNIQUE,
                    date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # SQLite schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    task_order INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day_number INTEGER NOT NULL,
                    task_id INTEGER NOT NULL,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY (task_id) REFERENCES tasks_list(id),
                    UNIQUE(day_number, task_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS day_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day_number INTEGER NOT NULL UNIQUE,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        conn.commit()
    except Exception as e:
        if db_type == 'postgresql':
            conn.rollback()
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def index():
    """Main calendar view"""
    return render_template('index.html')

@app.route('/api/tasks-list', methods=['GET'])
def get_tasks_list():
    """Get all tasks in the list"""
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    execute_query(cursor, 'SELECT id, task_name, task_order FROM tasks_list ORDER BY task_order, id', [], db_type)
    tasks = cursor.fetchall()
    cursor.close()
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
    
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    execute_query(cursor, 'SELECT MAX(task_order) as max_order FROM tasks_list', [], db_type)
    result = cursor.fetchone()
    max_order = result['max_order'] if result and result['max_order'] else 0
    
    if db_type == 'postgresql':
        execute_query(cursor, '''
            INSERT INTO tasks_list (task_name, task_order)
            VALUES (%s, %s)
            RETURNING id
        ''', (task_name, max_order + 1), db_type)
        task_id = cursor.fetchone()['id']
    else:
        execute_query(cursor, '''
            INSERT INTO tasks_list (task_name, task_order)
            VALUES (?, ?)
        ''', (task_name, max_order + 1), db_type)
        task_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'id': task_id, 'task_name': task_name, 'task_order': max_order + 1})

@app.route('/api/tasks-list/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task name"""
    data = request.json
    task_name = data.get('task_name', '').strip()
    
    if not task_name:
        return jsonify({'error': 'task_name is required'}), 400
    
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    execute_query(cursor, 'UPDATE tasks_list SET task_name = %s WHERE id = %s', (task_name, task_id), db_type)
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/tasks-list/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task from the list"""
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    # CASCADE will handle daily_tasks deletion for PostgreSQL
    # For SQLite, need to delete manually
    if db_type == 'sqlite':
        execute_query(cursor, 'DELETE FROM daily_tasks WHERE task_id = ?', (task_id,), db_type)
    execute_query(cursor, 'DELETE FROM tasks_list WHERE id = %s', (task_id,), db_type)
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/days/<int:day_number>', methods=['GET'])
def get_day_tasks(day_number):
    """Get tasks status for a specific day"""
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    
    # Get all tasks
    execute_query(cursor, 'SELECT id, task_name FROM tasks_list ORDER BY task_order, id', [], db_type)
    all_tasks = cursor.fetchall()
    
    # Get completed tasks for this day
    execute_query(cursor, '''
        SELECT task_id FROM daily_tasks 
        WHERE day_number = %s AND completed = 1
    ''', (day_number,), db_type)
    completed_tasks = {row['task_id'] for row in cursor.fetchall()}
    
    # Get notes for this day
    execute_query(cursor, 'SELECT notes FROM day_notes WHERE day_number = %s', (day_number,), db_type)
    notes_row = cursor.fetchone()
    notes = notes_row['notes'] if notes_row else ''
    
    cursor.close()
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
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    
    # Get total number of tasks
    execute_query(cursor, 'SELECT COUNT(*) as total FROM tasks_list', [], db_type)
    result = cursor.fetchone()
    total_tasks = result['total'] if result else 0
    
    # Get completed tasks count for each day
    execute_query(cursor, '''
        SELECT day_number, COUNT(*) as completed_count
        FROM daily_tasks
        WHERE completed = 1
        GROUP BY day_number
    ''', [], db_type)
    completed_by_day = {row['day_number']: row['completed_count'] for row in cursor.fetchall()}
    
    cursor.close()
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
    
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    
    if db_type == 'postgresql':
        execute_query(cursor, '''
            INSERT INTO daily_tasks (day_number, task_id, completed)
            VALUES (%s, %s, %s)
            ON CONFLICT (day_number, task_id) 
            DO UPDATE SET completed = EXCLUDED.completed
        ''', (day_number, task_id, 1 if completed else 0), db_type)
    else:
        execute_query(cursor, '''
            INSERT OR REPLACE INTO daily_tasks (day_number, task_id, completed)
            VALUES (?, ?, ?)
        ''', (day_number, task_id, 1 if completed else 0), db_type)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/days/<int:day_number>/notes', methods=['POST'])
def update_day_notes(day_number):
    """Update notes for a specific day"""
    data = request.json
    notes = data.get('notes', '')
    
    start_date = datetime.now().date()
    task_date = start_date + timedelta(days=day_number - 1)
    
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    
    if db_type == 'postgresql':
        execute_query(cursor, '''
            INSERT INTO day_notes (day_number, date, notes)
            VALUES (%s, %s, %s)
            ON CONFLICT (day_number) 
            DO UPDATE SET notes = EXCLUDED.notes, date = EXCLUDED.date
        ''', (day_number, task_date, notes), db_type)
    else:
        # SQLite uses TEXT for date, convert to string
        execute_query(cursor, '''
            INSERT OR REPLACE INTO day_notes (day_number, date, notes)
            VALUES (?, ?, ?)
        ''', (day_number, task_date.isoformat(), notes), db_type)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    conn, db_type = get_db_connection()
    cursor = get_cursor(conn, db_type)
    
    # Get total number of tasks
    execute_query(cursor, 'SELECT COUNT(*) as total FROM tasks_list', [], db_type)
    result = cursor.fetchone()
    total_tasks = result['total'] if result else 0
    
    if total_tasks == 0:
        cursor.close()
        conn.close()
        return jsonify({
            'completed_days': 0,
            'total_days': 100,
            'remaining': 100,
            'percentage': 0
        })
    
    # Count days with all tasks completed
    execute_query(cursor, '''
        SELECT dt.day_number, 
               COUNT(DISTINCT dt.task_id) as completed_count
        FROM daily_tasks dt
        WHERE dt.completed = 1
        GROUP BY dt.day_number
        HAVING COUNT(DISTINCT dt.task_id) = %s
    ''', (total_tasks,), db_type)
    
    completed_days = len(cursor.fetchall())
    
    cursor.close()
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

