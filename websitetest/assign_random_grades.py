import mysql.connector
import random
import argparse

# Simple script to randomly assign grades to all enrollments.
# This version chooses one faculty (first found) and uses it for all assignments to keep it simple.

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'DewangMYSQLC@270505',
    'database': 'DBMSPROJ'
}

GRADE_CHOICES = ['A+', 'A', 'B+', 'B', 'C', 'F']


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def assign_random_grades(dry_run: bool = False, seed: int | None = None):
    if seed is not None:
        random.seed(seed)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT student_id, course_id FROM enroll")
        enrollments = cursor.fetchall()
        if not enrollments:
            print('No enrollments found. Nothing to do.')
            return

        # pick a single faculty to use for all grade rows (simpler)
        cursor.execute("SELECT faculty_id FROM faculty LIMIT 1")
        row = cursor.fetchone()
        if not row:
            print('No faculty found in database. Cannot assign grades.')
            return
        faculty_id = row[0]

        inserts = []
        for student_id, course_id in enrollments:
            grade = random.choice(GRADE_CHOICES)
            inserts.append((student_id, course_id, faculty_id, grade))

        sql = (
            "INSERT INTO grades (student_id, course_id, faculty_id, grade) VALUES (%s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE grade = VALUES(grade), faculty_id = VALUES(faculty_id), date_assigned = CURRENT_TIMESTAMP"
        )

        print(f"Prepared {len(inserts)} grade assignments. Dry run: {dry_run}")
        if dry_run:
            for sample in inserts[:10]:
                sid, cid, fid, grd = sample
                print(f"{sid} -> {cid}: {grd} (faculty: {fid})")
            return

        cursor.executemany(sql, inserts)
        conn.commit()
        print(f"Done. {cursor.rowcount} rows affected (inserts/updates).")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Assign random grades to enrolled students (simple)')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to DB, only preview')
    parser.add_argument('--seed', type=int, help='Optional random seed to make results reproducible')
    args = parser.parse_args()

    assign_random_grades(dry_run=args.dry_run, seed=args.seed)
