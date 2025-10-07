from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import hashlib
import secrets
from datetime import datetime

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
            password='Saran123$',
            database='DBMSPROJ'
        )
    except mysql.connector.Error:
        return None

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
    
    if not user_id or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('login'))
    
    if user_id == 'admin' and password == 'admin123':
        session['user_id'] = 'admin'
        session['user_type'] = 'admin'
        session['user_name'] = 'Administrator'
        flash('Welcome Administrator!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if user_type == 'student':
                cursor.execute("SELECT * FROM students WHERE email = %s OR student_id = %s", (user_id, user_id))
                user = cursor.fetchone()
                if user and verify_password(password, user['password_hash']):
                    session['user_id'] = user['student_id']
                    session['user_type'] = 'student'
                    session['user_name'] = user['name']
                    flash(f'Welcome {user["name"]}!', 'success')
                    return redirect(url_for('student_dashboard'))
            
            elif user_type == 'faculty':
                cursor.execute("SELECT * FROM faculty WHERE email = %s OR faculty_id = %s", (user_id, user_id))
                user = cursor.fetchone()
                if user and verify_password(password, user['password_hash']):
                    session['user_id'] = user['faculty_id']
                    session['user_type'] = 'faculty'
                    session['user_name'] = user['name']
                    flash(f'Welcome {user["name"]}!', 'success')
                    return redirect(url_for('faculty_dashboard'))
            
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    flash('Invalid credentials', 'error')
    return redirect(url_for('login'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT program FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            
            if not student:
                flash('Student not found', 'error')
                return redirect(url_for('login'))
            
            student_program = student['program']
            
            cursor.execute("""
                SELECT c.* FROM courses c 
                WHERE c.course_id NOT IN (
                    SELECT e.course_id FROM enroll e WHERE e.student_id = %s
                )
            """, (student_id,))
            available_courses = cursor.fetchall()
            
            cursor.execute("""
                SELECT c.*, f.name as faculty_name 
                FROM courses c
                JOIN enroll e ON c.course_id = e.course_id
                LEFT JOIN taughtby tb ON c.course_id = tb.course_id
                LEFT JOIN faculty f ON tb.faculty_id = f.faculty_id
                WHERE e.student_id = %s
            """, (student_id,))
            enrolled_courses = cursor.fetchall()

            # Fetch active feedback sessions for the student's enrolled courses
            cursor.execute("SELECT fs.* FROM feedbacksession fs JOIN enroll e ON fs.course_id = e.course_id WHERE e.student_id = %s AND fs.start_date <= NOW() AND fs.end_date >= NOW()", (student_id,))
            active_sessions = cursor.fetchall()
            
            return render_template('student_dashboard.html', 
                                 available_courses=available_courses,
                                 enrolled_courses=enrolled_courses,
                                 student_program=student_program,
                                 active_sessions=active_sessions)
        finally:
            cursor.close()
            conn.close()

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'faculty':
        return redirect(url_for('login'))
    
    faculty_id = session['user_id']
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT c.*, tb.semester
                FROM courses c
                JOIN taughtby tb ON c.course_id = tb.course_id
                WHERE tb.faculty_id = %s
            """, (faculty_id,))
            taught_courses = cursor.fetchall()
            
            course_students = {}
            for course in taught_courses:
                cursor.execute("""
                    SELECT s.student_id, s.name, s.email, s.program
                    FROM students s
                    JOIN enroll e ON s.student_id = e.student_id
                    WHERE e.course_id = %s
                """, (course['course_id'],))
                course_students[course['course_id']] = cursor.fetchall()
            
            return render_template('faculty_dashboard.html', 
                                 taught_courses=taught_courses,
                                 course_students=course_students)
        finally:
            cursor.close()
            conn.close()

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM students ORDER BY student_id")
            students = cursor.fetchall()
            
            cursor.execute("SELECT * FROM faculty ORDER BY faculty_id")
            faculty = cursor.fetchall()
            
            cursor.execute("SELECT * FROM courses ORDER BY course_id")
            courses = cursor.fetchall()
            
            cursor.execute("""
                SELECT tb.*, f.name as faculty_name, c.course_name 
                FROM taughtby tb
                JOIN faculty f ON tb.faculty_id = f.faculty_id
                JOIN courses c ON tb.course_id = c.course_id
            """)
            assignments = cursor.fetchall()

            # Fetch all feedback sessions for admin view
            cursor.execute("SELECT * FROM feedbacksession ORDER BY start_date DESC")
            sessions = cursor.fetchall()
            
            return render_template('admin_dashboard.html', 
                                 students=students, 
                                 faculty=faculty, 
                                 courses=courses, 
                                 assignments=assignments,
                                 sessions=sessions)
        finally:
            cursor.close()
            conn.close()

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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO students (student_id, name, email, password_hash, program)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, name, email, password_hash, program))
        conn.commit()
        flash('Student added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding student: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
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

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE students SET name=%s, email=%s, program=%s WHERE student_id=%s",
                       (name, email, program, student_id))
        conn.commit()
        flash('Student updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating student: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_student/<student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
        conn.commit()
        flash('Student deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting student: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO faculty (faculty_id, name, email, password_hash, department)
            VALUES (%s, %s, %s, %s, %s)
        """, (faculty_id, name, email, password_hash, department))
        conn.commit()
        flash('Faculty added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding faculty: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
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

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE faculty SET name=%s, email=%s, department=%s WHERE faculty_id=%s",
                       (name, email, department, faculty_id))
        conn.commit()
        flash('Faculty updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating faculty: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_faculty/<faculty_id>', methods=['POST'])
def delete_faculty(faculty_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM faculty WHERE faculty_id=%s", (faculty_id,))
        conn.commit()
        flash('Faculty deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting faculty: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO courses (course_id, course_name, course_code, semester)
            VALUES (%s, %s, %s, %s)
        """, (course_id, course_name, course_code, semester))
        conn.commit()
        flash('Course added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding course: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
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

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE courses SET course_name=%s, course_code=%s, semester=%s WHERE course_id=%s",
                       (course_name, course_code, semester, course_id))
        conn.commit()
        flash('Course updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating course: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_course/<course_id>', methods=['POST'])
def delete_course(course_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM courses WHERE course_id=%s", (course_id,))
        conn.commit()
        flash('Course deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting course: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO taughtby (faculty_id, course_id, semester)
            VALUES (%s, %s, %s)
        """, (faculty_id, course_id, semester))
        conn.commit()
        flash('Faculty assigned to course successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error assigning faculty: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
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

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE taughtby SET semester=%s WHERE faculty_id=%s AND course_id=%s", (semester, faculty_id, course_id))
        conn.commit()
        flash('Assignment updated successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating assignment: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_assignment', methods=['POST'])
def delete_assignment():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    faculty_id = request.form.get('faculty_id')
    course_id = request.form.get('course_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM taughtby WHERE faculty_id=%s AND course_id=%s", (faculty_id, course_id))
        conn.commit()
        flash('Assignment removed', 'success')
    except mysql.connector.Error as err:
        flash(f'Error removing assignment: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/enroll_course', methods=['POST'])
def enroll_course():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    student_id = session['user_id']
    
    if not course_id:
        flash('Please select a course', 'error')
        return redirect(url_for('student_dashboard'))
    
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM enroll 
                WHERE student_id = %s AND course_id = %s
            """, (student_id, course_id))
            
            if cursor.fetchone()[0] > 0:
                flash('You are already enrolled in this course!', 'warning')
            else:
                cursor.execute("""
                    INSERT INTO enroll (student_id, course_id)
                    VALUES (%s, %s)
                """, (student_id, course_id))
                conn.commit()
                flash('Successfully enrolled in course!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error enrolling: {err}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('student_dashboard'))


@app.route('/create_feedback_session', methods=['POST'])
def create_feedback_session():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    session_id = request.form.get('session_id')
    course_id = request.form.get('course_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not all([session_id, course_id, start_date, end_date]):
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

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO feedbacksession (session_id, course_id, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s)",
                           (session_id, course_id, sd, ed, 'Active'))
            conn.commit()
            flash('Feedback session created successfully', 'success')
        except mysql.connector.Error as err:
            flash(f'Error creating session: {err}', 'error')
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/feedback_form/<session_id>', methods=['GET'])
def feedback_form(session_id):
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))

    student_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('student_dashboard'))

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM feedbacksession WHERE session_id = %s", (session_id,))
        fs = cursor.fetchone()
        if not fs:
            flash('Feedback session not found', 'error')
            return redirect(url_for('student_dashboard'))

        now = datetime.now()
        start = fs['start_date']
        end = fs['end_date']

        if not (start <= now <= end):
            flash('This feedback form is not currently open', 'error')
            return redirect(url_for('student_dashboard'))

        # fetch questions (limit to 10)
        cursor.execute("SELECT * FROM feedbackquestions ORDER BY question_id LIMIT 10")
        questions = cursor.fetchall()

        # check if student already submitted structured remarks
        cursor.execute("SELECT * FROM feedbackremarks WHERE student_id=%s AND session_id=%s", (student_id, session_id))
        remarks = cursor.fetchone()

        return render_template('feedback_form.html', session=fs, questions=questions, remarks=remarks)
    finally:
        cursor.close()
        conn.close()


@app.route('/submit_feedback/<session_id>', methods=['POST'])
def submit_feedback(session_id):
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))

    student_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('student_dashboard'))

    cursor = conn.cursor()
    try:
        # store ratings for 10 questions
        for i in range(1, 11):
            qid = request.form.get(f'question_{i}_id')
            rating = request.form.get(f'question_{i}')
            if qid and rating:
                resp_id = f"{session_id}_{student_id}_{i}"
                try:
                    cursor.execute("INSERT INTO feedbackresponses (response_id, student_id, session_id, course_id, faculty_id, question_id, rating) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                   (resp_id, student_id, session_id, request.form.get('course_id'), request.form.get('faculty_id'), qid, int(rating)))
                except mysql.connector.IntegrityError:
                    # ignore duplicates
                    pass

        # store free-form comments
        comments = request.form.get('comments')

        try:
            cursor.execute("INSERT INTO feedbackremarks (student_id, session_id, comments) VALUES (%s,%s,%s)",
                           (student_id, session_id, comments))
        except mysql.connector.IntegrityError:
            cursor.execute("UPDATE feedbackremarks SET comments=%s WHERE student_id=%s AND session_id=%s",
                           (comments, student_id, session_id))

        conn.commit()
        flash('Feedback submitted. Thank you!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error submitting feedback: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('student_dashboard'))


@app.route('/admin_feedback_report/<session_id>')
def admin_feedback_report(session_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_dashboard'))

    cursor = conn.cursor(dictionary=True)
    try:
        # Ensure session exists
        cursor.execute("SELECT * FROM feedbacksession WHERE session_id=%s", (session_id,))
        fs = cursor.fetchone()
        if not fs:
            flash('Feedback session not found', 'error')
            return redirect(url_for('admin_dashboard'))

        # compute average rating per question and overall
        cursor.execute("SELECT question_id, AVG(rating) as avg_rating FROM feedbackresponses WHERE session_id=%s GROUP BY question_id", (session_id,))
        per_question = cursor.fetchall()

        cursor.execute("SELECT AVG(rating) as overall_avg FROM feedbackresponses WHERE session_id=%s", (session_id,))
        overall = cursor.fetchone()

        # fetch remarks
        cursor.execute("SELECT * FROM feedbackremarks WHERE session_id=%s", (session_id,))
        remarks = cursor.fetchall()

        return render_template('feedback_report.html', session=fs, per_question=per_question, overall=overall, remarks=remarks)
    finally:
        cursor.close()
        conn.close()


@app.route('/close_feedback_session/<session_id>', methods=['POST'])
def close_feedback_session(session_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE feedbacksession SET status=%s WHERE session_id=%s", ('Closed', session_id))
        conn.commit()
        flash('Session closed successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error closing session: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)