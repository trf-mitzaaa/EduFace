import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import pymysql
import os
from PIL import Image, ImageTk, ImageOps
import bcrypt
from admin import hash_password, verify_password
from tkcalendar import DateEntry

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "yournewpassword"
DB_NAME = "school"
PHOTO_FOLDER = "student_photos"


def connect_db():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)


def login():
    global current_teacher_id, assignments, teacher_fullname
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    db = connect_db()
    cur = db.cursor()

    # First get the user and hashed password
    cur.execute("""
                SELECT u.id, u.password, t.first_name, t.last_name
                FROM users u
                         JOIN user_roles ur ON u.id = ur.user_id
                         JOIN teachers t ON u.id = t.id
                WHERE u.username = %s
                  AND ur.role = 'teacher'
                """, (username,))
    row = cur.fetchone()

    if not row or not verify_password(password, row[1]):
        messagebox.showerror("Autentificare eșuată", "Credențiale incorecte sau nu sunteți profesor.")
        db.close()
        return

    current_teacher_id, _, first_name, last_name = row
    teacher_fullname = f"{first_name} {last_name}"

    # Get assignments
    cur.execute("""
                SELECT ta.class_id, c.name, ta.subject_id, s.name
                FROM teacher_assignments ta
                         JOIN classes c ON ta.class_id = c.id
                         JOIN subjects s ON ta.subject_id = s.id
                WHERE ta.teacher_id = %s
                ORDER BY c.name, s.name
                """, (current_teacher_id,))
    assignments = cur.fetchall()
    db.close()
    root.destroy()
    open_assignment_select()


def open_assignment_select():
    win = tk.Tk()
    win.title("Alegeți atribuirea")
    win.geometry("440x250")
    win.configure(bg="#f0f2fa")
    tk.Label(win, text=f"Bine ați venit, {teacher_fullname}!", font=("Segoe UI", 14, "bold"), bg="#f0f2fa",
             fg="#283657").pack(pady=(24, 10))
    tk.Label(win, text="Selectați clasa și materia de gestionat:", font=("Segoe UI", 12), bg="#f0f2fa",
             fg="#31415e").pack(pady=6)

    asg_combo = ttk.Combobox(win, state="readonly", width=38)
    asg_combo.pack(pady=18)
    assignment_map = {}

    for cid, cname, sid, sname in assignments:
        label = f"{cname} – {sname}"  # fără ID
        asg_combo['values'] = (*asg_combo['values'], label) if asg_combo['values'] else (label,)
        assignment_map[label] = (cid, cname, sid, sname)

    def proceed():
        val = asg_combo.get()
        if not val:
            messagebox.showerror("Eroare", "Vă rugăm să selectați o clasă și o materie.")
            return
        class_id, class_name, subject_id, subject_name = assignment_map[val]
        win.destroy()
        open_student_grid(class_id, class_name, subject_id, subject_name)

    button_frame = tk.Frame(win, bg="#f0f6fa")
    button_frame.pack(pady=(10, 12))

    btn_style = {
        "bg": "#2a6786",
        "fg": "white",
        "font": ("Segoe UI", 11, "bold"),
        "width": 20,
        "bd": 0,
        "cursor": "hand2"
    }

    tk.Button(button_frame, text="Deschide Grila Elevi", command=proceed, **btn_style).pack(side="left", padx=6)
    tk.Button(button_frame, text="Deschide Notificări", command=lambda: show_notifications_window(current_teacher_id),
              **btn_style).pack(side="right", padx=6)

    win.mainloop()


