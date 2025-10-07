-- Student Management System Database Schema
-- Created: September 24, 2025
-- Database: DBMSPROJ

USE DBMSPROJ;

-- Drop tables in reverse order to handle foreign key constraints
DROP TABLE IF EXISTS feedbackresponses;
DROP TABLE IF EXISTS feedbackcomments;
DROP TABLE IF EXISTS evaluationreport;
DROP TABLE IF EXISTS feedbacksession;
DROP TABLE IF EXISTS feedbackquestions;
DROP TABLE IF EXISTS taughtby;
DROP TABLE IF EXISTS enroll;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS faculty;
DROP TABLE IF EXISTS students;

-- 1. Students Table
CREATE TABLE students (
    student_id VARCHAR(20) NOT NULL,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    program VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (student_id),
    UNIQUE KEY (email)
);

-- 2. Faculty Table
CREATE TABLE faculty (
    faculty_id VARCHAR(20) NOT NULL,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    department VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (faculty_id),
    UNIQUE KEY (email)
);

-- 3. Courses Table
CREATE TABLE courses (
    course_id VARCHAR(20) NOT NULL,
    course_name VARCHAR(50) NOT NULL,
    course_code VARCHAR(20) NOT NULL,
    semester VARCHAR(20) NOT NULL,
    PRIMARY KEY (course_id),
    UNIQUE KEY (course_code)
);

