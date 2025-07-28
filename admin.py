import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pymysql
import os
import shutil
import bcrypt
import re


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
                       WHERE u.username = %s
                         AND ur.role = 'admin'
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


def manage_conduct_ui():
    win = tk.Toplevel()
    win.title("Nota de purtare")
    win.geometry("500x400")
    win.configure(bg="#f0f6fa")

    # ——— Clasă selector ———
    tk.Label(win, text="Selectează clasa:", bg="#f0f6fa", font=("Segoe UI", 11)).pack(pady=(10,4))
    class_combo = ttk.Combobox(win, state="readonly", width=30)
    class_combo.pack(pady=(0,10))

    # load lista de clase din DB
    db = connect_db(); cur = db.cursor()
    cur.execute("SELECT id, name FROM classes ORDER BY name")
    classes = cur.fetchall()
    cur.close(); db.close()
    class_combo['values'] = [f"{cid} - {cname}" for cid,cname in classes]

    # ——— Treeview pentru note purtare ———
    tree = ttk.Treeview(win, columns=("id","nume","grade"), show="headings", height=15)
    tree.heading("id",    text="ID")
    tree.heading("nume",  text="Elev")
    tree.heading("grade", text="Nota de purtare")
    tree.column("id",    width=40, anchor="center")
    tree.column("nume",  width=200)
    tree.column("grade", width=120, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))

    def load_grades():
        # golim orice rând vechi
        tree.delete(*tree.get_children())
        sel = class_combo.get()
        if not sel:
            return
        cls_id = sel.split(" - ")[0]
        db = connect_db(); cur = db.cursor()
        cur.execute("""
            SELECT s.id,
                   CONCAT(s.first_name,' ',s.last_name),
                   COALESCE(c.grade,10)
            FROM students s
            LEFT JOIN conduct_grades c ON c.student_id=s.id
            WHERE s.class_id=%s
            ORDER BY s.last_name, s.first_name
        """, (cls_id,))
        for sid, nume, sc in cur.fetchall():
            tree.insert("", "end", values=(sid, nume, sc))
        cur.close(); db.close()

    def on_double_click(event):
        item = tree.identify_row(event.y)
        if not item:
            return
        sid, nume, vechi = tree.item(item, "values")
        # convertește corect vechi la int
        try:
            vechi_int = int(float(vechi))
        except ValueError:
            vechi_int = 10
        nou = simpledialog.askinteger(
            "Modifică nota de purtare",
            f"Noua notă pentru {nume}:",
            initialvalue=vechi_int,
            minvalue=1, maxvalue=10,
            parent=win
        )
        if nou is None:
            return

        db = connect_db(); cur = db.cursor()
        cur.execute("""
            INSERT INTO conduct_grades(student_id, grade)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE grade=%s
        """, (sid, nou, nou))
        db.commit(); cur.close(); db.close()

        tree.set(item, "grade", nou)

    # legăm evenimentele
    class_combo.bind("<<ComboboxSelected>>", lambda e: load_grades())
    tree.bind("<Double-1>", on_double_click)

    # buton de reload manual
    tk.Button(win, text="Reîncarcă", command=load_grades, bg="#344675", fg="white").pack(pady=(0,8))

    win.transient(root)  # dacă vrei să modalați față de fereastra principală
    win.grab_set()
    win.wait_window()


