from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
import mysql.connector
import hashlib
import secrets
import json
from datetime import datetime
from aitesting import generate_feedback_summary
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_change_this'

def format_semester(semester_num):
    try:
        num = int(semester_num)
        return f"Semester {num}"
    except (ValueError, TypeError):
        return str(semester_num)

app.jinja_env.globals.update(format_semester=format_semester)

def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='DewangMYSQLC@270505',
            database='DBMSPROJ'
        )
    except mysql.connector.Error:
        return None


def run_query(query, params=None, *, fetchone=False, fetchall=False, dictionary=False, commit=False):
    conn = get_db_connection()
    if not conn:
        raise mysql.connector.Error('Unable to connect to database')

    cursor = conn.cursor(dictionary=dictionary)
    try:
        cursor.execute(query, params or ())

        if commit:
            conn.commit()

        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return None
    finally:
        cursor.close()
        conn.close()

def custom_hash(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + hashed.hex()

def verify_password(password, stored_hash):
    salt = stored_hash[:32]
    stored_password_hash = stored_hash[32:]
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return password_hash.hex() == stored_password_hash

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    user_type = request.form.get('user_type')
    user_id = request.form.get('email')
    password = request.form.get('password')
    
    if not user_id or not password or not user_type:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('login'))
    
    try:
        # Student login - only allow student credentials (block admin)
        if user_type == 'student':
            # Block admin credentials in student portal
            if user_id == 'admin' and password == 'admin123':
                flash('Admin credentials cannot be used in student portal', 'error')
                return redirect(url_for('login'))
                
            user = run_query("SELECT * FROM students WHERE email = %s OR student_id = %s",
                             (user_id, user_id), fetchone=True, dictionary=True)
            if user and verify_password(password, user['password_hash']):
                session['user_id'] = user['student_id']
                session['user_type'] = 'student'
                session['user_name'] = user['name']
                flash(f'Welcome {user["name"]}!', 'success')
                return redirect(url_for('student_dashboard'))

        # Faculty login - allow both faculty and admin credentials
        elif user_type == 'faculty':
            # Admin login through faculty portal
            if user_id == 'admin' and password == 'admin123':
                session['user_id'] = 'admin'
                session['user_type'] = 'admin'
                session['user_name'] = 'Administrator'
                flash('Welcome Administrator!', 'success')
                return redirect(url_for('admin_dashboard'))
            
            # Regular faculty login
            user = run_query("SELECT * FROM faculty WHERE email = %s OR faculty_id = %s",
                             (user_id, user_id), fetchone=True, dictionary=True)
            if user and verify_password(password, user['password_hash']):
                session['user_id'] = user['faculty_id']
                session['user_type'] = 'faculty'
                session['user_name'] = user['name']
                flash(f'Welcome {user["name"]}!', 'success')
                return redirect(url_for('faculty_dashboard'))

        # Admin portal selection (if you have it in dropdown)
        elif user_type == 'admin':
            if user_id == 'admin' and password == 'admin123':
                session['user_id'] = 'admin'
                session['user_type'] = 'admin'
                session['user_name'] = 'Administrator'
                flash('Welcome Administrator!', 'success')
                return redirect(url_for('admin_dashboard'))

        # Invalid user type
        else:
            flash('Invalid user type selected', 'error')
            return redirect(url_for('login'))

    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')

    flash('Invalid credentials for selected user type', 'error')
    return redirect(url_for('login'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    student_id = session['user_id']

    try:
        student = run_query(
            "SELECT student_id, name, program FROM students WHERE student_id = %s",
            (student_id,), fetchone=True, dictionary=True
        )
        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('login'))

        student_program = student['program']

        available_courses = run_query(
            """
            SELECT c.* FROM courses c 
            WHERE c.course_id NOT IN (
                SELECT e.course_id FROM enroll e WHERE e.student_id = %s
            )
            """,
            (student_id,), fetchall=True, dictionary=True
        )

        enrolled_courses = run_query(
            """
            SELECT c.*, f.name as faculty_name 
            FROM courses c
            JOIN enroll e ON c.course_id = e.course_id
            LEFT JOIN taughtby tb ON c.course_id = tb.course_id
            LEFT JOIN faculty f ON tb.faculty_id = f.faculty_id
            WHERE e.student_id = %s
            """,
            (student_id,), fetchall=True, dictionary=True
        )
        active_sessions = run_query(
            """
            SELECT fs.*, c.course_name, f.name AS faculty_name
            FROM feedbacksession fs
            JOIN enroll e ON fs.course_id = e.course_id
            LEFT JOIN courses c ON fs.course_id = c.course_id
            LEFT JOIN faculty f ON fs.faculty_id = f.faculty_id
            WHERE e.student_id = %s
              AND fs.start_date <= NOW()
              AND fs.end_date >= NOW()
            """,
            (student_id,), fetchall=True, dictionary=True
        )

        # Check which feedback sessions the student has already submitted
        submitted_sessions = set()
        if active_sessions:
            session_ids = [s['session_id'] for s in active_sessions]
            submitted_feedback = run_query(
                """
                SELECT DISTINCT session_id 
                FROM feedbackresponses 
                WHERE student_id = %s AND session_id IN ({})
                """.format(','.join(['%s'] * len(session_ids))),
                [student_id] + session_ids, fetchall=True, dictionary=True
            )
            submitted_sessions = {sf['session_id'] for sf in submitted_feedback}

        # Add submission status to active sessions
        for session_item in active_sessions:
            session_item['submitted'] = session_item['session_id'] in submitted_sessions

        # Fetch student grades
        student_grades = {}
        grades_data = run_query(
            """
            SELECT g.course_id, g.grade, g.date_assigned
            FROM grades g
            WHERE g.student_id = %s
            """,
            (student_id,), fetchall=True, dictionary=True
        )
        
        for grade in grades_data:
            student_grades[grade['course_id']] = grade

        # Prepare chart data for student dashboard (labels and numeric grade values)
        student_chart_labels = [c['course_code'] for c in (enrolled_courses or [])]
        # Map grade letters to numeric values for plotting
        grade_to_num = {'A+':95,'A':90,'B+':85,'B':80,'C':70,'F':50}
        student_chart_values = []
        for c in (enrolled_courses or []):
            g = student_grades.get(c['course_id'])
            if g and g.get('grade') in grade_to_num:
                student_chart_values.append(grade_to_num[g.get('grade')])
            else:
                student_chart_values.append(0)

    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('login'))

    return render_template('student_dashboard.html',
                           available_courses=available_courses,
                           enrolled_courses=enrolled_courses,
                           student_program=student_program,
                           active_sessions=active_sessions,
                           student_info=student,
                           student_grades=student_grades,
                           student_chart_labels=student_chart_labels,
                           student_chart_values=student_chart_values)

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return redirect(url_for('login'))
    
    faculty_id = session['user_id']

    try:
        taught_courses = run_query(
            """
            SELECT c.*, tb.semester
            FROM courses c
            JOIN taughtby tb ON c.course_id = tb.course_id
            WHERE tb.faculty_id = %s
            """,
            (faculty_id,), fetchall=True, dictionary=True
        )

        course_students = {}
        for course in taught_courses:
            course_students[course['course_id']] = run_query(
                """
                SELECT s.student_id, s.name, s.email, s.program
                FROM students s
                JOIN enroll e ON s.student_id = e.student_id
                WHERE e.course_id = %s
                """,
                (course['course_id'],), fetchall=True, dictionary=True
            )

        faculty_sessions = run_query(
            """
            SELECT fs.*, c.course_name
            FROM feedbacksession fs
            JOIN courses c ON fs.course_id = c.course_id
            WHERE fs.faculty_id = %s
            ORDER BY fs.start_date DESC
            """,
            (faculty_id,), fetchall=True, dictionary=True
        )

        faculty_info = run_query(
            "SELECT faculty_id, name, department FROM faculty WHERE faculty_id = %s",
            (faculty_id,), fetchone=True, dictionary=True
        )

        # Fetch existing grades for all students in faculty's courses
        student_grades = {}
        grades_data = run_query(
            """
            SELECT g.student_id, g.course_id, g.grade, g.date_assigned
            FROM grades g
            JOIN taughtby tb ON g.course_id = tb.course_id
            WHERE tb.faculty_id = %s
            """,
            (faculty_id,), fetchall=True, dictionary=True
        )
        
        for grade in grades_data:
            student_grades[(grade['student_id'], grade['course_id'])] = grade

        # Calculate grade distribution for charts
        grade_distribution = {}
        for course in taught_courses:
            course_id = course['course_id']
            course_grades = run_query(
                """
                SELECT grade, COUNT(*) as count
                FROM grades g
                WHERE g.course_id = %s AND g.faculty_id = %s
                GROUP BY grade
                ORDER BY grade
                """,
                (course_id, faculty_id), fetchall=True, dictionary=True
            )
            
            # Initialize all grades to 0
            distribution = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'F': 0}
            for grade_info in course_grades:
                distribution[grade_info['grade']] = grade_info['count']
            
            grade_distribution[course_id] = distribution

    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('login'))

    return render_template('faculty_dashboard.html',
                           taught_courses=taught_courses,
                           course_students=course_students,
                           faculty_sessions=faculty_sessions,
                           faculty_info=faculty_info,
                           student_grades=student_grades,
                           grade_distribution=grade_distribution)