def open_student_grid(class_id, class_name, subject_id, subject_name):
    grid = tk.Tk()
    grid.title(f"Catalogul lui {teacher_fullname} - {class_name} ({subject_name})")
    grid.configure(bg="#f0f2fa")
    banner = tk.Label(grid, text=f"Elevii din {class_name} ({subject_name})", font=("Segoe UI", 16, "bold"),
                      bg="#31415e", fg="white", pady=12)
    banner.pack(fill=tk.X)
    frame = tk.Frame(grid, bg="#f0f2fa")
    frame.pack(padx=18, pady=20)
    back_btn = tk.Button(grid, text="⏪ Înapoi", font=("Segoe UI", 10, "bold"),
                         bg="#ccc", fg="black", command=lambda: (grid.destroy(), open_assignment_select()))
    back_btn.pack(pady=(0, 8))

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
                   SELECT id, first_name, last_name, photo
                   FROM students
                   WHERE class_id = %s
                   ORDER BY last_name, first_name
                   """, (class_id,))
    studs = cursor.fetchall()
    db.close()

    images = []
    cols = 4
    for i, (sid, fname, lname, photo) in enumerate(studs):
        holder = tk.Frame(frame, bg="#f0f2fa", highlightbackground="#cccccc", highlightthickness=1)
        holder.grid(row=i // cols, column=i % cols, padx=12, pady=14, ipadx=4, ipady=4)
        full_name = f"{fname} {lname}"
        img_path = os.path.join(PHOTO_FOLDER, photo) if photo else None
        if img_path and os.path.exists(img_path):
            img = Image.open(img_path).resize((90, 90))
        else:
            img = Image.new('RGB', (90, 90), color='#dbe5fa')
        db2 = connect_db()
        c = db2.cursor()
        c.execute("SELECT present FROM attendance_current WHERE student_id=%s", (sid,))
        rec = c.fetchone()
        present = rec[0] if rec else 0
        db2.close()
        if not present:
            img = ImageOps.grayscale(img)
        tkimg = ImageTk.PhotoImage(img)
        images.append(tkimg)
        btn = tk.Button(holder, image=tkimg, bg="white", borderwidth=0,
                        command=lambda sid=sid, nm=full_name, subid=subject_id,
                                       subname=subject_name: open_student_detail(sid, nm, subid, subname))
        btn.pack()
        lab = tk.Label(holder, text=full_name, font=("Segoe UI", 10, "bold"), bg="#f0f2fa", wraplength=90)
        lab.pack(pady=(3, 0))
        att_lab = tk.Label(holder, text="✔ Prezent" if present else "✖ Absent",
                           font=("Segoe UI", 9), fg="#17ad5c" if present else "#c74242", bg="#f0f2fa")
        att_lab.pack()
    tk.Button(grid, text="Scanează situația clasei", bg="#2a6786", fg="white",
                font=("Segoe UI", 10, "bold"),
                command=lambda: scan_class_for_fails(class_id, subject_name, current_teacher_id)).pack(pady=(4, 10))
    grid.mainloop()


def open_student_detail(student_id, student_name, subject_id, subject_name):
    win = tk.Toplevel()
    win.title(student_name)
    win.geometry("430x500")
    win.configure(bg="#f7f8fc")
    head = tk.Label(win, text=student_name, font=("Segoe UI", 14, "bold"), bg="#344675", fg="white", pady=10)
    head.pack(fill=tk.X)

    # --- Notele pentru materia selectată ---
    grades_frame = tk.LabelFrame(win, text=f"Note ({subject_name})", font=("Segoe UI", 11, "bold"), bg="#f7f8fc",
                                 fg="#283657", bd=2)
    grades_frame.pack(padx=14, pady=10, fill=tk.X)
    db = connect_db()
    cur = db.cursor()
    cur.execute("""
                SELECT grade, date_given
                FROM grades
                WHERE student_id = %s
                  AND subject = %s
                ORDER BY date_given
                """, (student_id, subject_name))
    rows = cur.fetchall()
    if not rows:
        tk.Label(grades_frame, text="Nicio notă momentan.", font=("Segoe UI", 10), bg="#f7f8fc", fg="#a7a7ad").pack()
    else:
        grades = [g for g, _ in rows if g is not None]
        avg = sum(grades) / len(grades) if grades else 0
        tk.Label(grades_frame, text=f"Media: {avg:.2f}", font=("Segoe UI", 10, "bold"),
                 bg="#f7f8fc", fg="#222233").pack(anchor="w", padx=8)
        for grade, dt in rows:
            if grade is not None and dt is not None:
                tk.Label(grades_frame, text=f"{dt.strftime('%d.%m.%Y')} — {grade}",
                         font=("Segoe UI", 10), bg="#f7f8fc", fg="#31415e").pack(anchor="w", padx=18)
    db.close()

    # --- Lista absențelor ---
    abs_frame = tk.LabelFrame(win, text="Absențe", font=("Segoe UI", 11, "bold"), bg="#f7f8fc", fg="#283657", bd=2)
    abs_frame.pack(padx=14, pady=6, fill=tk.X)
    db = connect_db()
    cur = db.cursor()
    cur.execute("""
                SELECT absent_date
                FROM attendance_history
                WHERE student_id = %s
                ORDER BY absent_date DESC
                """, (student_id,))
    absences = cur.fetchall()
    db.close()
    if not absences:
        tk.Label(abs_frame, text="Nicio absență.", font=("Segoe UI", 10), bg="#f7f8fc", fg="#17ad5c").pack(anchor="w",
                                                                                                           padx=8)
    else:
        for (date,) in absences:
            tk.Label(abs_frame, text=f"Absent: {date.strftime('%d.%m.%Y')}",
                     font=("Segoe UI", 10), bg="#f7f8fc", fg="#c74242").pack(anchor="w", padx=18)

    # --- Marcare absență doar dacă prezent=0 în attendance_current ---
    db = connect_db()
    cur = db.cursor()
    cur.execute("SELECT present FROM attendance_current WHERE student_id=%s", (student_id,))
    rec = cur.fetchone()
    db.close()

    def mark_absent():
        today = datetime.today().date()
        db2 = connect_db()
        c2 = db2.cursor()
        # Adaugă absență doar dacă nu există deja azi pentru ACEASTĂ MATERIE
        c2.execute("""
                   SELECT id
                   FROM attendance_history
                   WHERE student_id = %s
                     AND subject_id = %s
                     AND absent_date = %s
                   """, (student_id, subject_id, today))
        if not c2.fetchone():
            c2.execute("""
                       INSERT INTO attendance_history (student_id, subject_id, absent_date)
                       VALUES (%s, %s, %s)
                       """, (student_id, subject_id, today))
            db2.commit()
            messagebox.showinfo("Succes", "Absența pentru această materie și zi a fost înregistrată.")
        else:
            messagebox.showinfo("Informație", "Absența pentru această materie și zi este deja înregistrată.")
        db2.close()
        win.destroy()

    toggle_frame = tk.Frame(win, bg="#f7f8fc")
    toggle_frame.pack(pady=4)
    if rec and rec[0] == 0:
        tk.Button(toggle_frame, text="Marchează absent", bg="#c74242", fg="white",
                  font=("Segoe UI", 10, "bold"), command=mark_absent).pack(pady=3)

    # --- Secțiunea de adăugat notă ---
    add_frame = tk.LabelFrame(win, text="Adaugă notă", font=("Segoe UI", 11, "bold"),
                              bg="#f7f8fc", fg="#283657", bd=2)
    add_frame.pack(padx=14, pady=10, fill=tk.X)

    tk.Label(add_frame, text=f"Materia: {subject_name}", font=("Segoe UI", 10, "bold"),
             bg="#f7f8fc").pack(anchor="w", padx=6, pady=(4, 2))

    tk.Label(add_frame, text="Notă (1–10):", font=("Segoe UI", 10), bg="#f7f8fc").pack(anchor="w", padx=8)
    mark_ent = tk.Entry(add_frame, font=("Segoe UI", 10), width=10)
    mark_ent.pack(pady=(0, 6), padx=8, anchor="w")

    tk.Label(add_frame, text="Data:", font=("Segoe UI", 10), bg="#f7f8fc").pack(anchor="w", padx=8)
    date_ent = DateEntry(add_frame, font=("Segoe UI", 10), date_pattern="dd.MM.yyyy",
                         background="darkblue", foreground="white", borderwidth=2)
    date_ent.pack(pady=(0, 6), padx=8, anchor="w")

    def add_grade():
        try:
            grade = int(mark_ent.get())
            if not (1 <= grade <= 10):
                raise ValueError
        except:
            return messagebox.showerror("Eroare", "Introduceți o notă întreagă între 1 și 10.")

        d = date_ent.get_date()  # direct .get_date() din DateEntry

        db3 = connect_db()
        c3 = db3.cursor()
        c3.execute("INSERT INTO grades(student_id, subject, grade, date_given) VALUES(%s,%s,%s,%s)",
                   (student_id, subject_name, grade, d))
        db3.commit()
        db3.close()
        messagebox.showinfo("Succes", "Nota a fost adăugată.")
        win.destroy()

    tk.Button(add_frame, text="Adaugă", bg="#344675", fg="white",
              font=("Segoe UI", 10, "bold"), command=add_grade).pack(pady=7)


def show_notifications_window(current_teacher_id):
    win = tk.Toplevel()
    win.title("Notificări")
    win.geometry("620x430")
    win.configure(bg="#f0f6fa")

    tk.Label(win, text="Notificări", font=("Segoe UI", 14, "bold"),
             bg="#344675", fg="white", pady=10).pack(fill=tk.X)

    notif_tree = ttk.Treeview(win, columns=("date", "msg"), show="headings", height=15)
    notif_tree.heading("date", text="Data")
    notif_tree.heading("msg", text="Mesaj")
    notif_tree.column("date", width=130)
    notif_tree.column("msg", width=440)
    notif_tree.pack(fill="both", expand=True, padx=10, pady=10)

    notif_tree.bind("<Double-1>", lambda e: show_full_message(e, notif_tree))

    tk.Button(win, text="Am înțeles", bg="#4caf50", fg="white",
              font=("Segoe UI", 10, "bold"),
              command=lambda: mark_as_seen(current_teacher_id, notif_tree)).pack(pady=10)

    load_notifications(current_teacher_id, notif_tree)


def load_notifications(user_id, tree):
    db = connect_db()
    cur = db.cursor()
    cur.execute("""
                DELETE
                FROM notifications
                WHERE user_id = %s
                  AND seen = TRUE
                  AND created_at < (NOW() - INTERVAL 2 DAY)
                """, (user_id,))
    db.commit()

    cur.execute("""
                SELECT id, message, created_at, seen
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                """, (user_id,))
    rows = cur.fetchall()
    db.close()

    tree.delete(*tree.get_children())
    for notif_id, msg, created, seen in rows:
        label = "[✔]" if seen else ""
        tree.insert("", "end", iid=notif_id, values=(created.strftime("%d.%m.%Y %H:%M"), f"{msg} {label}"))


def mark_as_seen(user_id, tree):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selectează", "Selectează o notificare mai întâi.")
        return
    notif_id = selected[0]
    db = connect_db();
    cur = db.cursor()
    cur.execute("UPDATE notifications SET seen = TRUE WHERE id = %s", (notif_id,))
    db.commit();
    db.close()
    messagebox.showinfo("Confirmat", "Notificarea a fost marcată ca citită.")
    load_notifications(user_id, tree)


def show_full_message(event, tree):
    selected = tree.selection()
    if not selected:
        return
    notif_id = selected[0]
    msg = tree.item(notif_id, "values")[1]

    win = tk.Toplevel()
    win.title("Mesaj complet")
    win.geometry("500x200")
    win.configure(bg="#f0f6fa")
    tk.Label(win, text="Conținut notificare", font=("Segoe UI", 12, "bold"),
             bg="#344675", fg="white", pady=8).pack(fill=tk.X)
    tk.Message(win, text=msg, width=480, bg="#f0f6fa", font=("Segoe UI", 10)).pack(padx=10, pady=10)

def scan_class_for_fails(class_id, subject_name, teacher_id):
    db = connect_db()
    cur = db.cursor()

    # Obține user_id-ul profesorului

    user_id = teacher_id

    # Găsește toți elevii din clasă
    cur.execute("SELECT id, first_name, last_name FROM students WHERE class_id = %s", (class_id,))
    students = cur.fetchall()

    for sid, fn, ln in students:
        cur.execute("""
                    SELECT AVG(grade) FROM grades
                    WHERE student_id = %s AND subject = %s
                    """, (sid, subject_name))
        avg = cur.fetchone()[0]
        if avg is not None and avg < 4.4:
            msg = f"⚠️ Elevul {fn} {ln} are media {avg:.2f} la {subject_name} — risc de corigență."
            cur.execute("""
                        SELECT 1 FROM notifications
                        WHERE user_id=%s AND message=%s AND seen=FALSE
                        """, (user_id, msg))
            if not cur.fetchone():
                cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, msg))

    db.commit()
    db.close()
    messagebox.showinfo("Scanare completă", "Situația clasei a fost scanată cu succes.")

# ---- EXECUTARE PRINCIPALĂ ----
root = tk.Tk()
root.title("Autentificare Profesor")
root.geometry("340x250")
root.configure(bg="#f0f2fa")
tk.Label(root, text="Autentificare Profesor", font=("Segoe UI", 16, "bold"), bg="#31415e", fg="white", pady=10).pack(
    fill=tk.X)
tk.Label(root, text="Utilizator", bg="#f0f2fa", font=("Segoe UI", 11)).pack(pady=(15, 3))
username_entry = tk.Entry(root, font=("Segoe UI", 11));
username_entry.pack()
tk.Label(root, text="Parolă", bg="#f0f2fa", font=("Segoe UI", 11)).pack(pady=3)
password_entry = tk.Entry(root, show='*', font=("Segoe UI", 11));
password_entry.pack()
tk.Button(root, text="Autentificare", font=("Segoe UI", 11, "bold"), bg="#344675", fg="white", command=login).pack(
    pady=18)
root.mainloop()