# --- Admin Dashboard ---
def open_dashboard():
    dash = tk.Tk()
    dash.title("Meniu Admin")
    dash.geometry("900x700")
    dash.configure(bg="#f6f8fa")

    # 1) toggle helper stays nested
    def toggle_frame(frame, arrow_label):
        if frame.winfo_ismapped():
            frame.pack_forget()
            arrow_label.config(text="⯈")
        else:
            frame.pack(fill=tk.X, pady=(5, 10))
            arrow_label.config(text="⯆")

    # 2) Now *outside* of toggle_frame, define your UI:

    # title
    tk.Label(
        dash,
        text="Meniu Admin",
        font=("Segoe UI", 18, "bold"),
        bg="#324e7b",
        fg="white",
        pady=12
    ).pack(fill=tk.X)

    # button style
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

    # main three-column container
    content_frame = tk.Frame(dash, bg="#f6f8fa")
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    utilizatori_col = tk.Frame(content_frame, bg="#f6f8fa")
    management_col = tk.Frame(content_frame, bg="#f6f8fa")
    elevi_col = tk.Frame(content_frame, bg="#f6f8fa")

    utilizatori_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
    management_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
    elevi_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

    # helper to build each section
    def add_section(parent, title, buttons):
        frame = tk.Frame(parent, bg="#f6f8fa")
        arrow = tk.Label(frame, text="⯈", font=("Segoe UI", 12), bg="#3d5a80", fg="white")
        arrow.pack(side=tk.LEFT)
        toggle_btn = tk.Button(
            frame, text=title, **btn_style,
            command=lambda: toggle_frame(button_frame, arrow),
            width=25, height=2
        )
        toggle_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        frame.pack(pady=(0, 5), fill=tk.X)

        button_frame = tk.Frame(parent, bg="#f6f8fa")
        for text, cmd in buttons:
            tk.Button(button_frame, text=text, command=cmd, **btn_style, width=25, height=2).pack(pady=4)

    # now add your three sections
    add_section(utilizatori_col, "Utilizatori", [
        ("Adaugă Elev", add_student_ui),
        ("Adaugă Profesor", add_teacher_ui),
        ("Adaugă Diriginte", add_head_teacher_ui),
        ("Șterge Utilizator", delete_user_ui),
    ])

    add_section(management_col, "Management Clasă", [
        ("Adaugă Clasă", add_class_ui),
        ("Adaugă Materie", add_subject_ui),
        ("Șterge Materie", remove_subject_ui),
        ("Gestionare Atribuiri", assign_teacher_ui),
    ])

    add_section(elevi_col, "Elevi", [
        ("Șterge Notă", delete_grade_ui),
        ("Șterge Absență", delete_attendance_ui),
        ("Vizualizează Catalog", view_class_marksheet_ui),
        ("Promovează Elevii", confirm_and_promote),
        ("Nota de Purtare", manage_conduct_ui),
    ])

    # bottom buttons
    bottom = tk.Frame(dash, bg="#f6f8fa")
    bottom.pack(fill=tk.X, side=tk.BOTTOM, pady=20)
    tk.Button(bottom, text="Trimite Notificare", command=send_notification_ui,
              bg="#2a6786", fg="white", font=("Segoe UI", 11, "bold"), width=30, height=2).pack(pady=(0, 8))
    tk.Button(bottom, text="Ieșire", command=dash.destroy,
              bg="#b0413e", fg="white", font=("Segoe UI", 11, "bold"), width=30, height=2).pack()

    dash.mainloop()