@app.route('/faculty/grade_counts/<course_id>')
def faculty_grade_counts(course_id):
    # Return counts for each grade for a given course (faculty-only)
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return jsonify({'error': 'unauthorized'}), 403

    faculty_id = session.get('user_id')

    # verify faculty teaches the course
    ok = run_query(
        "SELECT 1 FROM taughtby WHERE faculty_id=%s AND course_id=%s LIMIT 1",
        (faculty_id, course_id), fetchone=True, dictionary=True
    )
    if not ok:
        return jsonify({'error': 'forbidden'}), 403

    try:
        rows = run_query(
            "SELECT grade, COUNT(*) AS cnt FROM grades WHERE course_id=%s GROUP BY grade",
            (course_id,), fetchall=True, dictionary=True
        ) or []

        grade_order = ['A+', 'A', 'B+', 'B', 'C', 'F']
        counts_map = {r['grade']: int(r['cnt']) for r in rows}
        counts = [counts_map.get(g, 0) for g in grade_order]

        return jsonify({'labels': grade_order, 'counts': counts})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


@app.route('/faculty/pass_fail/<course_id>')
def faculty_pass_fail(course_id):
    # Return pass/fail counts for a course (faculty-only)
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return jsonify({'error': 'unauthorized'}), 403

    faculty_id = session.get('user_id')

    # verify faculty teaches the course
    ok = run_query(
        "SELECT 1 FROM taughtby WHERE faculty_id=%s AND course_id=%s LIMIT 1",
        (faculty_id, course_id), fetchone=True, dictionary=True
    )
    if not ok:
        return jsonify({'error': 'forbidden'}), 403

    try:
        row_pass = run_query(
            "SELECT COUNT(*) AS cnt FROM grades WHERE course_id=%s AND grade != 'F'",
            (course_id,), fetchone=True, dictionary=True
        ) or {'cnt': 0}
        row_fail = run_query(
            "SELECT COUNT(*) AS cnt FROM grades WHERE course_id=%s AND grade = 'F'",
            (course_id,), fetchone=True, dictionary=True
        ) or {'cnt': 0}

        passed = int(row_pass['cnt'])
        failed = int(row_fail['cnt'])
        total = passed + failed
        passed_pct = round((passed / total) * 100, 1) if total > 0 else 0.0
        failed_pct = round((failed / total) * 100, 1) if total > 0 else 0.0

        return jsonify({'passed': passed, 'failed': failed, 'total': total, 'passed_pct': passed_pct, 'failed_pct': failed_pct})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/assign_grade', methods=['POST'])