-- 4. Enroll Table (Many-to-Many: Students ↔ Courses)
CREATE TABLE enroll (
    student_id VARCHAR(20) NOT NULL,
    course_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 5. Taught_By Table (Many-to-Many: Faculty ↔ Courses) - CORRECTED VERSION
CREATE TABLE taughtby (
    faculty_id VARCHAR(20) NOT NULL,
    course_id VARCHAR(20) NOT NULL,
    semester VARCHAR(50) NOT NULL,
    PRIMARY KEY (faculty_id, course_id, semester),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 6. Feedback_Session Table
CREATE TABLE feedbacksession (
    session_id VARCHAR(20) NOT NULL,
    course_id VARCHAR(20),
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    PRIMARY KEY (session_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- 7. Feedback_Questions Table
CREATE TABLE feedbackquestions (
    question_id VARCHAR(20) NOT NULL,
    question_text TEXT NOT NULL,
    PRIMARY KEY (question_id)
);

-- 8. Feedback_Responses Table
CREATE TABLE feedbackresponses (
    response_id VARCHAR(20) NOT NULL,
    student_id VARCHAR(20),
    session_id VARCHAR(20),
    course_id VARCHAR(20),
    faculty_id VARCHAR(20),
    question_id VARCHAR(20),
    rating INT NOT NULL,
    sub_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (response_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (session_id) REFERENCES feedbacksession(session_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (question_id) REFERENCES feedbackquestions(question_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CHECK (rating BETWEEN 1 AND 5)
);

-- 9. Feedback Remarks Table (store raw student comments for downstream AI processing)
CREATE TABLE feedbackremarks (
    student_id VARCHAR(20) NOT NULL,
    session_id VARCHAR(20) NOT NULL,
    comments TEXT,
    PRIMARY KEY (student_id, session_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (session_id) REFERENCES feedbacksession(session_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 10. Evaluation_Report Table
CREATE TABLE evaluationreport (
    report_id VARCHAR(20) NOT NULL,
    session_id VARCHAR(20),
    course_id VARCHAR(20),
    faculty_id VARCHAR(20),
    strength TEXT,
    area_of_improvement TEXT,
    ai_summary TEXT,
    sentiment_score DECIMAL(5,2),
    PRIMARY KEY (report_id),
    FOREIGN KEY (session_id) REFERENCES feedbacksession(session_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Insert sample data for testing

-- Sample Students
INSERT INTO students (student_id, name, email, program, password_hash) VALUES
('STU001', 'John Smith', 'john.smith@college.edu', 'Computer Science', 'hashed_password_1'),
('STU002', 'Jane Doe', 'jane.doe@college.edu', 'Information Technology', 'hashed_password_2'),
('STU003', 'Mike Johnson', 'mike.johnson@college.edu', 'Software Engineering', 'hashed_password_3');

-- Sample Faculty
INSERT INTO faculty (faculty_id, name, email, department, password_hash) VALUES
('FAC001', 'Dr. Alice Wilson', 'alice.wilson@college.edu', 'Computer Science', 'hashed_password_f1'),
('FAC002', 'Prof. Bob Brown', 'bob.brown@college.edu', 'Mathematics', 'hashed_password_f2'),
('FAC003', 'Dr. Carol Davis', 'carol.davis@college.edu', 'Information Technology', 'hashed_password_f3');

-- Sample Courses
INSERT INTO courses (course_id, course_name, course_code, semester) VALUES
('CRS001', 'Database Management Systems', 'CS301', 'Fall 2025'),
('CRS002', 'Data Structures and Algorithms', 'CS201', 'Fall 2025'),
('CRS003', 'Web Development', 'IT401', 'Spring 2025');

-- Sample Enrollments
INSERT INTO enroll (student_id, course_id) VALUES
('STU001', 'CRS001'),
('STU001', 'CRS002'),
('STU002', 'CRS001'),
('STU002', 'CRS003'),
('STU003', 'CRS002'),
('STU003', 'CRS003');

-- Sample Taught By relationships
INSERT INTO taughtby (faculty_id, course_id, semester) VALUES
('FAC001', 'CRS001', 'Fall 2025'),
('FAC001', 'CRS002', 'Fall 2025'),
('FAC003', 'CRS003', 'Spring 2025');

-- Sample Feedback Questions
INSERT INTO feedbackquestions (question_id, question_text) VALUES
('Q001', 'How would you rate the teaching quality?'),
('Q002', 'How clear was the course content?'),
('Q003', 'How effective was the communication?'),
('Q004', 'How would you rate the overall course experience?'),
('Q005', 'How well were practical examples/demos provided?'),
('Q006', 'How organized was the course material?'),
('Q007', 'How approachable was the faculty for doubts?'),
('Q008', 'How timely were the assessments/feedback?'),
('Q009', 'How relevant was the course to the program?'),
('Q010', 'Would you recommend this teacher/course to others?');

-- Sample Feedback Session
INSERT INTO feedbacksession (session_id, course_id, start_date, end_date, status) VALUES
('SES001', 'CRS001', '2025-09-01 09:00:00', '2025-09-30 23:59:59', 'Active'),
('SES002', 'CRS002', '2025-09-01 09:00:00', '2025-09-30 23:59:59', 'Active');

-- Sample Feedback Responses
INSERT INTO feedbackresponses (response_id, student_id, session_id, course_id, faculty_id, question_id, rating, sub_date) VALUES
('RES001', 'STU001', 'SES001', 'CRS001', 'FAC001', 'Q001', 5, '2025-09-15 14:30:00'),
('RES002', 'STU001', 'SES001', 'CRS001', 'FAC001', 'Q002', 4, '2025-09-15 14:31:00'),
('RES003', 'STU002', 'SES001', 'CRS001', 'FAC001', 'Q001', 4, '2025-09-16 10:15:00'),
('RES004', 'STU002', 'SES001', 'CRS001', 'FAC001', 'Q002', 5, '2025-09-16 10:16:00');

-- Sample Feedback Comments
-- Sample Feedback Remarks (single comment per student)
INSERT INTO feedbackremarks (student_id, session_id, comments) VALUES
('STU001', 'SES001', 'Clear explanations with structured lectures but could benefit from more hands-on labs.'),
('STU002', 'SES001', 'Good pacing and coverage overall; adding deeper practical examples would help.');

-- Sample Evaluation Report
INSERT INTO evaluationreport (report_id, session_id, course_id, faculty_id, strength, area_of_improvement, ai_summary, sentiment_score) VALUES
('REP001', 'SES001', 'CRS001', 'FAC001', 'Excellent teaching methodology and clear explanations', 'Could include more hands-on exercises', 'Overall positive feedback with high ratings for teaching quality', 4.25);

COMMIT;