def delete_user_ui():
    win = tk.Toplevel()
    win.title("Șterge Utilizator")
    win.geometry("450x200")
    win.configure(bg="#f0f6fa")

    tk.Label(win, text="Selectează utilizatorul de șters:", bg="#f0f6fa").pack(pady=(14, 6))
    combo = ttk.Combobox(win, width=40, state="readonly")
    combo.pack(pady=4)

    # Populăm dropdown-ul cu toți utilizatorii
    db = connect_db()
    cur = db.cursor()
    cur.execute("""
                SELECT u.id,
                       u.username,
                       COALESCE(s.first_name, t.first_name, h.first_name, '-') AS first,
               COALESCE(s.last_name,  t.last_name,  h.last_name,  '-') AS last
                FROM users u
                    LEFT JOIN students s
                ON u.id = s.user_id
                    LEFT JOIN teachers t ON u.id = t.id
                    LEFT JOIN head_teachers h ON u.id = h.id
                """)
    rows = cur.fetchall()
    db.close()

    user_map = {}
    for uid, uname, first, last in rows:
        label = f"{first} {last} — {uname}"
        combo['values'] = (*combo['values'], label)
        user_map[label] = uid

    def delete_user():
        sel = combo.get()
        if not sel:
            messagebox.showerror("Eroare", "Selectează un utilizator.")
            return
        uid = user_map[sel]
        if not messagebox.askyesno("Confirmare", f"Sigur vrei să ștergi {sel}?"):
            return

        db = connect_db()
        cur = db.cursor()
        try:
            # Ștergem toate rolurile și notificările
            cur.execute("DELETE FROM user_roles      WHERE user_id=%s", (uid,))
            cur.execute("DELETE FROM notifications   WHERE user_id=%s", (uid,))

            # Ștergem orice intrare de elev, profesor, diriginte
            cur.execute("DELETE FROM students         WHERE user_id=%s", (uid,))
            cur.execute("DELETE FROM teacher_assignments WHERE teacher_id=%s", (uid,))
            cur.execute("DELETE FROM teachers         WHERE id=%s", (uid,))
            cur.execute("DELETE FROM head_teachers    WHERE id=%s", (uid,))

            # În final ștergem utilizatorul
            cur.execute("DELETE FROM users            WHERE id=%s", (uid,))

            db.commit()
            messagebox.showinfo("Succes", f"Utilizatorul {sel} a fost șters.")
            win.destroy()

        except Exception as e:
            db.rollback()
            messagebox.showerror("Eroare", str(e))
        finally:
            cur.close()
            db.close()

    tk.Button(win, text="Șterge", command=delete_user, bg="#b0413e", fg="white", font=("Segoe UI", 11, "bold")).pack(
        pady=10)


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