def assign_grade():
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return redirect(url_for('login'))
    
    faculty_id = session['user_id']
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    grade = request.form.get('grade')
    
    if not all([student_id, course_id, grade]):
        flash('All fields are required!', 'error')
        return redirect(url_for('faculty_dashboard'))
    
    try:
        # Verify that the faculty teaches this course
        course_check = run_query(
            "SELECT COUNT(*) as count FROM taughtby WHERE faculty_id = %s AND course_id = %s",
            (faculty_id, course_id), fetchone=True, dictionary=True
        )
        
        if course_check['count'] == 0:
            flash('You are not authorized to grade this course!', 'error')
            return redirect(url_for('faculty_dashboard'))
        
        # Verify that the student is enrolled in this course
        enrollment_check = run_query(
            "SELECT COUNT(*) as count FROM enroll WHERE student_id = %s AND course_id = %s",
            (student_id, course_id), fetchone=True, dictionary=True
        )
        
        if enrollment_check['count'] == 0:
            flash('Student is not enrolled in this course!', 'error')
            return redirect(url_for('faculty_dashboard'))
        
        # Check if grade already exists
        existing_grade = run_query(
            "SELECT COUNT(*) as count FROM grades WHERE student_id = %s AND course_id = %s",
            (student_id, course_id), fetchone=True, dictionary=True
        )
        
        if existing_grade['count'] > 0:
            # Update existing grade
            run_query(
                "UPDATE grades SET grade = %s, faculty_id = %s, date_assigned = CURRENT_TIMESTAMP WHERE student_id = %s AND course_id = %s",
                (grade, faculty_id, student_id, course_id),
                commit=True
            )
            flash(f'Grade updated successfully for student {student_id}!', 'success')
        else:
            # Insert new grade
            run_query(
                "INSERT INTO grades (student_id, course_id, faculty_id, grade) VALUES (%s, %s, %s, %s)",
                (student_id, course_id, faculty_id, grade),
                commit=True
            )
            flash(f'Grade assigned successfully for student {student_id}!', 'success')
            
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
    
    return redirect(url_for('faculty_dashboard'))

