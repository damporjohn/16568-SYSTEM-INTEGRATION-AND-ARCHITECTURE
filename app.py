from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  
from datetime import date 

registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for session management

# Function to create tables in separate databases
# Function: Initialize Databases (Run Once)
def init_db():
    databases = {
        "adminuser.db": "admins",
        "staffuser.db": "staffs",
        "studentuser.db": "students"
    }

    for db_name, table_name in databases.items():
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idno TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    firstname TEXT NOT NULL,
                    lastname TEXT NOT NULL,
                    midname TEXT,
                    course TEXT,
                    yearlevel TEXT,
                    email TEXT UNIQUE NOT NULL,
                    remaining_sessions INTEGER DEFAULT 5,
                    registration_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    """Create required database tables if they do not exist."""
    with sqlite3.connect('labs.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS labs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE NOT NULL,
                capacity INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available'
            )
        ''')
        conn.commit()

    # Create the deans table inside adminuser.db
    with sqlite3.connect("adminuser.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS deans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            registration_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()


        
        print("Database initialized successfully.")  # Correct indentation

    # Run this function once to initialize the database

    with sqlite3.connect("studentuser.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idno TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                midname TEXT,
                course TEXT,
                yearlevel TEXT,
                email TEXT UNIQUE NOT NULL,
                registration_date TEXT NOT NULL,
                remaining_sessions INTEGER DEFAULT 5
            )
        ''')
        conn.commit()