def send_notification_ui():
    win = tk.Toplevel()
    win.title("Trimite Notificare")
    win.geometry("540x440")
    win.configure(bg="#f0f6fa")

    # === NOTIFICARE INDIVIDUALĂ CU CĂUTARE ===
    tk.Label(win, text="Trimite notificare individuală", font=("Segoe UI", 12, "bold"), bg="#f0f6fa").pack(pady=(14, 6))
    user_frame = tk.Frame(win, bg="#f0f6fa");
    user_frame.pack(pady=4)

    tk.Label(user_frame, text="Selectează utilizator:", bg="#f0f6fa").grid(row=0, column=0, padx=6, sticky="e")
    user_combo = ttk.Combobox(user_frame, width=42, state="readonly")
    user_combo.grid(row=0, column=1, padx=6)

    db = connect_db();
    cur = db.cursor()
    cur.execute("""
                SELECT u.id,
                       u.username,
                       COALESCE(s.first_name, t.first_name, h.first_name, '-') AS first,
               COALESCE(s.last_name, t.last_name, h.last_name, '-') AS last
                FROM users u
                    LEFT JOIN students s
                ON u.id = s.user_id
                    LEFT JOIN teachers t ON u.id = t.id
                    LEFT JOIN head_teachers h ON u.id = h.id
                """)
    all_users = cur.fetchall()
    db.close()

    user_map = {}
    user_combo['values'] = []
    for uid, uname, first, last in all_users:
        label = f"{first} {last} ({uname})"
        user_combo['values'] = (*user_combo['values'], label)
        user_map[label] = uid

    tk.Label(user_frame, text="Mesaj:", bg="#f0f6fa").grid(row=1, column=0, padx=6, pady=(8, 0))
    user_msg = tk.Entry(user_frame, width=45)
    user_msg.grid(row=1, column=1, padx=6, pady=(8, 0))

    def send_to_user():
        selection = user_combo.get()
        msg = user_msg.get().strip()
        if not selection or selection not in user_map or not msg:
            messagebox.showerror("Eroare", "Selectează un utilizator și scrie mesajul.")
            return
        user_id = user_map[selection]
        db = connect_db();
        cur = db.cursor()
        cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, msg))
        db.commit();
        db.close()
        messagebox.showinfo("Succes", "Mesajul a fost trimis!")
        user_combo.set("")
        user_msg.delete(0, tk.END)

    tk.Button(user_frame, text="Trimite", command=send_to_user, bg="#344675", fg="white").grid(row=2, columnspan=2,
                                                                                               pady=10)

    # === NOTIFICARE BROADCAST ===
    tk.Label(win, text="Trimite către toți utilizatorii cu un rol", font=("Segoe UI", 12, "bold"), bg="#f0f6fa").pack(
        pady=(22, 6))
    broadcast_frame = tk.Frame(win, bg="#f0f6fa");
    broadcast_frame.pack()
    tk.Label(broadcast_frame, text="Rol:", bg="#f0f6fa").grid(row=0, column=0, padx=6)
    role_combo = ttk.Combobox(broadcast_frame, state="readonly", values=["student", "teacher", "head_teacher", "admin"],
                              width=30)
    role_combo.grid(row=0, column=1, padx=6)
    tk.Label(broadcast_frame, text="Mesaj:", bg="#f0f6fa").grid(row=1, column=0, padx=6, pady=(8, 0))
    broadcast_msg = tk.Entry(broadcast_frame, width=45)
    broadcast_msg.grid(row=1, column=1, padx=6, pady=(8, 0))

    def send_broadcast():
        role = role_combo.get()
        msg = broadcast_msg.get().strip()
        if not role or not msg:
            messagebox.showerror("Eroare", "Selectează rolul și scrie mesajul.")
            return
        db = connect_db();
        cur = db.cursor()
        cur.execute("""
                    SELECT u.id
                    FROM users u
                             JOIN user_roles ur ON u.id = ur.user_id
                    WHERE ur.role = %s
                    """, (role,))
        users = cur.fetchall()
        for (uid,) in users:
            cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (uid, msg))
        db.commit()
        db.close()
        messagebox.showinfo("Succes", f"Mesajul a fost trimis către toți utilizatorii cu rolul {role}.")
        role_combo.set("")
        broadcast_msg.delete(0, tk.END)

    tk.Button(broadcast_frame, text="Trimite Broadcast", command=send_broadcast, bg="#2a6786", fg="white").grid(row=2,
                                                                                                                columnspan=2,
                                                                                                                pady=12)