@app.route('/export_grades')
def export_grades():
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return redirect(url_for('login'))
    
    faculty_id = session['user_id']
    course_id = request.args.get('course_id')
    format_type = request.args.get('format', 'csv')
    
    if not course_id:
        flash('Course ID is required!', 'error')
        return redirect(url_for('faculty_dashboard'))
    
    try:
        # Verify faculty teaches this course
        course_check = run_query(
            "SELECT COUNT(*) as count FROM taughtby WHERE faculty_id = %s AND course_id = %s",
            (faculty_id, course_id), fetchone=True, dictionary=True
        )
        
        if course_check['count'] == 0:
            flash('You are not authorized to export grades for this course!', 'error')
            return redirect(url_for('faculty_dashboard'))
        
        # Get course info
        course_info = run_query(
            "SELECT course_name, course_code FROM courses WHERE course_id = %s",
            (course_id,), fetchone=True, dictionary=True
        )
        
        # Get grades data
        grades_data = run_query(
            """
            SELECT s.student_id, s.name, s.program, 
                   COALESCE(g.grade, 'NP') as grade
            FROM students s
            JOIN enroll e ON s.student_id = e.student_id
            LEFT JOIN grades g ON s.student_id = g.student_id AND g.course_id = %s
            WHERE e.course_id = %s
            ORDER BY s.student_id
            """,
            (course_id, course_id), fetchall=True, dictionary=True
        )
        
        if format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Student ID', 'Student Name', 'Program', 'Grade'])
            
            # Write data
            for row in grades_data:
                writer.writerow([
                    row['student_id'],
                    row['name'],
                    row['program'],
                    row['grade']
                ])
            
            output.seek(0)
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=grades_{course_info["course_code"]}_{course_id}.csv'
                }
            )
        else:
            flash('Only CSV export is supported!', 'error')
            return redirect(url_for('faculty_dashboard'))
    
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('faculty_dashboard'))

