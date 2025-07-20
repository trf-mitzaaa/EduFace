import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pymysql
import os
import shutil
import bcrypt

def hash_password(plain_password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

# === CONFIG ===
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "yournewpassword"
DB_NAME = "school"
PHOTO_FOLDER = "student_photos"

def connect_db():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)

# --- Login Window ---
def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showerror("Error", "Te rog completează ambele câmpuri")
        return

    db = connect_db()
    cursor = db.cursor()

    try:
        # Check if user exists and is an admin using the user_roles table
        cursor.execute("""
            SELECT u.id, u.password 
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            WHERE u.username = %s AND ur.role = 'admin'
        """, (username,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Login Eșuat", "Credențiale invalide sau nu există contul.")
            return

        user_id, stored_password = result

        # If the stored password is not yet hashed (legacy password)
        if len(stored_password) < 50:  # Bcrypt hashes are ~60 chars
            if password == stored_password:
                # Update the password to hashed version
                hashed_password = hash_password(password)
                cursor.execute("UPDATE users SET password=%s WHERE id=%s",
                             (hashed_password, user_id))
                db.commit()
                messagebox.showinfo("Login Reușit", f"Bine ai venit, {username}")
                root.destroy()
                open_dashboard()
            else:
                messagebox.showerror("Login Eșuat", "Credențiale invalide.")
        else:
            # Password is already hashed, verify it
            if verify_password(password, stored_password):
                messagebox.showinfo("Login Reușit", f"Bine ai venit, {username}")
                root.destroy()
                open_dashboard()
            else:
                messagebox.showerror("Login Eșuat", "Credențiale invalide.")

    except Exception as e:
        messagebox.showerror("Error", f"Eroare la conectarea cu baza de date: {str(e)}")
    finally:
        db.close()

# --- Admin Dashboard ---
def open_dashboard():
    def toggle_frame(frame, arrow_label):
        if frame.winfo_ismapped():
            frame.pack_forget()
            arrow_label.config(text="⯈")
        else:
            frame.pack(fill=tk.X, pady=(5, 10))
            arrow_label.config(text="⯆")

    dash = tk.Tk()
    dash.title("Meniu Admin")
    dash.geometry("900x700")
    dash.configure(bg="#f6f8fa")

    tk.Label(
        dash, text="Meniu Admin", font=("Segoe UI", 18, "bold"),
        bg="#324e7b", fg="white", pady=12
    ).pack(fill=tk.X)

    # === Button style
    btn_style = {
        "font": ("Segoe UI", 11, "bold"),
        "bg": "#3d5a80",
        "fg": "white",
        "activebackground": "#29354a",
        "activeforeground": "white",
        "bd": 0,
        "relief": "groove",
        "cursor": "hand2"
    }

    # === Main content frame
    content_frame = tk.Frame(dash, bg="#f6f8fa")
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # === Three columns
    utilizatori_col = tk.Frame(content_frame, bg="#f6f8fa")
    management_col = tk.Frame(content_frame, bg="#f6f8fa")
    elevi_col = tk.Frame(content_frame, bg="#f6f8fa")

    utilizatori_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
    management_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
    elevi_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

    def add_section(parent, title, buttons):
        frame = tk.Frame(parent, bg="#f6f8fa")

        # Create the arrow label separately to toggle it later
        arrow = tk.Label(frame, text="⯈", font=("Segoe UI", 12), bg="#3d5a80", fg="white")
        arrow.pack(side=tk.LEFT)

        toggle_btn = tk.Button(
            frame, text=title, **btn_style,
            command=lambda: toggle_frame(button_frame, arrow),
            width=25, height=2
        )
        toggle_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        frame.pack(pady=(0, 5), fill=tk.X)

        # Sub-button container
        button_frame = tk.Frame(parent, bg="#f6f8fa")

        for text, cmd in buttons:
            tk.Button(button_frame, text=text, command=cmd, **btn_style, width=25, height=2).pack(pady=4)

    # === Populate columns
    add_section(utilizatori_col, "Utilizatori", [
        ("Adaugă Elev", add_student_ui),
        ("Adaugă Profesor", add_teacher_ui),
        ("Adaugă Diriginte", add_head_teacher_ui),
    ])

    add_section(management_col, "Management Clasă", [
        ("Adaugă Clasă", add_class_ui),
        ("Adaugă Materie", add_subject_ui),
        ("Adaugă materie/clasă profesor", assign_teacher_ui),
        ("Șterge Materie", remove_subject_ui),
    ])

    add_section(elevi_col, "Elevi", [
        ("Șterge Notă", delete_grade_ui),
        ("Șterge Absență", delete_attendance_ui),
        ("Vizualizează Catalog", view_class_marksheet_ui),
        ("Promovează Elevii", promote_all_students),
    ])

    # === Exit Button at Bottom
    exit_frame = tk.Frame(dash, bg="#f6f8fa")
    exit_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=20)
    tk.Button(exit_frame, text="Ieșire", command=dash.destroy, **btn_style, width=30, height=2).pack()

    dash.mainloop()

# --- Add Student ---
def add_student_ui():
    def choose_photo():
        file_path = filedialog.askopenfilename(
            title="Selectează Poză",
            filetypes=[("Fișiere imagine", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            photo_path_var.set(file_path)
            photo_label.config(text=os.path.basename(file_path))

    def submit():
        db = connect_db()
        cursor = db.cursor()
        try:
            username_val = username.get().strip()
            password_val = password.get().strip()
            first = first_name.get().strip()
            last = last_name.get().strip()
            selected_class = class_combo.get()
            if not (username_val and password_val and first and last and selected_class):
                messagebox.showerror("Eroare", "Toate câmpurile sunt obligatorii.")
                return

            # Hash the password before storing
            hashed_password = hash_password(password_val)

            # Insert into users WITHOUT role!
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                           (username_val, hashed_password))
            user_id = cursor.lastrowid

            # Add the student role in user_roles
            cursor.execute("INSERT INTO user_roles (user_id, role) VALUES (%s, 'student')", (user_id,))

            # Get class_id
            cursor.execute("SELECT id FROM classes WHERE name = %s", (selected_class,))
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Eroare", "Clasa nu a fost găsită în baza de date.")
                return
            class_id = row[0]

            photo_file = photo_path_var.get()
            if photo_file:
                os.makedirs(PHOTO_FOLDER, exist_ok=True)
                ext = os.path.splitext(photo_file)[1]
                safe_name = f"{first}_{last}_{selected_class}{ext}".replace(" ", "_")
                save_path = os.path.join(PHOTO_FOLDER, safe_name)
                shutil.copy(photo_file, save_path)
                db_photo = safe_name
            else:
                db_photo = None

            # Add student (with user_id)
            cursor.execute(
                "INSERT INTO students (first_name, last_name, class_id, photo, user_id) VALUES (%s, %s, %s, %s, %s)",
                (first, last, class_id, db_photo, user_id)
            )
            student_id = cursor.lastrowid

            # Add to attendance_current as absent (0)
            cursor.execute(
                "INSERT INTO attendance_current (student_id, present) VALUES (%s, 0)",
                (student_id,)
            )

            db.commit()
            messagebox.showinfo("Succes", "Elevul a fost adăugat.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
            db.rollback()
        db.close()

    win = tk.Toplevel()
    win.title("Adaugă Elev")
    win.geometry("420x310")
    win.configure(bg="#f0f6fa")

    tk.Label(win, text="Utilizator", bg="#f0f6fa").grid(row=0, column=0, padx=6, pady=8, sticky="e")
    username = tk.Entry(win)
    username.grid(row=0, column=1, padx=6, pady=8)
    tk.Label(win, text="Parolă", bg="#f0f6fa").grid(row=1, column=0, padx=6, pady=8, sticky="e")
    password = tk.Entry(win)
    password.grid(row=1, column=1, padx=6, pady=8)
    tk.Label(win, text="Prenume", bg="#f0f6fa").grid(row=2, column=0, padx=6, pady=8, sticky="e")
    first_name = tk.Entry(win)
    first_name.grid(row=2, column=1, padx=6, pady=8)
    tk.Label(win, text="Nume", bg="#f0f6fa").grid(row=3, column=0, padx=6, pady=8, sticky="e")
    last_name = tk.Entry(win)
    last_name.grid(row=3, column=1, padx=6, pady=8)
    tk.Label(win, text="Clasă", bg="#f0f6fa").grid(row=4, column=0, padx=6, pady=8, sticky="e")
    class_combo = ttk.Combobox(win, state="readonly")
    class_combo.grid(row=4, column=1, padx=6, pady=8)
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM classes ORDER BY name")
    class_combo['values'] = [row[0] for row in cursor.fetchall()]
    db.close()
    tk.Label(win, text="Poză", bg="#f0f6fa").grid(row=5, column=0, padx=6, pady=8, sticky="e")
    photo_path_var = tk.StringVar()
    photo_label = tk.Label(win, text="Nicio poză selectată", bg="#f0f6fa")
    photo_label.grid(row=5, column=1)
    tk.Button(win, text="Alege Poză", command=choose_photo, bg="#aacfe3").grid(row=5, column=2)
    tk.Button(win, text="Adaugă", command=submit, bg="#264653", fg="white").grid(row=6, columnspan=3, pady=15)

# --- Adaugă Profesor ---
def add_teacher_ui():
    assignments = []

    def add_assignment():
        db = connect_db()
        cur = db.cursor()
        cur.execute("SELECT id, name FROM classes ORDER BY name")
        class_choices = cur.fetchall()
        cur.execute("SELECT id, name FROM subjects ORDER BY name")
        subject_choices = cur.fetchall()
        db.close()

        assign_win = tk.Toplevel(win)
        assign_win.title("Atribuire Clasă și Materie")
        tk.Label(assign_win, text="Clasă").grid(row=0, column=0, padx=6, pady=6)
        class_combo = ttk.Combobox(assign_win, state="readonly",
                                   values=[f"{cid} - {cname}" for cid, cname in class_choices])
        class_combo.grid(row=0, column=1, padx=6, pady=6)
        tk.Label(assign_win, text="Materie").grid(row=1, column=0, padx=6, pady=6)
        subject_combo = ttk.Combobox(assign_win, state="readonly",
                                     values=[f"{sid} - {sname}" for sid, sname in subject_choices])
        subject_combo.grid(row=1, column=1, padx=6, pady=6)

        def confirm():
            if not class_combo.get() or not subject_combo.get():
                messagebox.showerror("Eroare", "Alegeți clasa și materia.")
                return
            assignments.append((class_combo.get(), subject_combo.get()))
            assign_win.destroy()

        tk.Button(assign_win, text="Adaugă Atribuire", command=confirm).grid(row=2, columnspan=2, pady=10)

    def submit():
        db = connect_db()
        cursor = db.cursor()
        try:
            username_val = username.get().strip()
            password_val = password.get().strip()
            first = first_name.get().strip()
            last = last_name.get().strip()
            if not (username_val and password_val and first and last):
                messagebox.showerror("Eroare", "Completați toate câmpurile.")
                return

            # Hash the password before storing
            hashed_password = hash_password(password_val)

            # Insert into users WITHOUT role!
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                           (username_val, hashed_password))
            user_id = cursor.lastrowid

            # Add the teacher role in user_roles
            cursor.execute("INSERT INTO user_roles (user_id, role) VALUES (%s, 'teacher')", (user_id,))

            # Insert into teachers table
            cursor.execute(
                "INSERT INTO teachers (id, first_name, last_name) VALUES (%s, %s, %s)",
                (user_id, first, last)
            )

            # Save assignments
            for class_val, subject_val in assignments:
                # Extract just the ID from the string (everything before the ' - ')
                class_id = class_val.split(" - ")[0]
                subject_id = subject_val.split(" - ")[0]
                cursor.execute(
                    "INSERT INTO teacher_assignments (teacher_id, class_id, subject_id) VALUES (%s, %s, %s)",
                    (user_id, class_id, subject_id)
                )
            db.commit()
            messagebox.showinfo("Succes", "Profesorul și atribuirea au fost adăugate.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
            db.rollback()
        finally:
            cursor.close()
            db.close()

    win = tk.Toplevel()
    win.title("Adaugă Profesor")
    win.geometry("410x310")
    win.configure(bg="#f0f6fa")

    tk.Label(win, text="Utilizator", bg="#f0f6fa").grid(row=0, column=0, padx=6, pady=8, sticky="e")
    username = tk.Entry(win)
    username.grid(row=0, column=1, padx=6, pady=8)

    tk.Label(win, text="Parolă", bg="#f0f6fa").grid(row=1, column=0, padx=6, pady=8, sticky="e")
    password = tk.Entry(win, show="*")  # Hide password with asterisks
    password.grid(row=1, column=1, padx=6, pady=8)

    tk.Label(win, text="Prenume", bg="#f0f6fa").grid(row=2, column=0, padx=6, pady=8, sticky="e")
    first_name = tk.Entry(win)
    first_name.grid(row=2, column=1, padx=6, pady=8)

    tk.Label(win, text="Nume", bg="#f0f6fa").grid(row=3, column=0, padx=6, pady=8, sticky="e")
    last_name = tk.Entry(win)
    last_name.grid(row=3, column=1, padx=6, pady=8)

    assign_label = tk.Label(win, text="Atribuiri (clasă + materie):", bg="#f0f6fa")
    assign_label.grid(row=4, column=0, padx=6, pady=8, sticky="e")
    tk.Button(win, text="Adaugă Atribuire", command=add_assignment).grid(row=4, column=1, padx=6, pady=8, sticky="w")

    tk.Button(win, text="Adaugă", command=submit, bg="#264653", fg="white").grid(row=5, columnspan=2, pady=15)

# --- Adaugă Diriginte ---
def add_head_teacher_ui():
    def submit():
        db = connect_db()
        cursor = db.cursor()
        try:
            username_val = username.get().strip()
            password_val = password.get().strip()
            first = first_name.get().strip()
            last = last_name.get().strip()
            class_val = class_combo.get()
            # This line splits "6 - 9d" into ["6", "9d"] and takes "6"
            class_id = class_val.split(" - ")[0]

            if not (username_val and password_val and first and last and class_val):
                messagebox.showerror("Eroare", "Completați toate câmpurile.")
                return

            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username_val,))
            existing_user = cursor.fetchone()

            if existing_user:
                # User exists, check if they're a teacher
                user_id = existing_user[0]
                cursor.execute("SELECT role FROM user_roles WHERE user_id = %s", (user_id,))
                roles = [r[0] for r in cursor.fetchall()]

                if 'head_teacher' in roles:
                    messagebox.showerror("Eroare", "Acest utilizator este deja diriginte.")
                    return

                # Add head_teacher role
                cursor.execute("INSERT INTO user_roles (user_id, role) VALUES (%s, 'head_teacher')",
                               (user_id,))

                # Extract class ID from the combo selection
                class_id = class_val.split(" - ")[0]

                # Add to head_teachers table
                cursor.execute(
                    "INSERT INTO head_teachers (id, first_name, last_name, class) VALUES (%s, %s, %s, %s)",
                    (user_id, first, last, class_id)
                )
            else:
                # Create new user
                hashed_password = hash_password(password_val)
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                               (username_val, hashed_password))
                user_id = cursor.lastrowid

                # Add head_teacher role
                cursor.execute("INSERT INTO user_roles (user_id, role) VALUES (%s, 'head_teacher')",
                               (user_id,))

                # Extract class ID from the combo selection
                class_id = class_val.split(" - ")[0]

                # Add to head_teachers table
                cursor.execute(
                    "INSERT INTO head_teachers (id, first_name, last_name, class) VALUES (%s, %s, %s, %s)",
                    (user_id, first, last, class_id)
                )

            db.commit()
            messagebox.showinfo("Succes", "Dirigintele a fost adăugat!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
            db.rollback()
        finally:
            cursor.close()
            db.close()

    win = tk.Toplevel()
    win.title("Adaugă Diriginte")
    win.geometry("400x220")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Utilizator", bg="#f0f6fa").grid(row=0, column=0, padx=6, pady=8, sticky="e")
    username = tk.Entry(win)
    username.grid(row=0, column=1, padx=6, pady=8)
    tk.Label(win, text="Parolă", bg="#f0f6fa").grid(row=1, column=0, padx=6, pady=8, sticky="e")
    password = tk.Entry(win)
    password.grid(row=1, column=1, padx=6, pady=8)
    tk.Label(win, text="Prenume", bg="#f0f6fa").grid(row=2, column=0, padx=6, pady=8, sticky="e")
    first_name = tk.Entry(win)
    first_name.grid(row=2, column=1, padx=6, pady=8)
    tk.Label(win, text="Nume", bg="#f0f6fa").grid(row=3, column=0, padx=6, pady=8, sticky="e")
    last_name = tk.Entry(win)
    last_name.grid(row=3, column=1, padx=6, pady=8)
    tk.Label(win, text="Clasă", bg="#f0f6fa").grid(row=4, column=0, padx=6, pady=8, sticky="e")
    class_combo = ttk.Combobox(win, state="readonly")
    class_combo.grid(row=4, column=1, padx=6, pady=8)
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM classes ORDER BY name")
    class_combo['values'] = [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]
    db.close()
    tk.Button(win, text="Adaugă", command=submit, bg="#264653", fg="white").grid(row=5, columnspan=2, pady=15)
    
def add_class_ui():
    win = tk.Toplevel()
    win.title("Adaugă Clasă")
    win.geometry("300x130")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Numele clasei (ex: 9A)", bg="#f0f6fa").pack(pady=10)
    class_entry = tk.Entry(win, font=("Segoe UI", 12))
    class_entry.pack(pady=4)

    def submit():
        cname = class_entry.get().strip()
        if not cname:
            messagebox.showerror("Eroare", "Numele clasei este obligatoriu.")
            return
        db = connect_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO classes (name) VALUES (%s)", (cname,))
            db.commit()
            messagebox.showinfo("Succes", f"Clasa „{cname}” a fost adăugată.")
            win.destroy()
        except pymysql.err.IntegrityError:
            messagebox.showerror("Eroare", "Această clasă există deja!")
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
        db.close()
    tk.Button(win, text="Adaugă", command=submit, bg="#264653", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=8)


def add_subject_ui():
    win = tk.Toplevel()
    win.title("Adaugă Materie")
    win.geometry("300x130")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Numele materiei", bg="#f0f6fa").pack(pady=10)
    subject_entry = tk.Entry(win, font=("Segoe UI", 12))
    subject_entry.pack(pady=4)
    def submit():
        name = subject_entry.get().strip()
        if not name:
            messagebox.showerror("Eroare", "Numele materiei este obligatoriu.")
            return
        db = connect_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO subjects (name) VALUES (%s)", (name,))
            db.commit()
            messagebox.showinfo("Succes", f"Materia „{name}” a fost adăugată.")
            win.destroy()
        except pymysql.err.IntegrityError:
            messagebox.showerror("Eroare", "Această materie există deja!")
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
        db.close()
    tk.Button(win, text="Adaugă", command=submit, bg="#264653", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=8)

def assign_teacher_ui():
    db = connect_db()
    cursor = db.cursor()
    # Get all teachers
    cursor.execute("SELECT t.id, t.first_name, t.last_name FROM teachers t")
    teachers = cursor.fetchall()
    # Get all classes
    cursor.execute("SELECT id, name FROM classes")
    classes = cursor.fetchall()
    # Get all subjects
    cursor.execute("SELECT id, name FROM subjects")
    subjects = cursor.fetchall()
    db.close()

    win = tk.Toplevel()
    win.title("Asignează profesor la clasă/materie")
    win.geometry("410x260")
    win.configure(bg="#f0f6fa")

    tk.Label(win, text="Profesor", bg="#f0f6fa").grid(row=0, column=0, padx=7, pady=14, sticky="e")
    teacher_combo = ttk.Combobox(win, state="readonly", width=27)
    teacher_combo["values"] = [f"{tid} - {fn} {ln}" for tid, fn, ln in teachers]
    teacher_combo.grid(row=0, column=1, padx=7, pady=14)

    tk.Label(win, text="Clasă", bg="#f0f6fa").grid(row=1, column=0, padx=7, pady=14, sticky="e")
    class_combo = ttk.Combobox(win, state="readonly", width=27)
    class_combo["values"] = [f"{cid} - {name}" for cid, name in classes]
    class_combo.grid(row=1, column=1, padx=7, pady=14)

    tk.Label(win, text="Materie", bg="#f0f6fa").grid(row=2, column=0, padx=7, pady=14, sticky="e")
    subject_combo = ttk.Combobox(win, state="readonly", width=27)
    subject_combo["values"] = [f"{sid} - {name}" for sid, name in subjects]
    subject_combo.grid(row=2, column=1, padx=7, pady=14)

    def assign():
        if not (teacher_combo.get() and class_combo.get() and subject_combo.get()):
            messagebox.showerror("Eroare", "Completează toate câmpurile.")
            return
        teacher_id = int(teacher_combo.get().split(" - ")[0])
        class_id = int(class_combo.get().split(" - ")[0])
        subject_id = int(subject_combo.get().split(" - ")[0])
        db = connect_db()
        cursor = db.cursor()
        # Prevent duplicate assignment
        cursor.execute("""
            SELECT id FROM teacher_assignments
            WHERE teacher_id=%s AND class_id=%s AND subject_id=%s
        """, (teacher_id, class_id, subject_id))
        if cursor.fetchone():
            db.close()
            messagebox.showwarning("Atenție", "Acest profesor este deja asignat la această clasă și materie.")
            return
        cursor.execute("""
            INSERT INTO teacher_assignments (teacher_id, class_id, subject_id)
            VALUES (%s, %s, %s)
        """, (teacher_id, class_id, subject_id))
        db.commit()
        db.close()
        messagebox.showinfo("Succes", "Profesorul a fost asignat cu succes!")
        win.destroy()

    tk.Button(win, text="Asignează", font=("Segoe UI", 11, "bold"),
              bg="#344675", fg="white", command=assign).grid(row=3, columnspan=2, pady=18)


def remove_subject_ui():
    win = tk.Toplevel()
    win.title("Șterge Materie")
    win.geometry("320x150")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Alege materia", bg="#f0f6fa").pack(pady=10)
    db = connect_db()
    cur = db.cursor()
    cur.execute("SELECT id, name FROM subjects ORDER BY name")
    subs = cur.fetchall()
    db.close()
    sub_combo = ttk.Combobox(win, state="readonly", values=[f"{sid} - {name}" for sid, name in subs], width=28)
    sub_combo.pack(pady=5)
    def delete():
        if not sub_combo.get():
            return
        sub_id = int(sub_combo.get().split(" - ")[0])
        db2 = connect_db()
        cur2 = db2.cursor()
        try:
            cur2.execute("DELETE FROM subjects WHERE id=%s", (sub_id,))
            db2.commit()
            messagebox.showinfo("Succes", "Materia a fost ștearsă.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
        db2.close()
    tk.Button(win, text="Șterge", command=delete, bg="#b0413e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=12)


def delete_grade_ui():
    def load_subjects():
        db = connect_db(); cursor = db.cursor()
        cursor.execute("SELECT DISTINCT subject FROM grades")
        subjects = [row[0] for row in cursor.fetchall()]
        db.close()
        subject_combo["values"] = subjects

    def load_students(event=None):
        subject = subject_combo.get()
        if not subject:
            return
        db = connect_db(); cursor = db.cursor()
        cursor.execute("""
            SELECT DISTINCT s.id, s.first_name, s.last_name, c.name 
            FROM grades g
            JOIN students s ON g.student_id = s.id 
            JOIN classes c ON s.class_id = c.id 
            WHERE g.subject = %s
            ORDER BY c.name, s.last_name
        """, (subject,))
        students = cursor.fetchall(); db.close()
        student_combo["values"] = [f"{sid} - {first} {last} [{cls}]" for sid, first, last, cls in students]
        grade_combo.set("")
        grade_combo["values"] = []

    def load_grades(event=None):
        if not subject_combo.get() or not student_combo.get():
            return
        subject = subject_combo.get()
        student_id = int(student_combo.get().split(" - ")[0])
        db = connect_db(); cursor = db.cursor()
        cursor.execute("SELECT id, grade, date_given FROM grades WHERE student_id = %s AND subject = %s", (student_id, subject))
        grades = cursor.fetchall(); db.close()
        grade_combo["values"] = [
            f"{gid} - {grade} ({date.strftime('%d.%m.%Y')})" for gid, grade, date in grades
        ]

    def submit():
        if not grade_combo.get():
            messagebox.showerror("Eroare", "Selectează o notă pentru ștergere.")
            return
        grade_id = int(grade_combo.get().split(" - ")[0])
        db = connect_db(); cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM grades WHERE id = %s", (grade_id,))
            db.commit()
            messagebox.showinfo("Succes", "Nota a fost ștearsă.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
        db.close()

    win = tk.Toplevel()
    win.title("Șterge Notă")
    win.geometry("470x230")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Materie", bg="#f0f6fa").grid(row=0, column=0, padx=6, pady=8, sticky="e")
    subject_combo = ttk.Combobox(win, state="readonly", width=32)
    subject_combo.grid(row=0, column=1, padx=6, pady=8)
    tk.Label(win, text="Elev", bg="#f0f6fa").grid(row=1, column=0, padx=6, pady=8, sticky="e")
    student_combo = ttk.Combobox(win, state="readonly", width=32)
    student_combo.grid(row=1, column=1, padx=6, pady=8)
    tk.Label(win, text="Notă", bg="#f0f6fa").grid(row=2, column=0, padx=6, pady=8, sticky="e")
    grade_combo = ttk.Combobox(win, state="readonly", width=32)
    grade_combo.grid(row=2, column=1, padx=6, pady=8)
    tk.Button(win, text="Șterge", command=submit, bg="#c44536", fg="white").grid(row=3, columnspan=2, pady=15)
    load_subjects()
    subject_combo.bind("<<ComboboxSelected>>", load_students)
    student_combo.bind("<<ComboboxSelected>>", load_grades)


def delete_attendance_ui():
    def load_subjects():
        db = connect_db(); cursor = db.cursor()
        cursor.execute("SELECT id, name FROM subjects")
        subjects = cursor.fetchall()
        db.close()
        subject_combo["values"] = [f"{sid} - {name}" for sid, name in subjects]

    def load_students(event=None):
        if not subject_combo.get():
            return
        subject_id = int(subject_combo.get().split(" - ")[0])
        db = connect_db(); cursor = db.cursor()
        cursor.execute("""
            SELECT DISTINCT s.id, s.first_name, s.last_name, c.name 
            FROM attendance_history ah
            JOIN students s ON ah.student_id = s.id 
            JOIN classes c ON s.class_id = c.id 
            WHERE ah.subject_id = %s
            ORDER BY c.name, s.last_name
        """, (subject_id,))
        students = cursor.fetchall(); db.close()
        student_combo["values"] = [f"{sid} - {first} {last} [{cls}]" for sid, first, last, cls in students]
        attendance_combo.set("")
        attendance_combo["values"] = []

    def load_attendance(event=None):
        if not subject_combo.get() or not student_combo.get():
            return
        subject_id = int(subject_combo.get().split(" - ")[0])
        student_id = int(student_combo.get().split(" - ")[0])
        db = connect_db(); cursor = db.cursor()
        cursor.execute("SELECT id, absent_date FROM attendance_history WHERE student_id = %s AND subject_id = %s", (student_id, subject_id))
        recs = cursor.fetchall(); db.close()
        attendance_combo["values"] = [
            f"{aid} - {date.strftime('%d.%m.%Y')}" for aid, date in recs
        ]

    def submit():
        if not attendance_combo.get():
            messagebox.showerror("Eroare", "Selectează o absență pentru ștergere.")
            return
        aid = int(attendance_combo.get().split(" - ")[0])
        db = connect_db(); cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM attendance_history WHERE id = %s", (aid,))
            db.commit()
            messagebox.showinfo("Succes", "Absența a fost ștearsă.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
        db.close()

    win = tk.Toplevel()
    win.title("Șterge Absență")
    win.geometry("470x230")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Materie", bg="#f0f6fa").grid(row=0, column=0, padx=6, pady=8, sticky="e")
    subject_combo = ttk.Combobox(win, state="readonly", width=32)
    subject_combo.grid(row=0, column=1, padx=6, pady=8)
    tk.Label(win, text="Elev", bg="#f0f6fa").grid(row=1, column=0, padx=6, pady=8, sticky="e")
    student_combo = ttk.Combobox(win, state="readonly", width=32)
    student_combo.grid(row=1, column=1, padx=6, pady=8)
    tk.Label(win, text="Absență", bg="#f0f6fa").grid(row=2, column=0, padx=6, pady=8, sticky="e")
    attendance_combo = ttk.Combobox(win, state="readonly", width=32)
    attendance_combo.grid(row=2, column=1, padx=6, pady=8)
    tk.Button(win, text="Șterge", command=submit, bg="#c44536", fg="white").grid(row=3, columnspan=2, pady=15)
    load_subjects()
    subject_combo.bind("<<ComboboxSelected>>", load_students)
    student_combo.bind("<<ComboboxSelected>>", load_attendance)

def view_class_marksheet_ui():
    win = tk.Toplevel()
    win.title("Catalogul clasei")
    win.geometry("900x550")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Clasa:", bg="#f0f6fa").pack()
    class_combo = ttk.Combobox(win, state="readonly", width=20)
    class_combo.pack()
    student_listbox = tk.Listbox(win, width=45, font=("Segoe UI",10))
    student_listbox.pack(pady=7)
    result_text = tk.Text(win, width=110, height=25, font=("Consolas",9), state=tk.DISABLED)
    result_text.pack(padx=7)

    db = connect_db(); cursor = db.cursor()
    cursor.execute("SELECT name FROM classes ORDER BY name")
    classes = [row[0] for row in cursor.fetchall()]
    db.close()
    class_combo["values"] = classes

    def load_students(event):
        selected_class = class_combo.get()
        db = connect_db(); cursor = db.cursor()
        cursor.execute("""
            SELECT s.id, s.first_name, s.last_name 
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE c.name = %s 
            ORDER BY s.last_name
        """, (selected_class,))
        students = cursor.fetchall(); db.close()
        student_listbox.delete(0, tk.END)
        for sid, first, last in students:
            student_listbox.insert(tk.END, f"{sid} - {first} {last}")

    def show_student_marks(event):
        selection = student_listbox.get(tk.ACTIVE)
        if not selection:
            return
        student_id = int(selection.split(" - ")[0])
        db = connect_db(); cursor = db.cursor()
        cursor.execute("""
            SELECT subject, grade, date_given
            FROM grades
            WHERE student_id = %s
            ORDER BY subject, date_given
        """, (student_id,))
        data = cursor.fetchall(); db.close()
        subject_map = {}
        for subject, grade, date in data:
            if subject not in subject_map:
                subject_map[subject] = []
            subject_map[subject].append((grade, date))
        result_text.config(state=tk.NORMAL)
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, f"ID elev: {student_id}\n")
        for subject, marks in subject_map.items():
            avg = sum(m[0] for m in marks) / len(marks)
            result_text.insert(tk.END, f"\nMaterie: {subject} (Media: {avg:.2f})\n")
            for grade, date in marks:
                result_text.insert(tk.END, f"  {date.strftime('%d.%m.%Y')} - Notă: {grade}\n")
        result_text.config(state=tk.DISABLED)

    class_combo.bind("<<ComboboxSelected>>", load_students)
    student_listbox.bind("<<ListboxSelect>>", show_student_marks)


def promote_all_students():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM classes")
    classes = cursor.fetchall()
    for class_id, name in classes:
        try:
            if len(name) < 2 or not name[:-1].isdigit():
                continue
            year = int(name[:-1])
            letter = name[-1]
            if year == 12:
                if year == 12:
                    # Gather all student ids and user ids in this class
                    cursor.execute("SELECT id, user_id FROM students WHERE class_id = %s", (class_id,))
                    graduating_students = cursor.fetchall()
                    for sid, uid in graduating_students:
                        cursor.execute("DELETE FROM grades WHERE student_id = %s", (sid,))
                        cursor.execute("DELETE FROM attendance_history WHERE student_id = %s", (sid,))
                        cursor.execute("DELETE FROM attendance_current WHERE student_id = %s", (sid,))
                        cursor.execute("DELETE FROM students WHERE id = %s", (sid,))
                    if uid:  # In case user_id is not NULL
                        cursor.execute("DELETE FROM users WHERE id = %s", (uid,))

            else:
                new_class_name = f"{year+1}{letter}"
                cursor.execute("SELECT id FROM classes WHERE name=%s", (new_class_name,))
                new_class = cursor.fetchone()
                if not new_class:
                    cursor.execute("INSERT INTO classes (name) VALUES (%s)", (new_class_name,))
                    new_class_id = cursor.lastrowid
                else:
                    new_class_id = new_class[0]
                # Promote students
                cursor.execute("SELECT id FROM students WHERE class_id=%s", (class_id,))
                students = cursor.fetchall()
                for (student_id,) in students:
                    cursor.execute("SELECT AVG(grade) FROM grades WHERE student_id=%s", (student_id,))
                    avg = cursor.fetchone()[0]
                    if avg is not None and avg >= 5.0:
                        cursor.execute("UPDATE students SET class_id=%s WHERE id=%s", (new_class_id, student_id))
                # Promote teachers for the class and their subjects
                cursor.execute("""
                    SELECT teacher_id, subject_id FROM teacher_assignments WHERE class_id=%s
                """, (class_id,))
                assignments = cursor.fetchall()
                for teacher_id, subject_id in assignments:
                    # Check if already assigned
                    cursor.execute("""
                        SELECT id FROM teacher_assignments WHERE class_id=%s AND teacher_id=%s AND subject_id=%s
                    """, (new_class_id, teacher_id, subject_id))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO teacher_assignments (teacher_id, class_id, subject_id)
                            VALUES (%s, %s, %s)
                        """, (teacher_id, new_class_id, subject_id))
        except Exception as e:
            print(f"Eroare promovare pentru clasa {name}: {e}")

    db.commit()
    db.close()
    messagebox.showinfo(
        "Promovare reușită",
        "Toți elevii eligibili au fost promovați!\nClasa a 12-a a absolvit.\nElevii cu medie sub 5 nu au fost promovați.\nProfesorii au fost promovați împreună cu clasele lor."
    )


# --- Fereastră de autentificare ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Autentificare Administrator")
    root.geometry("520x280")
    root.configure(bg="#f0f6fa")
    tk.Label(root, text="Autentificare Administrator", font=("Segoe UI",16,"bold"), bg="#324e7b", fg="white", pady=12).pack(fill=tk.X)
    tk.Label(root, text="Utilizator", font=("Segoe UI",11), bg="#f0f6fa").pack(pady=8)
    username_entry = tk.Entry(root, font=("Segoe UI",11))
    username_entry.pack()
    tk.Label(root, text="Parolă", font=("Segoe UI",11), bg="#f0f6fa").pack(pady=8)
    password_entry = tk.Entry(root, show='*', font=("Segoe UI",11))
    password_entry.pack()
    tk.Button(root, text="Autentificare", command=login, bg="#264653", fg="white", font=("Segoe UI",11,"bold"), width=17).pack(pady=22)
    root.mainloop()