def add_class_ui():
    win = tk.Toplevel()
    win.title("Adaugă Clasă")
    win.geometry("300x130")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Numele clasei (ex: 9A)", bg="#f0f6fa").pack(pady=10)
    class_entry = tk.Entry(win, font=("Segoe UI", 12))
    class_entry.pack(pady=4)

    def submit():
        cname = class_entry.get().strip().upper()

        if not re.match(r"^(9|10|11|12)[A-Z]$", cname):
            messagebox.showerror(
                "Format invalid",
                "Numele clasei trebuie să fie în formatul: numar de la 9-12 + litera A-Z."
            )
            return

        db = connect_db()
        cur = db.cursor()
        try:

            cur.execute("SELECT id FROM classes WHERE name=%s", (cname,))
            if cur.fetchone():
                messagebox.showwarning(
                    "Clasă existentă",
                    f"Clasa {cname} există deja în baza de date."
                )
                return

            cur.execute("INSERT INTO classes (name) VALUES (%s)", (cname,))
            db.commit()
            messagebox.showinfo("Succes", f"Clasa „{cname}” a fost adăugată.")
            win.destroy()

        except Exception as e:
            db.rollback()
            messagebox.showerror("Eroare", str(e))
        finally:
            cur.close()
            db.close()

    tk.Button(
        win, text="Adaugă", command=submit,
        bg="#264653", fg="white", font=("Segoe UI", 11, "bold")
    ).pack(pady=8)


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
    win.title("Asignare Clase + Materii pentru Profesori")
    win.geometry("620x430")
    win.configure(bg="#f0f6fa")

    tk.Label(win, text="Profesor:", bg="#f0f6fa", font=("Segoe UI", 11)).grid(row=0, column=0, padx=8, pady=(14, 4),
                                                                              sticky="e")
    teacher_combo = ttk.Combobox(win, state="readonly", width=36)
    teacher_combo["values"] = [f"{tid} - {fn} {ln}" for tid, fn, ln in teachers]
    teacher_combo.grid(row=0, column=1, padx=6, pady=(14, 4), columnspan=2, sticky="w")

    tk.Label(win, text="Clase:", bg="#f0f6fa", font=("Segoe UI", 11)).grid(row=1, column=0, padx=8, pady=(12, 2),
                                                                           sticky="ne")
    class_listbox = tk.Listbox(win, selectmode="multiple", width=30, height=10, exportselection=False)
    for cid, cname in classes:
        class_listbox.insert(tk.END, f"{cid} - {cname}")
    class_listbox.grid(row=1, column=1, padx=6, pady=4)

    tk.Label(win, text="Materii:", bg="#f0f6fa", font=("Segoe UI", 11)).grid(row=1, column=2, padx=8, pady=(12, 2),
                                                                             sticky="ne")
    subject_listbox = tk.Listbox(win, selectmode="multiple", width=30, height=10, exportselection=False)
    for sid, sname in subjects:
        subject_listbox.insert(tk.END, f"{sid} - {sname}")
    subject_listbox.grid(row=1, column=3, padx=6, pady=4)

    def assign_all():
        if not teacher_combo.get():
            messagebox.showerror("Eroare", "Selectează un profesor.")
            return

        selected_classes = [class_listbox.get(i) for i in class_listbox.curselection()]
        selected_subjects = [subject_listbox.get(i) for i in subject_listbox.curselection()]
        if not selected_classes or not selected_subjects:
            messagebox.showerror("Eroare", "Selectează cel puțin o clasă și o materie.")
            return

        teacher_id = int(teacher_combo.get().split(" - ")[0])

        db2 = connect_db()
        cur = db2.cursor()
        added = 0
        for class_val in selected_classes:
            class_id = int(class_val.split(" - ")[0])
            for subject_val in selected_subjects:
                subject_id = int(subject_val.split(" - ")[0])
                # Check if this combo already exists
                cur.execute("""
                            SELECT id
                            FROM teacher_assignments
                            WHERE teacher_id = %s
                              AND class_id = %s
                              AND subject_id = %s
                            """, (teacher_id, class_id, subject_id))
                if not cur.fetchone():
                    cur.execute("""
                                INSERT INTO teacher_assignments (teacher_id, class_id, subject_id)
                                VALUES (%s, %s, %s)
                                """, (teacher_id, class_id, subject_id))
                    added += 1

        db2.commit()
        db2.close()
        messagebox.showinfo("Succes", f"Atribuirile au fost salvate.\nTotal adăugate: {added}")
        win.destroy()

    tk.Button(win, text="Asignare Completă", font=("Segoe UI", 11, "bold"),
              bg="#344675", fg="white", command=assign_all).grid(row=2, column=0, columnspan=4, pady=20)


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
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("SELECT DISTINCT subject FROM grades")
        subjects = [row[0] for row in cursor.fetchall()]
        db.close()
        subject_combo["values"] = subjects

    def load_students(event=None):
        subject = subject_combo.get()
        if not subject:
            return
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("""
                       SELECT DISTINCT s.id, s.first_name, s.last_name, c.name
                       FROM grades g
                                JOIN students s ON g.student_id = s.id
                                JOIN classes c ON s.class_id = c.id
                       WHERE g.subject = %s
                       ORDER BY c.name, s.last_name
                       """, (subject,))
        students = cursor.fetchall();
        db.close()
        student_combo["values"] = [f"{sid} - {first} {last} [{cls}]" for sid, first, last, cls in students]
        grade_combo.set("")
        grade_combo["values"] = []

    def load_grades(event=None):
        if not subject_combo.get() or not student_combo.get():
            return
        subject = subject_combo.get()
        student_id = int(student_combo.get().split(" - ")[0])
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("SELECT id, grade, date_given FROM grades WHERE student_id = %s AND subject = %s",
                       (student_id, subject))
        grades = cursor.fetchall();
        db.close()
        grade_combo["values"] = [
            f"{gid} - {grade} ({date.strftime('%d.%m.%Y')})" for gid, grade, date in grades
        ]

    def submit():
        if not grade_combo.get():
            messagebox.showerror("Eroare", "Selectează o notă pentru ștergere.")
            return
        grade_id = int(grade_combo.get().split(" - ")[0])
        db = connect_db();
        cursor = db.cursor()
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
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("SELECT id, name FROM subjects")
        subjects = cursor.fetchall()
        db.close()
        subject_combo["values"] = [f"{sid} - {name}" for sid, name in subjects]

    def load_students(event=None):
        if not subject_combo.get():
            return
        subject_id = int(subject_combo.get().split(" - ")[0])
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("""
                       SELECT DISTINCT s.id, s.first_name, s.last_name, c.name
                       FROM attendance_history ah
                                JOIN students s ON ah.student_id = s.id
                                JOIN classes c ON s.class_id = c.id
                       WHERE ah.subject_id = %s
                       ORDER BY c.name, s.last_name
                       """, (subject_id,))
        students = cursor.fetchall();
        db.close()
        student_combo["values"] = [f"{sid} - {first} {last} [{cls}]" for sid, first, last, cls in students]
        attendance_combo.set("")
        attendance_combo["values"] = []

    def load_attendance(event=None):
        if not subject_combo.get() or not student_combo.get():
            return
        subject_id = int(subject_combo.get().split(" - ")[0])
        student_id = int(student_combo.get().split(" - ")[0])
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("SELECT id, absent_date FROM attendance_history WHERE student_id = %s AND subject_id = %s",
                       (student_id, subject_id))
        recs = cursor.fetchall();
        db.close()
        attendance_combo["values"] = [
            f"{aid} - {date.strftime('%d.%m.%Y')}" for aid, date in recs
        ]

    def submit():
        if not attendance_combo.get():
            messagebox.showerror("Eroare", "Selectează o absență pentru ștergere.")
            return
        aid = int(attendance_combo.get().split(" - ")[0])
        db = connect_db();
        cursor = db.cursor()
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
    student_listbox = tk.Listbox(win, width=45, font=("Segoe UI", 10))
    student_listbox.pack(pady=7)
    result_text = tk.Text(win, width=110, height=25, font=("Consolas", 9), state=tk.DISABLED)
    result_text.pack(padx=7)

    db = connect_db();
    cursor = db.cursor()
    cursor.execute("SELECT name FROM classes ORDER BY name")
    classes = [row[0] for row in cursor.fetchall()]
    db.close()
    class_combo["values"] = classes

    def load_students(event):
        selected_class = class_combo.get()
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("""
                       SELECT s.id, s.first_name, s.last_name
                       FROM students s
                                JOIN classes c ON s.class_id = c.id
                       WHERE c.name = %s
                       ORDER BY s.last_name
                       """, (selected_class,))
        students = cursor.fetchall();
        db.close()
        student_listbox.delete(0, tk.END)
        for sid, first, last in students:
            student_listbox.insert(tk.END, f"{sid} - {first} {last}")

    def show_student_marks(event):
        selection = student_listbox.get(tk.ACTIVE)
        if not selection:
            return
        student_id = int(selection.split(" - ")[0])
        db = connect_db();
        cursor = db.cursor()
        cursor.execute("""
                       SELECT subject, grade, date_given
                       FROM grades
                       WHERE student_id = %s
                       ORDER BY subject, date_given
                       """, (student_id,))
        data = cursor.fetchall();
        db.close()
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


