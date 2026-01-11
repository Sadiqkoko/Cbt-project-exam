from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import random
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "cbt_secret_key"

DB = "cbt_database.db"

# Faculty + Departments (dole a saman kafin routes)
FACULTIES = {
    "FACULTY OF PHYSICAL": {
        "code": "1020",
        "departments": {
            "COMPUTER SCIENCE":"01",
            "PHYSICS":"02",
            "APPLIED CHEMISTRY":"03",
            "INDUSTRIAL CHEMISTRY":"04",
            "STATISTICS":"05",
            "MATHEMATICS":"06"
        }
    },
    "FACULTY OF LIFE SCIENCE": {
        "code":"1030",
        "departments":{
            "BIOCHEMISTRY":"01",
            "MICROBIOLOGY":"02",
            "BIOLOGY":"03",
            "BOTANY":"04",
            "ZOOLOGY":"05"
        }
    },
    "FACULTY OF ENGINEERING":{
        "code":"1040",
        "departments":{
            "CIVIL ENGINEERING":"01",
            "ICT":"02",
            "MECHANICAL ENGINEERING":"03",
            "ELECTRIC AND ELECTRONIC ENGINEERING":"04"
        }
    },
    "FACULTY OF EDUCATION":{
        "code":"1050",
        "departments":{
            "SCIENCE EDUCATION":"01",
            "EDUCATION COMPUTER":"02",
            "EDUCATION MATHEMATICS":"03",
            "EDUCATION CHEMISTRY":"04",
            "EDUCATION BIOLOGY":"05",
            "EDUCATION PHYSICS":"06",
            "LIBRARY AND INFORMATION SCIENCE":"07",
            "EDUCATION CIVIL ENGINEERING":"08",
            "EDUCATION AGRICULTURE":"09"
        }
    },
    "FACULTY OF AGRICULTURE":{
        "code":"1060",
        "departments":{
            "ANIMAL SCIENCE":"01",
            "SOIL SCIENCE":"02",
            "FORESTRY":"03",
            "FISHERY":"04",
            "AGRICULTURE ECONOMICS AND EXTENSION":"05"
        }
    },
    "FACULTY OF BUILDING":{
        "code":"1070",
        "departments":{
            "QUANTITY SURVEY":"01",
            "ARCHITECTURE":"02",
            "BUILDING":"03"
        }
    }
}

# Create folder for profile pictures
if not os.path.exists('static/profile_pictures'):
    os.makedirs('static/profile_pictures')

# DB connection helper
def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# Generate admission number
def generate_admission_number(faculty_name, department_name):
    faculty_code = FACULTIES[faculty_name]["code"]
    dept_code = FACULTIES[faculty_name]["departments"][department_name]
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students WHERE faculty=? AND department=?", (faculty_name, department_name))
    count = c.fetchone()[0] + 1
    conn.close()
    serial = str(count).zfill(2)
    return f"AL{faculty_code}{dept_code}{serial}"  # 10-digit admission number

@app.route("/home")
@app.route("/")
def home():
    return render_template("home.html")

