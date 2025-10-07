# Student Management System

A modern, secure student management system built with Flask and MySQL.

## Features

- **Multi-Portal Login System**
  - Student Portal (coming soon)
  - Faculty Portal (coming soon)  
  - Admin Portal (fully functional)

- **Admin Features**
  - Add new students with secure password hashing
  - Add new faculty members with secure password hashing
  - View all students and faculty
  - Modern, responsive design

- **Security**
  - Custom password hashing with salt
  - Session management
  - Form validation
  - SQL injection protection

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database**
   - Update MySQL credentials in `app.py`:
   ```python
   def get_db_connection():
       return mysql.connector.connect(
           host='localhost',
           user='your_username',      # Change this
           password='your_password',  # Change this
           database='student_management'  # Change this
       )
   ```

3. **Create Database Tables**
   Make sure your MySQL database has these tables:
   - `students` (student_id, name, email, password_hash, program)
   - `faculty` (faculty_id, name, email, password_hash, department)

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the System**
   - Open http://127.0.0.1:5000
   - Use Faculty login with credentials: `admin` / `admin123` to access admin portal

## Default Admin Credentials
- **Username:** admin
- **Password:** admin123

## File Structure
```
websitetest/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css     # Custom styling
│   └── js/
│       └── script.js     # JavaScript enhancements
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Landing page
    ├── login.html        # Login page
    ├── student_dashboard.html    # Student portal
    ├── faculty_dashboard.html    # Faculty portal
    └── admin_dashboard.html      # Admin portal
```

## Design Features
- Modern gradient backgrounds
- Floating animations
- Responsive design
- Bootstrap 5 integration
- Custom CSS animations
- Interactive elements
- Mobile-friendly interface

## Security Notes
- All passwords are hashed using PBKDF2 with SHA-256
- Session management prevents unauthorized access
- Form validation on both client and server side
- Protection against SQL injection using parameterized queries