def confirm_and_promote():
    result = messagebox.askyesno(
        "Confirmare Promovare",
        "⚠️ Această acțiune va promova elevii, va șterge elevii din clasa a 12-a și va copia atribuțiile profesorilor pentru clasele următoare.\n\nEști sigur că vrei să continui?"
    )
    if result:
        promote_all_students()


def promote_all_students():
    db = connect_db()
    cursor = db.cursor()
    try:

        cursor.execute("SELECT id, name FROM classes")
        classes = cursor.fetchall()

        missing = set()
        for class_id, name in classes:
            clean = name.strip().replace(" ", "").upper()
            m = re.match(r"^(9|10|11)([A-Z])$", clean)
            if not m:
                continue
            year, letter = int(m.group(1)), m.group(2)
            next_name = f"{year + 1}{letter}"
            cursor.execute("SELECT 1 FROM classes WHERE name=%s", (next_name,))
            if not cursor.fetchone():
                missing.add(next_name)

        if missing:
            miss_list = ", ".join(sorted(missing))
            ans = messagebox.askyesno(
                "Clase lipsă",
                f"Următoarele clase nu există: {miss_list}.\n"
                "Doriți crearea lor înainte de promovare?"
            )
            if not ans:
                return
            for cname in missing:
                cursor.execute("INSERT INTO classes (name) VALUES (%s)", (cname,))
            db.commit()

        for class_id, name in classes:
            clean = name.strip().replace(" ", "").upper()
            m = re.match(r"^(9|10|11)([A-Z])$", clean)
            if not m:
                continue
            year, letter = int(m.group(1)), m.group(2)
            next_name = f"{year + 1}{letter}"
            # obținem ID-ul noii clase (acum sigur există)
            cursor.execute("SELECT id FROM classes WHERE name=%s", (next_name,))
            next_id = cursor.fetchone()[0]

            cursor.execute("SELECT id FROM students WHERE class_id=%s", (class_id,))
            studs = cursor.fetchall()
            for (sid,) in studs:
                cursor.execute("SELECT AVG(grade) FROM grades WHERE student_id=%s", (sid,))
                avg = cursor.fetchone()[0] or 0.0
                if avg >= 5.0:
                    cursor.execute(
                        "UPDATE students SET class_id=%s WHERE id=%s",
                        (next_id, sid)
                    )

                cursor.execute("DELETE FROM grades WHERE student_id=%s", (sid,))
                cursor.execute("DELETE FROM attendance_history WHERE student_id=%s", (sid,))
                cursor.execute("DELETE FROM attendance_current WHERE student_id=%s", (sid,))
                cursor.execute(
                    "INSERT INTO attendance_current (student_id, present) VALUES (%s, 0)",
                    (sid,)
                )

        db.commit()
        messagebox.showinfo("Promovare finalizată", "⇨ Elevii au fost promovați şi catalogul a fost curățat.")

    except Exception as e:
        db.rollback()
        messagebox.showerror("Eroare critică", str(e))
    finally:
        cursor.close()
        db.close()


# --- Fereastră de autentificare ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Autentificare Administrator")
    root.geometry("520x280")
    root.configure(bg="#f0f6fa")
    tk.Label(root, text="Autentificare Administrator", font=("Segoe UI", 16, "bold"), bg="#324e7b", fg="white",
             pady=12).pack(fill=tk.X)
    tk.Label(root, text="Utilizator", font=("Segoe UI", 11), bg="#f0f6fa").pack(pady=8)
    username_entry = tk.Entry(root, font=("Segoe UI", 11))
    username_entry.pack()
    tk.Label(root, text="Parolă", font=("Segoe UI", 11), bg="#f0f6fa").pack(pady=8)
    password_entry = tk.Entry(root, show='*', font=("Segoe UI", 11))
    password_entry.pack()
    tk.Button(root, text="Autentificare", command=login, bg="#264653", fg="white", font=("Segoe UI", 11, "bold"),
              width=17).pack(pady=22)
    root.mainloop()
