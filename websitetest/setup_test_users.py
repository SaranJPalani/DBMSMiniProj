import mysql.connector
import hashlib
import secrets

def custom_hash(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + hashed.hex()

def setup_test_users():
    # Database connection
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Saran123$',
        database='DBMSPROJ'
    )
    cursor = conn.cursor()
    
    try:
        # Clear existing test data
        print("Clearing existing test data...")
        cursor.execute("DELETE FROM enroll")
        cursor.execute("DELETE FROM taughtby")
        cursor.execute("DELETE FROM students WHERE student_id LIKE 'TEST%'")
        cursor.execute("DELETE FROM faculty WHERE faculty_id LIKE 'TEST%'")
        cursor.execute("DELETE FROM courses WHERE course_id LIKE 'TEST%'")
        
        # Create test students with proper password hashes
        print("Creating test students...")
        test_students = [
            ('TESTU001', 'Alice Johnson', 'alice@test.com', 'Computer Science', 'password123'),
            ('TESTU002', 'Bob Smith', 'bob@test.com', 'Information Technology', 'password123'),
            ('TESTU003', 'Carol Davis', 'carol@test.com', 'Software Engineering', 'password123')
        ]
        
        for student_id, name, email, program, password in test_students:
            password_hash = custom_hash(password)
            cursor.execute("""
                INSERT INTO students (student_id, name, email, program, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, (student_id, name, email, program, password_hash))
            print(f"Created student: {name} (ID: {student_id}, Email: {email})")
        
        # Create test faculty with proper password hashes
        print("Creating test faculty...")
        test_faculty = [
            ('TESTF001', 'Dr. John Wilson', 'john.wilson@test.com', 'Computer Science', 'faculty123'),
            ('TESTF002', 'Prof. Sarah Brown', 'sarah.brown@test.com', 'Mathematics', 'faculty123'),
            ('TESTF003', 'Dr. Mike Taylor', 'mike.taylor@test.com', 'Information Technology', 'faculty123')
        ]
        
        for faculty_id, name, email, department, password in test_faculty:
            password_hash = custom_hash(password)
            cursor.execute("""
                INSERT INTO faculty (faculty_id, name, email, department, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, (faculty_id, name, email, department, password_hash))
            print(f"Created faculty: {name} (ID: {faculty_id}, Email: {email})")
        
        # Create test courses
        print("Creating test courses...")
        test_courses = [
            ('TESTC001', 'Database Systems', 'CS301', 'Fall 2025'),
            ('TESTC002', 'Data Structures', 'CS201', 'Fall 2025'),
            ('TESTC003', 'Web Development', 'IT401', 'Spring 2025')
        ]
        
        for course_id, course_name, course_code, semester in test_courses:
            cursor.execute("""
                INSERT INTO courses (course_id, course_name, course_code, semester)
                VALUES (%s, %s, %s, %s)
            """, (course_id, course_name, course_code, semester))
            print(f"Created course: {course_name} ({course_code})")
        
        # Create enrollments
        print("Creating test enrollments...")
        test_enrollments = [
            ('TESTU001', 'TESTC001'),
            ('TESTU001', 'TESTC002'),
            ('TESTU002', 'TESTC001'),
            ('TESTU002', 'TESTC003'),
            ('TESTU003', 'TESTC002'),
            ('TESTU003', 'TESTC003')
        ]
        
        for student_id, course_id in test_enrollments:
            cursor.execute("""
                INSERT INTO enroll (student_id, course_id)
                VALUES (%s, %s)
            """, (student_id, course_id))
        
        # Create faculty-course assignments
        print("Creating faculty-course assignments...")
        test_assignments = [
            ('TESTF001', 'TESTC001', 'Fall 2025'),
            ('TESTF001', 'TESTC002', 'Fall 2025'),
            ('TESTF003', 'TESTC003', 'Spring 2025')
        ]
        
        for faculty_id, course_id, semester in test_assignments:
            cursor.execute("""
                INSERT INTO taughtby (faculty_id, course_id, semester)
                VALUES (%s, %s, %s)
            """, (faculty_id, course_id, semester))
        
        conn.commit()
        print("\n✅ Test users created successfully!")
        print("\n📝 Test Login Credentials:")
        print("STUDENTS:")
        print("- Email: alice@test.com | Password: password123")
        print("- Email: bob@test.com | Password: password123")
        print("- Email: carol@test.com | Password: password123")
        print("\nFACULTY:")
        print("- Email: john.wilson@test.com | Password: faculty123")
        print("- Email: sarah.brown@test.com | Password: faculty123")
        print("- Email: mike.taylor@test.com | Password: faculty123")
        print("\nADMIN:")
        print("- Username: admin | Password: admin123")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_test_users()