# Function: Initialize Reservations Table (Run Once)
def init_reservations_table():
    with sqlite3.connect('reservations.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                lab_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()

# Ensure reservations table exists
def create_reservations_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lab_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Ensure table exists
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sit_in_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lab_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


    
conn = sqlite3.connect("studentuser.db")
cur = conn.cursor()

# Check if table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students';")
table_exists = cur.fetchone()

if table_exists:
    print("Table 'students' exists.")

    # Show table schema
    cur.execute("PRAGMA table_info(students);")
    columns = cur.fetchall()
    print("Columns in 'students' table:")
    for column in columns:
        print(column)
else:
    print("Table 'students' does not exist!")

conn.close()






# Function to get a database connection
def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    return conn


def get_db_connection(db_name='reservations.db'):  # Accepts an optional argument
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Allows access to columns by name
    return conn

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row  # Enables accessing columns by name
    return conn


def get_db_connection(db_name='studentuser.db'):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def get_labs():
    conn = sqlite3.connect("your_database.db")  # Ensure correct database name
    cur = conn.cursor()
    cur.execute("SELECT id, number, capacity FROM labs")  # Make sure column names match
    labs = cur.fetchall()
    conn.close()
    return labs

DATABASE = "your_database.db"  # Make sure this is correct

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Optional: Makes rows accessible as dictionaries
    return conn









#Index route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'login' in request.form:
            return redirect(url_for('login_dashboard'))  # Redirect to login page if login button is pressed
        elif 'register' in request.form:
            return redirect(url_for('register_user'))  # Redirect to register page if register button is pressed

    return render_template('index.html')  # Render home page template

# Combined Login and Dashboard Route
@app.route('/login', methods=['GET', 'POST'])
def login_dashboard():
    if 'role' in session and session['role'] in ['admin', 'staff', 'student']:
        return redirect(url_for(f"{session['role']}_dashboard"))  # Redirect only if authenticated

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        databases = {
            "adminuser.db": "admins",
            "staffuser.db": "staffs",
            "studentuser.db": "students"
        }

        for db_name, table_name in databases.items():
            with sqlite3.connect(db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT password, firstname, lastname FROM {table_name} WHERE username=?", (username,))
                user = cursor.fetchone()

                if user:
                    stored_password, firstname, lastname = user
                    if check_password_hash(stored_password, password):
                        session.clear()  # Clear previous session data
                        session.update({
                            'username': username,
                            'firstname': firstname,
                            'lastname': lastname,
                            'role': db_name.replace("user.db", "")  # Extract correct role
                        })
                        return redirect(url_for(f"{session['role']}_dashboard"))

        error = "Invalid username or password."
        flash(error, 'danger')

    return render_template('login.html', error=error)


@app.route('/registeruser')
def register_user():
    return render_template("registeruser.html")  # Render registration page

# Registration route
@app.route('/register/<role>', methods=['GET', 'POST'])
def register(role):
    database_map = {
        "admin": "adminuser.db",
        "staff": "staffuser.db",
        "student": "studentuser.db"
    }

    if role not in database_map:
        flash("Invalid role.")  # Flash message for invalid role
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Gather form data
        idno = request.form['idno']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        midname = request.form.get('midname', '')
        course = request.form.get('course', '')
        yearlevel = request.form.get('yearlevel', '')
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match.")  # Flash message for password mismatch
            return redirect(url_for('register', role=role))

        hashed_password = generate_password_hash(password)  # Hash the password
        registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Corrected line

        db_name = database_map[role]
        table_name = role

        try:
            with sqlite3.connect(db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT INTO {table_name}s (idno, username, password, firstname, lastname, midname, course, yearlevel, email, registration_date) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (idno, username, hashed_password, firstname, lastname, midname, course, yearlevel, email, registration_date))
                conn.commit()

            flash(f"Successfully registered as {role}!")  # Success message
            return redirect(url_for('login_dashboard'))

        except sqlite3.IntegrityError as e:
            # Check for specific integrity error and set the flash message accordingly
            if 'UNIQUE constraint failed' in str(e):
                flash("Email already exists. Please use a different email.")
            else:
                flash("An error occurred. Please try again.")
            return redirect(url_for('register', role=role))

    return render_template(f'register_{role}.html')  # Render registration template














# Admin Dashboard Route
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':  # Should be 'admin' instead of 'admins'
        return redirect(url_for('login_dashboard'))

    staff_members = []
    with sqlite3.connect('staffuser.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT idno, username, firstname, lastname, registration_date FROM staffs")
        staff_members = cursor.fetchall()

    deans = []
    with sqlite3.connect('adminuser.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, id_number, username, first_name, last_name, email, department, registration_date FROM deans")
        deans = cursor.fetchall()

    labs = []
    with sqlite3.connect('labs.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, number, capacity, status FROM computer_labs")
        labs = cursor.fetchall()

    return render_template('admin_dashboard.html', staff_members=staff_members, deans=deans, labs=labs)

#MAG DELETE OG STAFF
@app.route('/delete_staff/<idno>', methods=['POST'])
def delete_staff(idno):
    if session.get('role') != 'admins':
        return redirect(url_for('dashboard'))  # Redirect if not an admin
    
    with sqlite3.connect('staffuser.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM staffs WHERE idno=?", (idno,))
            conn.commit()
            flash("Staff member deleted successfully.", "success")  # Success message
        except sqlite3.Error as e:
            flash("An error occurred while deleting the staff member: " + str(e), "error")  # Error message

    return redirect(url_for('admin_dashboard'))  # Redirect back to admin dashboard

#MAG ADD/REGISTER OG DEAN
@app.route('/add_dean', methods=['POST'])
def add_dean():
    dean_id = request.form['dean_id']
    username = request.form['dean_username']
    first_name = request.form['dean_firstname']
    last_name = request.form['dean_lastname']
    email = request.form['dean_email']
    department = request.form['dean_department']

    try:
        with sqlite3.connect('adminuser.db') as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO deans (id_number, username, first_name, last_name, email, department, registration_date) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (dean_id, username, first_name, last_name, email, department, registration_date))
            conn.commit()
        flash("Dean added successfully!", "success")
    except sqlite3.IntegrityError:
        flash("Error: ID Number or Email already exists.", "danger")
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "danger")

    return redirect(url_for('admin_dashboard'))

#ADD OG LABORATORY 
@app.route('/add_lab', methods=['POST'])
def add_lab():
    if request.method == 'POST':
        lab_number = request.form.get('lab_number', '').strip()
        capacity = request.form.get('lab_capacity', '').strip()

        if not lab_number or not capacity:
            flash("Lab Number and Capacity are required!", "danger")
            return redirect(url_for('admin_dashboard'))

        try:
            with sqlite3.connect('labs.db') as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO computer_labs (number, capacity, status) VALUES (?, ?, ?)", 
                            (lab_number, capacity, "Available"))
                conn.commit()
            flash("Lab added successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Error: Lab number already exists!", "warning")
        except sqlite3.Error as e:
            flash(f"Database Error: {e}", "danger")

    return redirect(url_for('admin_dashboard'))











# Student Dashboard Route
@app.route('/student_dashboard') 
def student_dashboard():
    if 'username' not in session or session.get('role') != 'student':  # Ensure role is 'student'
        flash("You need to log in first.", "danger")
        return redirect(url_for('login_dashboard'))

    username = session['username']

    # Open connection to studentuser.db
    conn_user = get_db_connection('studentuser.db')  # Use get_db_connection() if defined
    cursor_user = conn_user.cursor()
    cursor_user.execute("SELECT firstname, lastname, email, course, yearlevel FROM students WHERE username = ?", (username,))
    student = cursor_user.fetchone()
    conn_user.close()

    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for('login_dashboard'))

    # Open connection to labs.db
    conn_labs = get_db_connection('labs.db')  # Use get_db_connection() if defined
    cursor_labs = conn_labs.cursor()
    cursor_labs.execute("SELECT id, number, capacity FROM labs")
    labs = cursor_labs.fetchall()
    conn_labs.close()

    return render_template('student_dashboard.html', 
                           firstname=student[0], 
                           lastname=student[1], 
                           email=student[2], 
                           course=student[3], 
                           yearlevel=student[4], 
                           labs=[{"id": lab[0], "number": lab[1], "capacity": lab[2]} for lab in labs], 
                           current_date=date.today().isoformat())


@app.route('/edit_student_record', methods=['GET', 'POST'])
def edit_student_record():
    print("Session Data:", session)  # Debug session contents

    if 'username' not in session or session.get('role') != 'students':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))  # Ensure 'login' is the correct route

    username = session['username']

    # Open connection to studentuser.db
    conn_user = get_db_connection('studentuser.db')
    cur_user = conn_user.cursor()

    # Fetch the student's record
    cur_user.execute("SELECT * FROM students WHERE username = ?", (username,))
    student = cur_user.fetchone()
    print("Fetched Student Record:", student)  # Debug student data

    if not student:
        flash("Student record not found.", "danger")
        conn_user.close()
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        try:
            # Collect form data (use existing values if fields are empty)
            firstname = request.form.get('firstname', student[1]) or student[1]
            lastname = request.form.get('lastname', student[2]) or student[2]
            midname = request.form.get('midname', student[3]) or student[3]
            email = request.form.get('email', student[4]) or student[4]
            course = request.form.get('course', student[5]) or student[5]
            yearlevel = request.form.get('yearlevel', student[6]) or student[6]

            # Update student record
            cur_user.execute('''
                UPDATE students 
                SET firstname=?, lastname=?, midname=?, email=?, course=?, yearlevel=?
                WHERE username=?
            ''', (firstname, lastname, midname, email, course, yearlevel, username))
            conn_user.commit()

            flash("Your record has been updated successfully!", "success")
            return redirect(url_for('student_dashboard'))

        except sqlite3.Error as e:
            flash(f"Database error: {e}", "danger")

    conn_user.close()
    
    # Ensure student is passed as a dictionary
    student_dict = {
        'id': student[0],
        'firstname': student[1],
        'lastname': student[2],
        'midname': student[3] if student[3] else '',
        'email': student[4],
        'course': student[5] if student[5] else '',
        'yearlevel': student[6]
    }

    return render_template('edit_student_record.html', student=student_dict)