@app.route('/export_student_grades')
def export_student_grades():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    format_type = request.args.get('format', 'csv')
    
    try:
        # Get student info
        student_info = run_query(
            "SELECT name, program FROM students WHERE student_id = %s",
            (student_id,), fetchone=True, dictionary=True
        )
        
        # Get grades data
        grades_data = run_query(
            """
            SELECT c.course_code, c.course_name, f.name as faculty_name,
                   COALESCE(g.grade, 'NP') as grade
            FROM courses c
            JOIN enroll e ON c.course_id = e.course_id
            LEFT JOIN grades g ON c.course_id = g.course_id AND g.student_id = %s
            LEFT JOIN taughtby tb ON c.course_id = tb.course_id
            LEFT JOIN faculty f ON tb.faculty_id = f.faculty_id
            WHERE e.student_id = %s
            ORDER BY c.course_code
            """,
            (student_id, student_id), fetchall=True, dictionary=True
        )
        
        if format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Course Code', 'Course Name', 'Faculty', 'Grade'])
            
            # Write data
            for row in grades_data:
                writer.writerow([
                    row['course_code'],
                    row['course_name'],
                    row['faculty_name'] or 'Not Assigned',
                    row['grade']
                ])
            
            output.seek(0)
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=my_grades_{student_id}.csv'
                }
            )
        else:
            flash('Only CSV export is supported!', 'error')
            return redirect(url_for('student_dashboard'))
    
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('student_dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    try:
        students = run_query("SELECT * FROM students ORDER BY student_id", fetchall=True, dictionary=True)
        faculty = run_query("SELECT * FROM faculty ORDER BY faculty_id", fetchall=True, dictionary=True)
        courses = run_query("SELECT * FROM courses ORDER BY course_id", fetchall=True, dictionary=True)
        assignments = run_query(
            """
            SELECT tb.*, f.name as faculty_name, c.course_name 
            FROM taughtby tb
            JOIN faculty f ON tb.faculty_id = f.faculty_id
            JOIN courses c ON tb.course_id = c.course_id
            """,
            fetchall=True, dictionary=True
        )
        sessions = run_query(
            """
            SELECT fs.*, c.course_name, f.name AS faculty_name
            FROM feedbacksession fs
            LEFT JOIN courses c ON fs.course_id = c.course_id
            LEFT JOIN faculty f ON fs.faculty_id = f.faculty_id
            ORDER BY fs.start_date DESC
            """,
            fetchall=True, dictionary=True
        )
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('login'))

    return render_template('admin_dashboard.html',
                           students=students,
                           faculty=faculty,
                           courses=courses,
                           assignments=assignments,
                           sessions=sessions)

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    student_id = request.form.get('student_id')
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    program = request.form.get('program')
    
    if not all([student_id, name, email, password, program]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))
    
    password_hash = custom_hash(password)
    
    try:
        run_query(
            """
            INSERT INTO students (student_id, name, email, password_hash, program)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (student_id, name, email, password_hash, program),
            commit=True
        )
        flash('Student added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding student: {err}', 'error')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_student', methods=['POST'])
def edit_student():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    student_id = request.form.get('student_id')
    name = request.form.get('name')
    email = request.form.get('email')
    program = request.form.get('program')

    if not all([student_id, name, email, program]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        run_query("UPDATE students SET name=%s, email=%s, program=%s WHERE student_id=%s",
                  (name, email, program, student_id), commit=True)
        flash('Student updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating student: {err}', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_student/<student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    try:
        run_query("DELETE FROM students WHERE student_id=%s", (student_id,), commit=True)
        flash('Student deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting student: {err}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/add_faculty', methods=['POST'])
def add_faculty():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    faculty_id = request.form.get('faculty_id')
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    department = request.form.get('department')
    
    if not all([faculty_id, name, email, password, department]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))
    
    password_hash = custom_hash(password)
    
    try:
        run_query(
            """
            INSERT INTO faculty (faculty_id, name, email, password_hash, department)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (faculty_id, name, email, password_hash, department),
            commit=True
        )
        flash('Faculty added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding faculty: {err}', 'error')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_faculty', methods=['POST'])
