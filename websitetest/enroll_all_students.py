import mysql.connector

# Safe script to enroll test students S001..S060 into five test courses.
# It performs INSERT IGNORE so existing enrollments are not duplicated and nothing is deleted.

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'DewangMYSQLC@270505',
    'database': 'DBMSPROJ'
}

# Preferred test course IDs — if these exist they'll be used; otherwise the script will fall back to all courses in the DB.
PREFERRED_COURSE_IDS = ['C101', 'C201', 'C301', 'C401', 'C501']


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def enroll_all_students_into_courses():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Build student list S001..S060
        students = [f"S{i:03d}" for i in range(1, 61)]

        # Try to use preferred course IDs if they exist
        cursor.execute("SELECT course_id FROM courses WHERE course_id IN (%s, %s, %s, %s, %s)", tuple(PREFERRED_COURSE_IDS))
        found = [row[0] for row in cursor.fetchall()]

        if found:
            course_ids = found
            print(f"Using preferred course IDs found in DB: {course_ids}")
        else:
            # Fallback: enroll into all courses in the courses table
            cursor.execute("SELECT course_id FROM courses")
            course_ids = [row[0] for row in cursor.fetchall()]
            print(f"Preferred course IDs not found. Falling back to all courses: {course_ids}")

        if not course_ids:
            print("No courses found in the database. Aborting.")
            return

        # Prepare a batch of (student_id, course_id) tuples
        to_insert = []
        for sid in students:
            for cid in course_ids:
                to_insert.append((sid, cid))

        # Use INSERT IGNORE to avoid duplicate-primary-key errors (does not delete or modify existing rows)
        sql = "INSERT IGNORE INTO enroll (student_id, course_id) VALUES (%s, %s)"

        print(f"Attempting to insert {len(to_insert)} enrollments (duplicates will be ignored)...")
        cursor.executemany(sql, to_insert)
        conn.commit()

        print(f"Done. {cursor.rowcount} rows affected (newly-inserted enrollments).")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    enroll_all_students_into_courses()