@app.route('/make_reservation', methods=['POST'])
def make_reservation():
    if 'username' not in session or session.get('role') != 'students':
        return redirect(url_for('login'))
    
    username = session['username']
    lab_id = request.form['lab']
    date = request.form['date']
    time = request.form['time']
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # ✅ Fetch lab details from labs.db
        with get_db_connection('labs.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, capacity FROM labs WHERE id=?", (lab_id,))
            lab = cur.fetchone()
        
        if not lab:
            flash("Invalid lab selection!", "danger")
            return redirect(url_for('student_dashboard'))
        
        lab_capacity = lab[1]  # Extract lab capacity

        # ✅ Check student's remaining sessions in studentuser.db
        with get_db_connection('studentuser.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT remaining_sessions FROM students WHERE username=?", (username,))
            student = cur.fetchone()
        
        if not student or student[0] <= 0:
            flash("You have no remaining sit-in sessions!", "danger")
            return redirect(url_for('student_dashboard'))
        
        # ✅ Check if lab is full for the selected date & time
        with get_db_connection('reservations.db') as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM reservations 
                WHERE lab_id=? AND date=? AND time=?
            """, (lab_id, date, time))
            current_reservations = cur.fetchone()[0]
        
        if current_reservations >= lab_capacity:
            flash("Lab is already full for the selected time!", "danger")
            return redirect(url_for('student_dashboard'))

        # ✅ Insert reservation & update student's remaining sessions atomically
        with get_db_connection('reservations.db') as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO reservations (username, lab_id, date, time, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, lab_id, date, time, timestamp))
            conn.commit()
        
        with get_db_connection('studentuser.db') as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE students SET remaining_sessions = remaining_sessions - 1 
                WHERE username=?
            """, (username,))
            conn.commit()

        flash("Reservation successful!", "success")
    
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "danger")
    
    return redirect(url_for('student_dashboard'))

