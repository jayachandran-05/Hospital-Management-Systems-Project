from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "hospital123"

DATABASE = "hospital.db"


# ---------------- DATABASE CONNECTION ---------------- #

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE DATABASE TABLES ---------------- #

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    # Admin Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Patients Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            address TEXT
        )
    """)

    # Doctors Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT,
            phone TEXT
        )
    """)

    # Appointments Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            doctor_name TEXT,
            appointment_date TEXT,
            appointment_time TEXT
        )
    """)

    # Insert Default Admin
    cur.execute("SELECT * FROM admin WHERE username = ?", ("admin",))
    admin = cur.fetchone()

    if admin is None:
        cur.execute("""
            INSERT INTO admin(username, password)
            VALUES (?, ?)
        """, ("admin", "admin123"))

    conn.commit()
    conn.close()


# Create Tables Automatically
create_tables()


# ---------------- LOGIN REQUIRED DECORATOR ---------------- #

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please login first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- LOGIN ---------------- #

@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        admin = conn.execute("""
            SELECT * FROM admin
            WHERE username=? AND password=?
        """, (username, password)).fetchone()

        conn.close()

        if admin:
            session["user"] = username
            flash("Login Successful")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Username or Password")

    return render_template("login.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db_connection()

    total_patients = conn.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    total_doctors = conn.execute(
        "SELECT COUNT(*) FROM doctors"
    ).fetchone()[0]

    total_appointments = conn.execute(
        "SELECT COUNT(*) FROM appointments"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        patients=total_patients,
        doctors=total_doctors,
        appointments=total_appointments
    )
# ---------------- PATIENT MANAGEMENT ---------------- #

@app.route("/patients")
@login_required
def patients():

    conn = get_db_connection()

    patient_list = conn.execute("""
        SELECT * FROM patients
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "patients.html",
        patients=patient_list
    )


# ---------------- ADD PATIENT ---------------- #

@app.route("/add_patient", methods=["GET", "POST"])
@login_required
def add_patient():

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        address = request.form["address"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO patients
            (name, age, gender, phone, address)
            VALUES (?, ?, ?, ?, ?)
        """, (name, age, gender, phone, address))

        conn.commit()
        conn.close()

        flash("Patient added successfully!")
        return redirect(url_for("patients"))

    return render_template("add_patient.html")


# ---------------- DELETE PATIENT ---------------- #

@app.route("/delete_patient/<int:id>")
@login_required
def delete_patient(id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM patients
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Patient deleted successfully!")

    return redirect(url_for("patients"))


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
@login_required
def logout():

    session.clear()

    flash("Logged out successfully!")

    return redirect(url_for("login"))

# ---------------- DOCTOR MANAGEMENT ---------------- #

@app.route("/doctors")
@login_required
def doctors():

    conn = get_db_connection()

    doctor_list = conn.execute("""
        SELECT * FROM doctors
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "doctors.html",
        doctors=doctor_list
    )


# ---------------- ADD DOCTOR ---------------- #

@app.route("/add_doctor", methods=["GET", "POST"])
@login_required
def add_doctor():

    if request.method == "POST":

        name = request.form["name"]
        specialization = request.form["specialization"]
        phone = request.form["phone"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO doctors
            (name, specialization, phone)
            VALUES (?, ?, ?)
        """, (name, specialization, phone))

        conn.commit()
        conn.close()

        flash("Doctor added successfully!")

        return redirect(url_for("doctors"))

    return render_template("add_doctor.html")


# ---------------- DELETE DOCTOR ---------------- #

@app.route("/delete_doctor/<int:id>")
@login_required
def delete_doctor(id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM doctors
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Doctor deleted successfully!")

    return redirect(url_for("doctors"))


# ---------------- APPOINTMENT MANAGEMENT ---------------- #

@app.route("/appointments")
@login_required
def appointments():

    conn = get_db_connection()

    appointment_list = conn.execute("""
        SELECT * FROM appointments
        ORDER BY id DESC
    """).fetchall()

    doctor_list = conn.execute("""
        SELECT * FROM doctors
    """).fetchall()

    patient_list = conn.execute("""
        SELECT * FROM patients
    """).fetchall()

    conn.close()

    return render_template(
        "appointments.html",
        appointments=appointment_list,
        doctors=doctor_list,
        patients=patient_list
    )


# ---------------- ADD APPOINTMENT ---------------- #

@app.route("/add_appointment", methods=["GET", "POST"])
@login_required
def add_appointment():

    if request.method == "POST":

        patient_name = request.form["patient_name"]
        doctor_name = request.form["doctor_name"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO appointments
            (patient_name, doctor_name, appointment_date, appointment_time)
            VALUES (?, ?, ?, ?)
        """, (
            patient_name,
            doctor_name,
            appointment_date,
            appointment_time
        ))

        conn.commit()
        conn.close()

        flash("Appointment booked successfully!")

        return redirect(url_for("appointments"))

    conn = get_db_connection()

    doctor_list = conn.execute("SELECT * FROM doctors").fetchall()
    patient_list = conn.execute("SELECT * FROM patients").fetchall()

    conn.close()

    return render_template(
        "add_appointment.html",
        doctors=doctor_list,
        patients=patient_list
    )


# ---------------- DELETE APPOINTMENT ---------------- #

@app.route("/delete_appointment/<int:id>")
@login_required
def delete_appointment(id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM appointments
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Appointment deleted successfully!")

    return redirect(url_for("appointments"))


# ---------------- RUN APPLICATION ---------------- #

if __name__ == "__main__":
    app.run(debug=True)