# ROUTE: Register
@app.route("/", methods=["GET", "POST"])
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form['fullname']
        email = request.form['email']  # ✅ new field
        dob = request.form['dob']
        phone = request.form['phone']
        nin = request.form['nin']
        gender = request.form['gender']
        country = request.form['country']
        state = request.form['state']
        lga = request.form['lga']
        address = request.form['address']
        faculty = request.form['faculty']
        department = request.form['department']
        level = request.form['level']
        session_ = request.form['session']
        password = request.form['password']
        pin = request.form['pin']
        secret_answer = request.form['secret_answer']

        # Profile picture
        profile_picture = request.files['profile_picture']
        if profile_picture.filename != '':
            filename = secure_filename(profile_picture.filename)
            filepath = os.path.join('static/profile_pictures', filename)
            profile_picture.save(filepath)
        else:
            filename = 'default.jpg'

        # Generate admission number
        admission_number = generate_admission_number(faculty, department)

        # Insert into DB
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO students 
            (fullname, email, admission_number, dob, phone, nin, picture, gender, country, state, lga, address, faculty, department, level, session, password, pin, secret_answer, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (fullname, email, admission_number, dob, phone, nin, filename, gender, country, state, lga, address, faculty, department, level, session_, password, pin, secret_answer, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        flash(f"Congratulations {fullname}! Your Admission Number is {admission_number}. Welcome to Alhuda Cyber Cafe Academy.", "success")
        return redirect(url_for("register"))

    return render_template("register.html", faculties=FACULTIES)

# ROUTE: Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_type = request.form['login_type']  # "student" or "admin"
        identifier = request.form['identifier']  # Admission / Phone / NIN or Username
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()

        if login_type == "student":
            # Student login: check admission_number, phone, or nin
            c.execute("""
                SELECT * FROM students 
                WHERE (admission_number=? OR phone=? OR nin=?) AND password=?
            """, (identifier, identifier, identifier, password))
            user = c.fetchone()
            conn.close()
            if user:
                # ✅ Set session for student
                session['student_id'] = user['id']
                session['student_name'] = user['fullname']
                session['student_picture'] = user['picture']
                session['student_level'] = user['level']
                session['first_visit'] = True  # don notification na farko

                flash(f"Welcome {user['fullname']}!", "success")
                return redirect(url_for("student_dashboard"))
            else:
                flash("Invalid login credentials for student.", "danger")
                return redirect(url_for("login"))

        elif login_type == "admin":
            # Admin login: check username
            c.execute("SELECT * FROM admin WHERE username=? AND password=?", (identifier, password))
            admin = c.fetchone()
            conn.close()
            if admin:
                # ✅ Set session for admin
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['fullname']
                session['admin_picture'] = admin['picture']

                flash(f"Welcome Admin {admin['fullname']}!", "success")
                return redirect(url_for("admin_dashboard"))
            else:
                flash("Invalid login credentials for admin.", "danger")
                return redirect(url_for("login"))
        else:
            flash("Invalid login type selected.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/student/dashboard")
def student_dashboard():
    # check if student is logged in
    student_id = session.get('student_id')
    if not student_id:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    conn.close()

    # First visit notification
    first_visit = session.get('first_visit', False)
    if first_visit:
        session['first_visit'] = False  # saita zuwa False bayan an nuna notification

    return render_template("student_dashboard.html", student=student, first_visit=first_visit)

# Route: Admin Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    # Tabbatar admin yana logged in
    if not session.get("admin_id"):
        flash("Please login as admin first.", "danger")
        return redirect(url_for("login"))

    admin_id = session.get("admin_id")
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admin WHERE id=?", (admin_id,)).fetchone()
    conn.close()

    return render_template("admin_dashboard.html", admin=admin)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form['identifier']  # Admission / Phone / NIN
        secret_answer = request.form['secret_answer']
        new_password = request.form['new_password']

        conn = get_db_connection()
        c = conn.cursor()
        # Check student
        c.execute("""
            SELECT * FROM students WHERE (admission_number=? OR phone=? OR nin=?) AND secret_answer=?
        """, (identifier, identifier, identifier, secret_answer))
        student = c.fetchone()
        if student:
            # Insert request
            c.execute("""
                INSERT INTO forgot_password_requests (student_id, new_password, request_date)
                VALUES (?, ?, ?)
            """, (student['id'], new_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            flash("Your password reset request has been sent. Admin will review it.", "success")
            return redirect(url_for("login"))
        else:
            conn.close()
            flash("Invalid details. Please check Admission Number / Phone / NIN and secret answer.", "danger")
            return redirect(url_for("forgot_password"))

    return render_template("forgot_password.html")

@app.route("/admin/password_requests")
def admin_password_requests():
    admin_id = session.get("admin_id")  # assume admin login session
    if not admin_id:
        flash("Please login first.", "danger")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    c = conn.cursor()
    
    # Samu admin info
    admin = c.execute("SELECT * FROM admin WHERE id=?", (admin_id,)).fetchone()
    
    # Samu pending password requests
    c.execute("""
        SELECT fpr.id, s.fullname, s.admission_number, fpr.new_password, fpr.status, fpr.request_date
        FROM forgot_password_requests fpr
        JOIN students s ON fpr.student_id = s.id
        WHERE fpr.status='Pending'
    """)
    requests = c.fetchall()
    conn.close()

    return render_template(
        "admin_password_requests.html",
        requests=requests,
        admin=admin  # <-- tura admin zuwa template
    )

@app.route("/admin/password_requests/<int:request_id>/<action>", methods=["POST"])
def admin_handle_request(request_id, action):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM forgot_password_requests WHERE id=?", (request_id,))
    req = c.fetchone()
    if not req:
        conn.close()
        flash("Request not found.", "danger")
        return redirect(url_for("admin_password_requests"))

    if action == "approve":
        # update student's password
        c.execute("UPDATE students SET password=? WHERE id=?", (req['new_password'], req['student_id']))
        c.execute("""
            UPDATE forgot_password_requests 
            SET status='Approved', decision_date=? 
            WHERE id=?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request_id))
        flash("Password reset approved.", "success")

    elif action == "reject":
        reason = request.form.get("reason", "No reason provided")
        c.execute("""
            UPDATE forgot_password_requests
            SET status='Rejected', reason=?, decision_date=?
            WHERE id=?
        """, (reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request_id))
        flash("Password reset rejected.", "info")

    conn.commit()
    conn.close()
    return redirect(url_for("admin_password_requests"))

@app.route("/student/notifications")
def student_notifications():
    student_id = request.args.get("student_id")  # Idan kana session management, zaka iya dauka daga session
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT new_password, status, reason, decision_date
        FROM forgot_password_requests
        WHERE student_id=?
        ORDER BY decision_date DESC
    """, (student_id,))
    notifications = c.fetchall()
    conn.close()
    return render_template("student_notifications.html", notifications=notifications)

# ROUTE: Student View Profile
@app.route("/student/profile")
def view_profile():
    # Assume student_id is stored in session after login
    from flask import session

    if 'student_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for("login"))

    student_id = session['student_id']

    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    conn.close()

    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for("login"))

    return render_template("student_profile.html", student=student)

@app.route("/exam/pin", methods=["GET","POST"])
def exam_pin():
    student_id = session.get("student_id")
    if not student_id:
        flash("Please login first.")
        return redirect("/login")  # ko student dashboard/login page

    if request.method == "POST":
        pin = request.form["pin"]
        conn = get_db_connection()
        s = conn.execute(
            "SELECT * FROM students WHERE id=? AND pin=?",
            (student_id, pin)
        ).fetchone()
        conn.close()

        if s:
            session["exam_verified"] = True
            return redirect("/exam/courses")
        else:
            flash("Invalid PIN")

    return render_template("exam_pin.html")

@app.route("/exam/forgot-pin", methods=["GET","POST"])
def forgot_pin():
    if request.method == "POST":
        admission = request.form["admission"]
        nin = request.form["nin"]
        new_pin = request.form["new_pin"]

        conn = get_db_connection()
        conn.execute("""
        UPDATE students SET pin=?
        WHERE admission_number=? AND nin=?
        """,(new_pin, admission, nin))
        conn.commit()
        conn.close()

        flash("PIN reset successful")
        return redirect("/exam/pin")

    return render_template("forgot_pin.html")

@app.route("/exam/courses", methods=["GET","POST"])
def exam_courses():
    if not session.get("exam_verified"):
        return redirect("/exam/pin")

    student_id = session["student_id"]
    conn = get_db_connection()
    student = conn.execute(
        "SELECT level FROM students WHERE id=?", (student_id,)
    ).fetchone()
    student_level = str(student["level"])  # ko int, idan level int

    # fetch courses matching student's level
    courses = conn.execute(
        "SELECT * FROM courses WHERE level=?", (student_level,)
    ).fetchall()
    conn.close()

    if request.method == "POST":
        session["course_id"] = request.form["course_id"]
        return redirect("/exam/instruction")

    return render_template("exam_courses.html", courses=courses)

@app.route("/exam/instruction", methods=["GET","POST"])
def exam_instruction():
    if request.method == "POST":
        return redirect("/exam/start")
    return render_template("exam_instruction.html")

@app.route("/exam/start", methods=["GET", "POST"])
def exam_page():
    course_id = session.get("course_id")
    student_id = session.get("student_id")

    if not course_id:
        flash("Please select a course first.")
        return redirect("/exam/courses")

    conn = get_db_connection()

    if request.method == "GET":
        questions = conn.execute("""
            SELECT * FROM exam_questions
            WHERE course_id=?
            ORDER BY RANDOM()
            LIMIT 60
        """, (course_id,)).fetchall()

        session["exam_questions"] = [q["id"] for q in questions]

        conn.close()
        return render_template("exam_page.html", questions=questions)

    # POST
    question_ids = session.get("exam_questions")

    questions = conn.execute(
        f"SELECT * FROM exam_questions WHERE id IN ({','.join(['?']*len(question_ids))})",
        question_ids
    ).fetchall()

    score = 0
    for q in questions:
        ans = request.form.get(str(q["id"]))
        correct = 1 if ans == q["correct_answer"] else 0
        score += correct

        conn.execute("""
            INSERT INTO exam_answers
            (student_id, course_id, question_id, selected_answer, is_correct)
            VALUES (?,?,?,?,?)
        """, (student_id, course_id, q["id"], ans, correct))

    conn.execute("""
        INSERT INTO exam_attempted
        (student_id, course_id, score, date_taken)
        VALUES (?,?,?,?)
    """, (student_id, course_id, score,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

    session.pop("exam_questions", None)

    return redirect("/exam/done")

@app.route("/exam/done")
def exam_done():
    return render_template("exam_done.html")

@app.route("/student/results")
def view_results():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()

    # Samu duk courses da student ya yi exam
    courses = conn.execute("""
        SELECT DISTINCT c.id, c.course_code, c.course_title
        FROM exam_attempted ea
        JOIN courses c ON ea.course_id = c.id
        WHERE ea.student_id=?
    """, (student_id,)).fetchall()

    student_results = []

    for course in courses:
        # Duba status daga admin
        status_row = conn.execute(
            "SELECT status, reason FROM results_status WHERE student_id=? AND course_id=?",
            (student_id, course["id"])
        ).fetchone()

        if not status_row or status_row["status"] == "Pending":
            # Baza nuna questions ba, kawai message
            student_results.append({
                "course": course,
                "results": [],
                "total_questions": 0,
                "score": 0,
                "percentage": 0,
                "gpa": 0,
                "status": "Pending",
                "reason": ""
            })
            continue

        # Samu questions + student answers
        questions = conn.execute(
            "SELECT * FROM exam_questions WHERE course_id=? ORDER BY id ASC",
            (course["id"],)
        ).fetchall()

        answers_dict = {a["question_id"]: a for a in conn.execute(
            "SELECT * FROM exam_answers WHERE student_id=? AND course_id=?",
            (student_id, course["id"])
        ).fetchall()}

        results = []
        correct_count = 0

        for q in questions:
            a = answers_dict.get(q["id"])
            if a:
                selected = a["selected_answer"]
                is_correct = a["is_correct"]
                score = 1 if is_correct else 0
                grade = "Correct" if is_correct else "Wrong"
            else:
                selected = None
                score = 0
                grade = "Not Answered"

            if grade=="Correct": correct_count+=1

            results.append({
                "question_text": q["question_text"],
                "selected_answer": selected,
                "correct_answer": q["correct_answer"],
                "score": score,
                "grade": grade
            })

        total_questions = len(questions)
        total_score = correct_count
        percentage = round((total_score/total_questions)*100,2) if total_questions>0 else 0
        gpa = round((total_score/total_questions)*5,2) if total_questions>0 else 0

        student_results.append({
            "course": course,
            "results": results,
            "total_questions": total_questions,
            "score": total_score,
            "percentage": percentage,
            "gpa": gpa,
            "status": status_row["status"],
            "reason": status_row["reason"]
        })

    conn.close()
    return render_template("view_results.html", student=student, student_results=student_results)

@app.route("/student/change_password", methods=["GET","POST"])
def change_password_request():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    request_status = conn.execute("SELECT * FROM password_requests WHERE student_id=? ORDER BY id DESC LIMIT 1", (student_id,)).fetchone()

    if request.method == "POST":
        new_password = request.form['new_password']
        conn.execute("""
            INSERT INTO password_requests (student_id, new_password, status, reason, created_at)
            VALUES (?, ?, 'Pending', '', ?)
        """, (student_id, new_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        flash("Your password change request has been submitted. Wait for admin approval.", "success")
        return redirect(url_for("change_password_request"))

    conn.close()
    return render_template("change_password_request.html", student=student, request_status=request_status)

@app.route("/student/fees")
def payment_invoice():
    student_id = session.get('student_id')
    if not student_id:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    fees = conn.execute("SELECT * FROM fees WHERE student_id=? ORDER BY id DESC", (student_id,)).fetchall()
    conn.close()
    return render_template("payment_invoice.html", student=student, fees=fees)

@app.route("/admin/fees", methods=["GET", "POST"])
def admin_fees():
    conn = get_db_connection()
    c = conn.cursor()

    # Get departments and levels
    c.execute("SELECT DISTINCT department FROM students")
    departments = [d['department'] for d in c.fetchall()]
    c.execute("SELECT DISTINCT level FROM students")
    levels = [l['level'] for l in c.fetchall()]

    if request.method == "POST":
        department = request.form["department"]
        level = request.form["level"]
        amount = float(request.form["amount"])
        session_text = request.form.get("session", "2025/2026")  # default session
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get all students in that department & level
        students = c.execute("SELECT id FROM students WHERE department=? AND level=?",
                             (department, level)).fetchall()

        for s in students:
            c.execute("""
                INSERT INTO fees (student_id, amount, session, status, date_paid)
                VALUES (?, ?, ?, ?, ?)
            """, (s['id'], amount, session_text, "Pending", None))
        conn.commit()
        flash("Fees assigned successfully!", "success")
        return redirect(url_for("admin_fees"))

    # Get all fees records with student info
    c.execute("""
        SELECT f.id, s.fullname, s.admission_number, s.department, s.level, s.picture, 
               f.amount, f.status, f.date_paid, f.session
        FROM fees f
        JOIN students s ON f.student_id = s.id
        ORDER BY f.date_paid DESC
    """)
    fees_records = c.fetchall()
    conn.close()
    return render_template("admin_fees.html", departments=departments, levels=levels, fees_records=fees_records)

@app.route("/admin/fees/mark_paid/<int:fee_id>", methods=["POST"])
def admin_mark_fee_paid(fee_id):
    conn = get_db_connection()
    from datetime import datetime
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE fees SET status='Paid', date_paid=? WHERE id=?", (date_now, fee_id))
    conn.commit()
    conn.close()
    return {"success": True, "date_paid": date_now}

@app.route("/admin/student/results")
def admin_student_results():
    conn = get_db_connection()
    results = conn.execute("""
        SELECT DISTINCT s.id AS student_id, s.fullname,
                        c.id AS course_id, c.course_code
        FROM exam_attempted ea
        JOIN students s ON ea.student_id = s.id
        JOIN courses c ON ea.course_id = c.id
    """).fetchall()
    conn.close()
    return render_template("admin_student_results.html", results=results)

@app.route("/admin/student/results/<int:student_id>/<int:course_id>", methods=["GET", "POST"])
def admin_student_results_detail(student_id, course_id):
    conn = get_db_connection()

    # Samu student da course
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()

    # Samu duk questions na course
    questions = conn.execute(
        "SELECT * FROM exam_questions WHERE course_id=? ORDER BY id ASC",
        (course_id,)
    ).fetchall()

    # Samu answers na student
    answers_dict = {a["question_id"]: a for a in conn.execute(
        "SELECT * FROM exam_answers WHERE student_id=? AND course_id=?",
        (student_id, course_id)
    ).fetchall()}

    results = []
    for q in questions:
        a = answers_dict.get(q["id"])
        if a:
            selected = a["selected_answer"]
            is_correct = a["is_correct"]
            score = 1 if is_correct else 0
            grade = "Correct" if is_correct else "Wrong"
        else:
            selected = None
            score = 0
            grade = "Not Answered"

        results.append({
            "question_id": q["id"],
            "question_text": q["question_text"],
            "selected_answer": selected,
            "correct_answer": q["correct_answer"],
            "score": score,
            "grade": grade
        })

    # Samu status na approval daga results_status table
    status_row = conn.execute(
        "SELECT status, reason FROM results_status WHERE student_id=? AND course_id=?",
        (student_id, course_id)
    ).fetchone()
    current_status = status_row["status"] if status_row else None
    current_reason = status_row["reason"] if status_row else ""

    if request.method == "POST":
        status = request.form["status"]  # Approved / Rejected
        reason = request.form.get("reason", "")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert or update results_status
        conn.execute("""
            INSERT INTO results_status (student_id, course_id, status, reason, date_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id, course_id) DO UPDATE SET
                status=excluded.status,
                reason=excluded.reason,
                date_updated=excluded.date_updated
        """, (student_id, course_id, status, reason, now))

        conn.commit()
        flash("Result updated successfully!", "success")
        return redirect(f"/admin/student/results/{student_id}/{course_id}")

    conn.close()
    return render_template(
        "admin_student_results_detail.html",
        student=student,
        course=course,
        results=results,
        current_status=current_status,
        current_reason=current_reason
    )

@app.route("/admin/students")
def admin_view_students():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return render_template(
        "admin_view_students.html",
        students=students
    )

@app.route("/admin/students/delete/<int:student_id>", methods=["POST"])
def admin_delete_student(student_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()

    flash("Student deleted successfully.", "success")
    return redirect(url_for("admin_view_students"))

@app.route("/admin/profile")
def admin_profile():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    admin_id = session["admin_id"]

    conn = get_db_connection()
    admin = conn.execute(
        "SELECT * FROM admin WHERE id=?",
        (admin_id,)
    ).fetchone()
    conn.close()

    return render_template(
        "admin_profile.html",
        admin=admin
    )

@app.route("/logout")
def logout():
    session.clear()  # Fitar da duk session
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))

# RUN APP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)