def edit_faculty():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    faculty_id = request.form.get('faculty_id')
    name = request.form.get('name')
    email = request.form.get('email')
    department = request.form.get('department')

    if not all([faculty_id, name, email, department]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        run_query("UPDATE faculty SET name=%s, email=%s, department=%s WHERE faculty_id=%s",
                  (name, email, department, faculty_id), commit=True)
        flash('Faculty updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating faculty: {err}', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_faculty/<faculty_id>', methods=['POST'])
def delete_faculty(faculty_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    try:
        run_query("DELETE FROM faculty WHERE faculty_id=%s", (faculty_id,), commit=True)
        flash('Faculty deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting faculty: {err}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/add_course', methods=['POST'])
def add_course():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    course_name = request.form.get('course_name')
    course_code = request.form.get('course_code')
    semester = request.form.get('semester')
    
    if not all([course_id, course_name, course_code, semester]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        run_query(
            """
            INSERT INTO courses (course_id, course_name, course_code, semester)
            VALUES (%s, %s, %s, %s)
            """,
            (course_id, course_name, course_code, semester),
            commit=True
        )
        flash('Course added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding course: {err}', 'error')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_course', methods=['POST'])
def edit_course():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    course_id = request.form.get('course_id')
    course_name = request.form.get('course_name')
    course_code = request.form.get('course_code')
    semester = request.form.get('semester')

    if not all([course_id, course_name, course_code, semester]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        run_query("UPDATE courses SET course_name=%s, course_code=%s, semester=%s WHERE course_id=%s",
                  (course_name, course_code, semester, course_id), commit=True)
        flash('Course updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating course: {err}', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_course/<course_id>', methods=['POST'])
def delete_course(course_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    try:
        run_query("DELETE FROM courses WHERE course_id=%s", (course_id,), commit=True)
        flash('Course deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting course: {err}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/assign_faculty', methods=['POST'])
def assign_faculty():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    faculty_id = request.form.get('faculty_id')
    course_id = request.form.get('course_id')
    semester = request.form.get('semester')
    
    if not all([faculty_id, course_id, semester]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        run_query(
            """
            INSERT INTO taughtby (faculty_id, course_id, semester)
            VALUES (%s, %s, %s)
            """,
            (faculty_id, course_id, semester),
            commit=True
        )
        flash('Faculty assigned to course successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error assigning faculty: {err}', 'error')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_assignment', methods=['POST'])
def edit_assignment():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    faculty_id = request.form.get('faculty_id')
    course_id = request.form.get('course_id')
    semester = request.form.get('semester')

    if not all([faculty_id, course_id, semester]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        run_query("UPDATE taughtby SET semester=%s WHERE faculty_id=%s AND course_id=%s",
                  (semester, faculty_id, course_id), commit=True)
        flash('Assignment updated successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating assignment: {err}', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_assignment', methods=['POST'])
def delete_assignment():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    faculty_id = request.form.get('faculty_id')
    course_id = request.form.get('course_id')
    try:
        run_query("DELETE FROM taughtby WHERE faculty_id=%s AND course_id=%s",
                  (faculty_id, course_id), commit=True)
        flash('Assignment removed', 'success')
    except mysql.connector.Error as err:
        flash(f'Error removing assignment: {err}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/enroll_course', methods=['POST'])
def enroll_course():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    student_id = session['user_id']
    
    print(f"🔍 Enrollment attempt - Student: {student_id}, Course: {course_id}")

    if not course_id:
        flash('Please select a course', 'error')
        return redirect(url_for('student_dashboard'))
    
    try:
        result = run_query(
            """
            SELECT COUNT(*) FROM enroll 
            WHERE student_id = %s AND course_id = %s
            """,
            (student_id, course_id), fetchone=True
        )

        if result and result[0] > 0:
            flash('You are already enrolled in this course!', 'warning')
        else:
            run_query(
                """
                INSERT INTO enroll (student_id, course_id)
                VALUES (%s, %s)
                """,
                (student_id, course_id), commit=True
            )
            flash('Successfully enrolled in course!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error enrolling: {err}', 'error')
    
    return redirect(url_for('student_dashboard'))


@app.route('/create_feedback_session', methods=['POST'])
def create_feedback_session():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    session_id = request.form.get('session_id')
    course_id = request.form.get('course_id')
    faculty_id = request.form.get('faculty_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not all([session_id, course_id, faculty_id, start_date, end_date]):
        flash('Please fill in all fields for the feedback session', 'error')
        return redirect(url_for('admin_dashboard'))

    # Validate datetimes
    try:
        sd = datetime.fromisoformat(start_date)
        ed = datetime.fromisoformat(end_date)
        if ed <= sd:
            flash('End date must be after start date', 'error')
            return redirect(url_for('admin_dashboard'))
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DDTHH:MM:SS', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        run_query(
            "INSERT INTO feedbacksession (session_id, course_id, faculty_id, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (session_id, course_id, faculty_id, sd, ed, 'Active'),
            commit=True
        )
        flash('Feedback session created successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error creating session: {err}', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/faculty_create_feedback_session', methods=['POST'])
def faculty_create_feedback_session():
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return redirect(url_for('login'))

    faculty_id = session['user_id']
    session_id = request.form.get('session_id')
    course_id = request.form.get('course_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not all([session_id, course_id, start_date, end_date]):
        flash('Please fill in all fields for the feedback session', 'error')
        return redirect(url_for('faculty_dashboard'))

    try:
        taught = run_query("SELECT 1 FROM taughtby WHERE faculty_id=%s AND course_id=%s",
                           (faculty_id, course_id), fetchone=True)
        if not taught:
            flash('You can only create sessions for courses you teach', 'error')
            return redirect(url_for('faculty_dashboard'))
    except mysql.connector.Error as err:
        flash(f'Error creating session: {err}', 'error')
        return redirect(url_for('faculty_dashboard'))

    try:
        sd = datetime.fromisoformat(start_date)
        ed = datetime.fromisoformat(end_date)
        if ed <= sd:
            flash('End date must be after start date', 'error')
            return redirect(url_for('faculty_dashboard'))
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DDTHH:MM', 'error')
        return redirect(url_for('faculty_dashboard'))

    try:
        run_query(
            "INSERT INTO feedbacksession (session_id, course_id, faculty_id, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (session_id, course_id, faculty_id, sd, ed, 'Active'),
            commit=True
        )
        flash('Feedback session created successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error creating session: {err}', 'error')

    return redirect(url_for('faculty_dashboard'))


@app.route('/feedback_form/<session_id>', methods=['GET'])
def feedback_form(session_id):
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))

    student_id = session['user_id']
    try:
        fs = run_query("SELECT * FROM feedbacksession WHERE session_id = %s", (session_id,),
                       fetchone=True, dictionary=True)
        if not fs:
            flash('Feedback session not found', 'error')
            return redirect(url_for('student_dashboard'))

        now = datetime.now()
        start = fs['start_date']
        end = fs['end_date']

        if not (start <= now <= end):
            flash('This feedback form is not currently open', 'error')
            return redirect(url_for('student_dashboard'))

        # Check if student has already submitted feedback for this session
        existing_feedback = run_query(
            "SELECT COUNT(*) as count FROM feedbackresponses WHERE student_id = %s AND session_id = %s",
            (student_id, session_id), fetchone=True, dictionary=True
        )
        
        if existing_feedback['count'] > 0:
            # Student has already submitted feedback
            return render_template('feedback_submitted.html', session=fs)

        questions = run_query("SELECT * FROM feedbackquestions ORDER BY question_id LIMIT 10",
                              fetchall=True, dictionary=True)

        remarks = run_query("SELECT * FROM feedbackremarks WHERE student_id=%s AND session_id=%s",
                             (student_id, session_id), fetchone=True, dictionary=True)

        return render_template('feedback_form.html', session=fs, questions=questions, remarks=remarks)
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('student_dashboard'))


@app.route('/submit_feedback/<session_id>', methods=['POST'])
def submit_feedback(session_id):
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))

    student_id = session['user_id']
    try:
        course_id = request.form.get('course_id')
        faculty_id = request.form.get('faculty_id')
        if not course_id or not faculty_id:
            row = run_query("SELECT course_id, faculty_id FROM feedbacksession WHERE session_id=%s",
                            (session_id,), fetchone=True)
            if row:
                course_id = course_id or row[0]
                faculty_id = faculty_id or row[1]

        if not course_id or not faculty_id:
            flash('Unable to determine course or faculty for this feedback session.', 'error')
            return redirect(url_for('student_dashboard'))

        for i in range(1, 11):
            qid = request.form.get(f'question_{i}_id')
            rating = request.form.get(f'question_{i}')
            if qid and rating:
                resp_id = f"{session_id}_{student_id}_{i}"
                try:
                    run_query(
                        "INSERT INTO feedbackresponses (response_id, student_id, session_id, course_id, faculty_id, question_id, rating) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (resp_id, student_id, session_id, course_id, faculty_id, qid, int(rating)),
                        commit=True
                    )
                except mysql.connector.IntegrityError:
                    pass

        comments = request.form.get('comments')

        try:
            run_query(
                "INSERT INTO feedbackremarks (student_id, session_id, comments) VALUES (%s,%s,%s)",
                (student_id, session_id, comments),
                commit=True
            )
        except mysql.connector.IntegrityError:
            run_query(
                "UPDATE feedbackremarks SET comments=%s WHERE student_id=%s AND session_id=%s",
                (comments, student_id, session_id),
                commit=True
            )

        flash('Feedback submitted. Thank you!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error submitting feedback: {err}', 'error')

    return redirect(url_for('student_dashboard'))


@app.route('/admin_feedback_report/<session_id>')
def admin_feedback_report(session_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    try:
        fs = run_query(
            """
            SELECT fs.*, c.course_name, f.name AS faculty_name
            FROM feedbacksession fs
            LEFT JOIN courses c ON fs.course_id = c.course_id
            LEFT JOIN faculty f ON fs.faculty_id = f.faculty_id
            WHERE fs.session_id=%s
            """,
            (session_id,), fetchone=True, dictionary=True
        )
        if not fs:
            flash('Feedback session not found', 'error')
            return redirect(url_for('admin_dashboard'))

        per_question = run_query(
            "SELECT question_id, AVG(rating) as avg_rating FROM feedbackresponses WHERE session_id=%s GROUP BY question_id",
            (session_id,), fetchall=True, dictionary=True
        )
        student_averages = run_query(
            """
            SELECT fr.student_id,
                   s.name AS student_name,
                   AVG(fr.rating) AS average_rating
            FROM feedbackresponses fr
            LEFT JOIN students s ON fr.student_id = s.student_id
            WHERE fr.session_id=%s
            GROUP BY fr.student_id, s.name
            ORDER BY s.name
            """,
            (session_id,), fetchall=True, dictionary=True
        )
        overall_avg = None
        if student_averages:
            ratings = [row['average_rating'] for row in student_averages if row['average_rating'] is not None]
            if ratings:
                overall_avg = sum(ratings) / len(ratings)
        response_details = run_query(
            """
            SELECT fr.question_id, fr.rating, fr.student_id, s.name AS student_name
            FROM feedbackresponses fr
            LEFT JOIN students s ON fr.student_id = s.student_id
            WHERE fr.session_id=%s
            ORDER BY fr.student_id, fr.question_id
            """,
            (session_id,), fetchall=True, dictionary=True
        )
        remarks = run_query(
            """
            SELECT fr.*, s.name AS student_name
            FROM feedbackremarks fr
            LEFT JOIN students s ON fr.student_id = s.student_id
            WHERE fr.session_id=%s
            """,
            (session_id,), fetchall=True, dictionary=True
        )

        return render_template('feedback_report.html', session=fs, per_question=per_question, overall_avg=overall_avg,
                               remarks=remarks, response_details=response_details, student_averages=student_averages)
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/close_feedback_session/<session_id>', methods=['POST'])
def close_feedback_session(session_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    try:
        run_query("UPDATE feedbacksession SET status=%s WHERE session_id=%s",
                  ('Closed', session_id), commit=True)
        flash('Session closed successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error closing session: {err}', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_feedback_session/<session_id>', methods=['POST'])
def delete_feedback_session(session_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    try:
        # Remove dependent feedback data first to avoid FK issues and to make deletion explicit
        run_query("DELETE FROM feedbackresponses WHERE session_id=%s", (session_id,), commit=True)
        run_query("DELETE FROM feedbackremarks WHERE session_id=%s", (session_id,), commit=True)
        # Remove any evaluation / AI reports related to this session
        run_query("DELETE FROM evaluationreport WHERE session_id=%s", (session_id,), commit=True)
        # Finally remove the session itself
        run_query("DELETE FROM feedbacksession WHERE session_id=%s", (session_id,), commit=True)
        flash('Feedback session and all associated responses were deleted', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting feedback session: {err}', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/faculty_feedback_report/<session_id>')
def faculty_feedback_report(session_id):
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return redirect(url_for('login'))

    faculty_id = session['user_id']
    try:
        # Get session details
        fs = run_query(
            """
            SELECT fs.*, c.course_name
            FROM feedbacksession fs
            LEFT JOIN courses c ON fs.course_id = c.course_id
            WHERE fs.session_id=%s AND fs.faculty_id=%s
            """,
            (session_id, faculty_id), fetchone=True, dictionary=True
        )
        
        if not fs:
            flash('Feedback session not found', 'error')
            return redirect(url_for('faculty_dashboard'))

        # Check if feedback session has responses
        response_count = run_query(
            "SELECT COUNT(*) as count FROM feedbackremarks WHERE session_id=%s",
            (session_id,), fetchone=True, dictionary=True
        )
        
        if not response_count or response_count['count'] == 0:
            ai_summary = None
            parsed_summary = None
        else:
            # Generate AI summary of student comments
            ai_summary_raw = generate_feedback_summary(session_id)
            
            # Try to parse JSON response
            try:
                parsed_summary = json.loads(ai_summary_raw)
                ai_summary = ai_summary_raw  # Keep raw for fallback
            except json.JSONDecodeError as e:
                # Fallback to raw text if JSON parsing fails
                print(f"JSON parsing failed: {e}")
                print(f"Raw response: {ai_summary_raw}")
                parsed_summary = None
                ai_summary = ai_summary_raw

        return render_template('faculty_ai_summary.html', 
                             session=fs, 
                             ai_summary=ai_summary,
                             parsed_summary=parsed_summary,
                             response_count=response_count['count'] if response_count else 0)
                             
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('faculty_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)