#ARI RA KUTOB STUDENT 












# Staff Dashboard Route
@app.route('/staff_dashboard')
def staff_dashboard():
    if session.get('role') != 'staff':  # Should be 'staff' instead of 'staffs'
        return redirect(url_for('login_dashboard'))

    create_reservations_table()  # Ensure table exists before querying

    conn = get_db_connection()
    cur = conn.cursor()
    today = date.today().strftime('%Y-%m-%d')  # Fixed datetime issue
    cur.execute("SELECT * FROM reservations WHERE date=?", (today,))
    today_reservations = cur.fetchall()
    conn.close()
    
    return render_template('staff_dashboard.html', today_reservations=today_reservations, firstname=session.get('firstname', 'Staff'))

# Reset Student Session Route
@app.route('/reset_session')
def reset_session():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE students SET remaining_sessions = 5")
        conn.commit()

    flash("All student sessions have been reset!", "success")
    return redirect(url_for('staff_dashboard'))

#Searchbar
@app.route('/search_reservation', methods=['GET'])
def search_reservation():
    if 'username' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip()

    reservations = []
    if query:
        conn = get_db_connection('reservations.db')
        cur = conn.cursor()
        
        # Search query (adjust the table/column names as needed)
        cur.execute('''
            SELECT * FROM reservations
            WHERE username LIKE ? OR lab_id LIKE ? OR date LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        reservations = cur.fetchall()
        conn.close()

    return render_template('search_reservation.html', reservations=reservations, query=query)

@app.route('/sit_in_reservations')
def sit_in_reservations():
    conn = sqlite3.connect("reservations.db")  # Connect to reservations.db
    conn.row_factory = sqlite3.Row  # Allows column access by name
    cur = conn.cursor()

    cur.execute("SELECT * FROM reservations")  # Fetch all reservations
    reservations = cur.fetchall() 
    
    conn.close()
    
    return render_template('staff_dashboard.html', reservations=reservations)


@app.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection('reservations.db')
    cur = conn.cursor()
    
    # Fetch the reservation
    cur.execute('SELECT * FROM reservations WHERE id = ?', (reservation_id,))
    reservation = cur.fetchone()

    if not reservation:
        flash("Reservation not found.", "danger")
        return redirect(url_for('search_reservation'))

    if request.method == 'POST':
        username = request.form.get('username', '')
        lab_id = request.form.get('lab_id', '')
        date = request.form.get('date', '')
        time_slot = request.form.get('time_slot', '')

        cur.execute('''
            UPDATE reservations
            SET username = ?, lab_id = ?, date = ?, time_slot = ?
            WHERE id = ?
        ''', (username, lab_id, date, time_slot, reservation_id))
        
        conn.commit()
        conn.close()

        flash("Reservation updated successfully!", "success")
        return redirect(url_for('search_reservation'))

    conn.close()
    return render_template('edit_reservation.html', reservation=reservation)

#DELETE
@app.route('/delete_reservation/<int:reservation_id>', methods=['POST'])
def delete_reservation(reservation_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection('reservations.db')
    cur = conn.cursor()

    cur.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
    conn.commit()
    conn.close()

    flash("Reservation deleted successfully!", "success")
    return redirect(url_for('search_reservation'))

@app.route('/sit_in_records')
def sit_in_records():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM sit_in_records")
    records = cur.fetchall()
    
    conn.close()

    return render_template('sit_in_record.html', records=records)

# View Past, Present, and Future Reservations
@app.route('/view_past_reservations')
def view_past_reservations():
    today = datetime.date.today().strftime("%Y-%m-%d")

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reservations WHERE date < ?", (today,))
        past_reservations = cur.fetchall()

    return render_template("reservation_list.html", reservations=past_reservations, title="Past Reservations")

@app.route('/view_present_reservations')
def view_present_reservations():
    today = datetime.date.today().strftime("%Y-%m-%d")

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reservations WHERE date = ?", (today,))
        present_reservations = cur.fetchall()

    return render_template("reservation_list.html", reservations=present_reservations, title="Present Reservations")

@app.route('/view_future_reservations')
def view_future_reservations():
    today = datetime.date.today().strftime("%Y-%m-%d")

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reservations WHERE date > ?", (today,))
        future_reservations = cur.fetchall()

    return render_template("reservation_list.html", reservations=future_reservations, title="Future Reservations")











# Logout Route
@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    return redirect(url_for('login_dashboard'))  # Redirect to login page

if __name__ == '__main__':
    app.run(debug=True)  # Run the application in debug mode
