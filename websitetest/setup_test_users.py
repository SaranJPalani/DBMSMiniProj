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
        
        # Create 60 test students with 3 programs cycling: Computer Science, IT, Mathematics
        print("Creating 60 test students...")
        first_names = [
            'Aarav','Diya','Ishaan','Mira','Arjun','Neha','Rohan','Sanya','Karan','Tara',
            'Vikram','Anika','Dev','Ira','Kabir','Leela','Manav','Nisha','Om','Pari',
            'Siddharth','Rhea','Aditya','Meera','Kunal','Pooja','Sameer','Ananya','Rahul','Ritika',
            'Yash','Kavya','Nimisha','Rajat','Soham','Priya','Zoya','Kiran','Harsh','Nitika',
            'Ragini','Ishita','Mayank','Tanvi','Aman','Nidhi','Akash','Esha','Vansh','Suhana',
            'Keshav','Trisha','Arnav','Sarika','Naveen','Prisha','Yuvraj','Mitali','Rudra','Anvi'
        ]
        last_names = [
            'Patel','Sharma','Gupta','Kapoor','Reddy','Verma','Malhotra','Mehta','Bhatia','Nair',
            'Singh','Bose','Khanna','Desai','Jain','Iyer','Joshi','Kulkarni','Prakash','Saxena',
            'Kumar','Agarwal','Chowdhury','Chadha','Shah','Sethi','Chopra','Roy','Kohli','Garg',
            'Bhardwaj','Pandey','Saxena','Tiwari','Rao','Naik','Biswas','Ghosh','Saini','Pandit',
            'Mehra','Dutta','Bhatt','Khandelwal','Kapoor','Mahajan','Raman','Bose','Shukla','Goyal',
            'Bhattacharya','Chakraborty','Saxena','Mishra','Bedi','Sinha','Jha','Rao','Malik','Ahuja'
        ]

        programs = ['Computer Science', 'IT', 'Mathematics']

        # collect created students for summary output
        test_students = []

        for i in range(1, 61):
            student_id = f"S{i:03d}"
            fn = first_names[(i-1) % len(first_names)]
            ln = last_names[(i-1) % len(last_names)]
            name = f"{fn} {ln}"
            # create an email that's likely unique
            email = f"{fn.lower()}.{ln.lower()}{i:03d}@test.com"
            program = programs[(i-1) % len(programs)]
            password = 'password123'
            password_hash = custom_hash(password)
            try:
                cursor.execute("""
                    INSERT INTO students (student_id, name, email, program, password_hash)
                    VALUES (%s, %s, %s, %s, %s)
                """, (student_id, name, email, program, password_hash))
                # append only on successful insert
                test_students.append((student_id, name, email, program, password_hash))
                print(f"Created student: {name} (ID: {student_id}, Email: {email}, Program: {program})")
            except mysql.connector.Error as err:
                # If duplicate or other error, print and continue
                print(f"Warning: couldn't create {student_id} - {err}")
        
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
        if test_students:
            for student_id, name, email, program, _ in test_students[:5]:
                print(f"- {name} | ID: {student_id} | Email: {email} | Program: {program}")
            if len(test_students) > 5:
                print(f"  ...and {len(test_students) - 5} more test students")
        else:
            print("No test students were created.")

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