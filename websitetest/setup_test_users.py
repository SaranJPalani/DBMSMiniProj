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
        password='DewangMYSQLC@270505',
        database='DBMSPROJ'
    )
    cursor = conn.cursor()
    
    try:
        # Clear existing test data
        print("Clearing existing test data...")
        cursor.execute("DELETE FROM enroll")
        cursor.execute("DELETE FROM taughtby") 
        cursor.execute("DELETE FROM students")  # Remove all students
        cursor.execute("DELETE FROM faculty")   # Remove all faculty
        cursor.execute("DELETE FROM courses")   # Remove all courses
        
        # Create test students with only 3 programs: Computer Science, IT, Mathematics
        print("Creating test students...")
        test_students = [
            ('S001', 'Aarav Patel', 'aarav.patel@test.com', 'Computer Science', 'password123'),
            ('S002', 'Diya Sharma', 'diya.sharma@test.com', 'IT', 'password123'),
            ('S003', 'Ishaan Gupta', 'ishaan.gupta@test.com', 'Mathematics', 'password123'),
            ('S004', 'Mira Kapoor', 'mira.kapoor@test.com', 'Computer Science', 'password123'),
            ('S005', 'Arjun Reddy', 'arjun.reddy@test.com', 'IT', 'password123'),
            ('S006', 'Neha Verma', 'neha.verma@test.com', 'Mathematics', 'password123'),
            ('S007', 'Rohan Malhotra', 'rohan.malhotra@test.com', 'Computer Science', 'password123'),
            ('S008', 'Sanya Mehta', 'sanya.mehta@test.com', 'IT', 'password123'),
            ('S009', 'Karan Bhatia', 'karan.bhatia@test.com', 'Mathematics', 'password123'),
            ('S010', 'Tara Nair', 'tara.nair@test.com', 'Computer Science', 'password123'),
            ('S011', 'Vikram Singh', 'vikram.singh@test.com', 'IT', 'password123'),
            ('S012', 'Anika Bose', 'anika.bose@test.com', 'Mathematics', 'password123'),
            ('S013', 'Dev Khanna', 'dev.khanna@test.com', 'Computer Science', 'password123'),
            ('S014', 'Ira Desai', 'ira.desai@test.com', 'IT', 'password123'),
            ('S015', 'Kabir Jain', 'kabir.jain@test.com', 'Mathematics', 'password123'),
            ('S016', 'Leela Iyer', 'leela.iyer@test.com', 'Computer Science', 'password123'),
            ('S017', 'Manav Joshi', 'manav.joshi@test.com', 'IT', 'password123'),
            ('S018', 'Nisha Kulkarni', 'nisha.kulkarni@test.com', 'Mathematics', 'password123'),
            ('S019', 'Om Prakash', 'om.prakash@test.com', 'Computer Science', 'password123'),
            ('S020', 'Pari Saxena', 'pari.saxena@test.com', 'IT', 'password123')
        ]

        for student_id, name, email, program, password in test_students:
            password_hash = custom_hash(password)
            cursor.execute("""
                INSERT INTO students (student_id, name, email, program, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, (student_id, name, email, program, password_hash))
            print(f"Created student: {name} (ID: {student_id}, Email: {email}, Program: {program})")
        
        # Create test faculty with matching departments
        print("Creating test faculty...")
        test_faculty = [
            ('F001', 'Dr. Raghav Menon', 'raghav.menon@test.com', 'Computer Science', 'faculty123'),
            ('F002', 'Prof. Aisha Rahman', 'aisha.rahman@test.com', 'IT', 'faculty123'),
            ('F003', 'Dr. Vikram Deshpande', 'vikram.deshpande@test.com', 'Mathematics', 'faculty123'),
            ('F004', 'Prof. Sunita Rao', 'sunita.rao@test.com', 'Computer Science', 'faculty123'),
            ('F005', 'Dr. Nikhil Banerjee', 'nikhil.banerjee@test.com', 'IT', 'faculty123')
        ]
        
        for faculty_id, name, email, department, password in test_faculty:
            password_hash = custom_hash(password)
            cursor.execute("""
                INSERT INTO faculty (faculty_id, name, email, department, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, (faculty_id, name, email, department, password_hash))
            print(f"Created faculty: {name} (ID: {faculty_id}, Email: {email}, Department: {department})")
        
        # Create test courses
        print("Creating test courses...")
        test_courses = [
            ('C101', 'Foundations of Computing', 'C101', '5'),
            ('C201', 'Data Structures and Algorithms', 'C201', '5'),
            ('C301', 'Database Management Systems', 'C301', '5'),
            ('C401', 'Network Fundamentals', 'C401', '5'),
            ('C501', 'Probability and Statistics', 'C501', '5')
        ]

        for course_id, course_name, course_code, semester in test_courses:
            try:
                cursor.execute("""
                    INSERT INTO courses (course_id, course_name, course_code, semester)
                    VALUES (%s, %s, %s, %s)
                """, (course_id, course_name, course_code, semester))
                print(f"Created course: {course_name} ({course_code})")
            except mysql.connector.Error as err:
                if err.errno == 1062:  # Duplicate entry error
                    print(f"Course {course_name} ({course_code}) already exists - skipping")
                else:
                    print(f"❌ Error creating course {course_name}: {err}")

        conn.commit()
        print("\n✅ Test users created successfully!")
        print("\n📝 Test Login Credentials:")
        print("STUDENTS (all use password: password123):")
        for student_id, name, email, program, _ in test_students[:5]:
            print(f"- {name} | ID: {student_id} | Email: {email} | Program: {program}")
        if len(test_students) > 5:
            print(f"  ...and {len(test_students) - 5} more test students")

        print("\nFACULTY (all use password: faculty123):")
        for faculty_id, name, email, department, _ in test_faculty:
            print(f"- {name} | ID: {faculty_id} | Email: {email} | Department: {department}")

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