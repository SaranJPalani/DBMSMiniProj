import mysql.connector

# Quick debug script to check student chart data
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='DewangMYSQLC@270505',
    database='DBMSPROJ'
)
cursor = conn.cursor(dictionary=True)

# Check S001's enrollment and grades
print("=== Student S001 Debug ===")
cursor.execute("""
    SELECT c.course_code, c.course_id, g.grade 
    FROM enroll e 
    JOIN courses c ON e.course_id = c.course_id 
    LEFT JOIN grades g ON e.student_id = g.student_id AND e.course_id = g.course_id 
    WHERE e.student_id = %s
""", ('S001',))

rows = cursor.fetchall()
print(f"S001 has {len(rows)} enrolled courses:")
for r in rows:
    print(f"  {r['course_code']} ({r['course_id']}): {r['grade'] or 'NP'}")

# Test the exact query from student_dashboard
print("\n=== Testing student_dashboard query ===")
student_id = 'S001'

# Get enrolled courses (same query as in app.py)
enrolled_courses = cursor.execute("""
    SELECT c.*, f.name as faculty_name 
    FROM courses c
    JOIN enroll e ON c.course_id = e.course_id
    LEFT JOIN taughtby tb ON c.course_id = tb.course_id
    LEFT JOIN faculty f ON tb.faculty_id = f.faculty_id
    WHERE e.student_id = %s
""", (student_id,))
enrolled_courses = cursor.fetchall()

print(f"Enrolled courses query returned {len(enrolled_courses)} courses:")
for c in enrolled_courses:
    print(f"  {c['course_code']} - {c['course_name']}")

# Get grades (same query as in app.py)
cursor.execute("""
    SELECT g.course_id, g.grade, g.date_assigned
    FROM grades g
    WHERE g.student_id = %s
""", (student_id,))
grades_data = cursor.fetchall()

print(f"\nGrades query returned {len(grades_data)} grades:")
student_grades = {}
for grade in grades_data:
    student_grades[grade['course_id']] = grade
    print(f"  {grade['course_id']}: {grade['grade']}")

# Test chart data generation
print("\n=== Chart data generation test ===")
student_chart_labels = [c['course_code'] for c in enrolled_courses]
grade_to_num = {'A+':95,'A':90,'B+':85,'B':80,'C':70,'F':50}
student_chart_values = []
for c in enrolled_courses:
    g = student_grades.get(c['course_id'])
    if g and g.get('grade') in grade_to_num:
        student_chart_values.append(grade_to_num[g.get('grade')])
    else:
        student_chart_values.append(0)

print(f"Chart labels: {student_chart_labels}")
print(f"Chart values: {student_chart_values}")

conn.close()