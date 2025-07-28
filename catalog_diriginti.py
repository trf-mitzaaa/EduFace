import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime, timedelta
import os
import bcrypt
from admin import hash_password, verify_password
from PIL import Image, ImageTk
import matplotlib.pyplot as plt

def connect_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="yournewpassword",
        database="school"
    )


def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    db = connect_db()
    cursor = db.cursor()

    # First get the user and hashed password
    cursor.execute("""
                   SELECT u.id, u.password, h.class
                   FROM users u
                            JOIN user_roles ur ON u.id = ur.user_id
                            JOIN head_teachers h ON u.id = h.id
                   WHERE u.username = %s
                     AND ur.role = 'head_teacher'
                   """, (username,))

    result = cursor.fetchone()

    if not result or not verify_password(password, result[1]):
        db.close()
        messagebox.showerror("Autentificare eșuată", "Credențiale invalide pentru diriginte.")
        return

    teacher_id, _, class_id = result
    cursor.execute("SELECT name FROM classes WHERE id = %s", (class_id,))
    class_row = cursor.fetchone()
    db.close()

    class_name = class_row[0] if class_row else ""
    messagebox.showinfo("Autentificare reușită", f"Bine ai venit, {username}!")
    root.destroy()
    open_dashboard(teacher_id, class_id, class_name)


def open_dashboard(teacher_id, class_id, class_name):
    dash = tk.Tk()
    dash.title("Panou Diriginte")
    dash.geometry("500x620")
    dash.configure(bg="#f4f6fa")
    tk.Label(dash, text=f"Diriginte - Clasa {class_name}", font=("Segoe UI", 16, "bold"), bg="#344675", fg="white",
             pady=10).pack(fill=tk.X)
    btn_frame = tk.Frame(dash, bg="#f4f6fa")
    btn_frame.pack(pady=20)

    button_style = {
        "font": ("Segoe UI", 11, "bold"),
        "width": 25,
        "bg": "#324e7b",
        "fg": "white",
        "activebackground": "#203557",
        "activeforeground": "white",
        "bd": 0,
        "cursor": "hand2"
    }

    tk.Button(btn_frame, text="Vezi elevii clasei", command=lambda: view_students_ui(class_id, class_name), **button_style).pack(pady=10)
    tk.Button(btn_frame, text="Vezi catalogul clasei", command=lambda: view_marksheet_ui(class_id, class_name), **button_style).pack(pady=10)
    tk.Button(btn_frame, text="Șterge notă", command=lambda: delete_mark_ui(class_id, class_name), **button_style).pack(pady=10)
    tk.Button(btn_frame, text="Șterge absență", command=lambda: delete_absence_ui(class_id, class_name), **button_style).pack(pady=10)
    tk.Button(btn_frame, text="Scanează situația claselor", command=lambda: scan_headteacher_classes(teacher_id), **button_style).pack(pady=10)
    tk.Button(btn_frame, text="Vezi cereri motivări absențe", command=lambda: open_absence_requests_window(teacher_id), **button_style).pack(pady=10)
    tk.Button(btn_frame, text="Statistici promovabilitate", command=lambda: show_pie_promovabilitate(class_id), **button_style).pack(pady=10)



    tk.Button(btn_frame, text="Ieșire", font=("Segoe UI", 11, "bold"), width=25, activebackground="#203557",
              activeforeground="white", bd=0, cursor="hand2", bg="#b0413e", fg="white", command=dash.destroy).pack(
        pady=18)

    tk.Button(dash, text="Deschide Notificări", bg="#2a6786", fg="white",
              font=("Segoe UI", 11, "bold"),
              command=lambda: show_notifications_window(teacher_id)).pack(pady=(4, 10))

    dash.mainloop()


def view_students_ui(class_id, class_name):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
                   SELECT s.first_name, s.last_name, s.photo, u.username, s.id
                   FROM students s
                            LEFT JOIN users u ON s.user_id = u.id
                   WHERE s.class_id = %s
                   ORDER BY s.last_name, s.first_name
                   """, (class_id,))
    students = cursor.fetchall()
    db.close()

    win = tk.Toplevel()
    win.title(f"Elevii din {class_name}")
    win.geometry("560x480")
    win.configure(bg="#f5f7fb")

    tk.Label(win, text=f"Elevii clasei {class_name}",
             font=("Segoe UI", 15, "bold"),
             bg="#324e7b", fg="white",
             pady=8).pack(fill=tk.X, pady=(0, 8))

    # --- Scrollable Treeview Frame ---
    tree_frame = tk.Frame(win, bg="#f5f7fb")
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

    columns = ("nume", "utilizator", "absente", "media")
    tree = ttk.Treeview(
        tree_frame, columns=columns, show="headings"
    )
    for col, title, w in [
        ("nume",       "Nume elev",      180),
        ("utilizator","User",            100),
        ("absente",   "Absente",         70),
        ("media",     "Media generală", 110),
    ]:
        tree.heading(col, text=title)
        tree.column(col, width=w, anchor="center" if col!="nume" else "w")

    # vertical scrollbar
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    # layout with grid so both expand
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)

    # populate rows
    for fname, lname, photo, username, sid in students:
        db = connect_db()
        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM attendance_history WHERE student_id=%s", (sid,))
        abs_count = c.fetchone()[0]
        c.execute("SELECT AVG(grade) FROM grades WHERE student_id=%s", (sid,))
        avg = c.fetchone()[0]
        db.close()

        avg_disp = f"{avg:.2f}" if avg is not None else "-"
        tree.insert(
            "", "end",
            values=(f"{fname} {lname}", username or "-", abs_count, avg_disp)
        )

    # make non-editable
    tree.bind("<Key>", lambda e: "break")


def view_marksheet_ui(class_id, class_name):
    win = tk.Toplevel()
    win.title(f"Catalogul clasei {class_name}")
    win.geometry("960x570")
    win.configure(bg="#f5f7fb")

    tk.Label(win, text=f"Catalogul clasei {class_name}",
             font=("Segoe UI", 14, "bold"),
             bg="#324e7b", fg="white",
             pady=8).pack(fill=tk.X, pady=(0, 8))

    # === Dropdown-uri materie + elev ===
    filter_frame = tk.Frame(win, bg="#f5f7fb")
    filter_frame.pack(pady=(6, 4))

    db = connect_db()
    c = db.cursor()

    # Materii
    c.execute("""
              SELECT DISTINCT subject
              FROM grades g
                       JOIN students s ON g.student_id = s.id
              WHERE s.class_id = %s
              """, (class_id,))
    subjects = [row[0] for row in c.fetchall()]
    subjects.insert(0, "Toate")

    tk.Label(filter_frame, text="Materie:", bg="#f5f7fb", font=("Segoe UI", 10)) \
        .grid(row=0, column=0, padx=6)
    subj_combo = ttk.Combobox(filter_frame, values=subjects,
                              state="readonly", width=18)
    subj_combo.set("Toate")
    subj_combo.grid(row=0, column=1, padx=(0, 12))

    # Elevi
    c.execute("""
              SELECT id, first_name, last_name
              FROM students
              WHERE class_id = %s
              """, (class_id,))
    elevi = [(row[0], f"{row[1]} {row[2]}") for row in c.fetchall()]
    elevi_combo_map = {name: sid for sid, name in elevi}
    elevi_nume = ["Toți elevii"] + [name for _, name in elevi]

    tk.Label(filter_frame, text="Elev:", bg="#f5f7fb", font=("Segoe UI", 10)) \
        .grid(row=0, column=2, padx=6)
    elev_combo = ttk.Combobox(filter_frame, values=elevi_nume,
                              state="readonly", width=22)
    elev_combo.set("Toți elevii")
    elev_combo.grid(row=0, column=3, padx=(0, 6))

    db.close()

    # === Scrollable Treeview ===
    tree_frame = tk.Frame(win, bg="#f5f7fb")
    tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

    columns = ("nume", "subject", "data", "nota")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    for col, txt, w in zip(columns,
                           ["Nume elev", "Materie", "Data", "Nota"],
                           [160, 120, 80, 60]):
        tree.heading(col, text=txt)
        tree.column(col, width=w, anchor="w")

    # vertical scrollbar
    vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                        command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    # layout
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)

    # === Funcție încărcare cu filtru dublu ===
    def load_grades(*args):
        subject = subj_combo.get()
        elev_nume = elev_combo.get()
        elev_id = elevi_combo_map.get(elev_nume)

        query = """
                SELECT s.first_name, s.last_name, g.subject, g.grade, g.date_given
                FROM grades g
                         JOIN students s ON g.student_id = s.id
                WHERE s.class_id = %s \
                """
        params = [class_id]

        if subject != "Toate":
            query += " AND g.subject = %s"
            params.append(subject)
        if elev_id:
            query += " AND s.id = %s"
            params.append(elev_id)

        query += " ORDER BY s.last_name, g.subject, g.date_given"

        db2 = connect_db()
        c2 = db2.cursor()
        c2.execute(query, tuple(params))
        rows = c2.fetchall()
        db2.close()

        tree.delete(*tree.get_children())
        for fname, lname, subj, grade, date in rows:
            tree.insert("", "end", values=(
                f"{fname} {lname}",
                subj,
                date.strftime("%d.%m.%Y"),
                grade
            ))

    # Binds
    subj_combo.bind("<<ComboboxSelected>>", load_grades)
    elev_combo.bind("<<ComboboxSelected>>", load_grades)

    load_grades()

    # make non-editable
    tree.bind("<Key>", lambda e: "break")


def delete_mark_ui(class_id, class_name):
    db = connect_db()
    cursor = db.cursor()
    # First: find all subjects for this class
    cursor.execute("""
                   SELECT DISTINCT subject
                   FROM grades g
                            JOIN students s ON g.student_id = s.id
                   WHERE s.class_id = %s
                   """, (class_id,))
    subjects = [row[0] for row in cursor.fetchall()]

    # Now all students in class
    cursor.execute("""
                   SELECT id, first_name, last_name
                   FROM students
                   WHERE class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    db.close()

    win = tk.Toplevel()
    win.title("Șterge notă")
    win.geometry("580x250")
    win.configure(bg="#f5f7fb")

    tk.Label(win, text="Materie:", font=("Segoe UI", 11), bg="#f5f7fb").pack(pady=(8, 2))
    subj_combo = ttk.Combobox(win, values=subjects, state="readonly", width=24)
    subj_combo.pack()

    tk.Label(win, text="Elev:", font=("Segoe UI", 11), bg="#f5f7fb").pack(pady=(14, 2))
    student_combo = ttk.Combobox(win, state="readonly", width=34)
    student_combo.pack()

    tk.Label(win, text="Notă:", font=("Segoe UI", 11), bg="#f5f7fb").pack(pady=(14, 2))
    grade_combo = ttk.Combobox(win, state="readonly", width=60)
    grade_combo.pack()

    # Filter students for selected subject
    def on_subject_change(event=None):
        sel_subject = subj_combo.get()
        db = connect_db()
        cur = db.cursor()
        cur.execute("""
                    SELECT DISTINCT s.id, s.first_name, s.last_name
                    FROM grades g
                             JOIN students s ON g.student_id = s.id
                    WHERE s.class_id = %s
                      AND g.subject = %s
                    """, (class_id, sel_subject))
        student_rows = cur.fetchall()
        db.close()
        student_combo['values'] = [f"{sid} - {fname} {lname}" for sid, fname, lname in student_rows]
        student_combo.set("")
        grade_combo.set("")
        grade_combo['values'] = []

    def on_student_change(event=None):
        sel_subject = subj_combo.get()
        sel_student = student_combo.get()
        if not sel_subject or not sel_student:
            return
        student_id = int(sel_student.split(" - ")[0])
        db = connect_db()
        cur = db.cursor()
        cur.execute("""
                    SELECT id, grade, date_given
                    FROM grades
                    WHERE student_id = %s
                      AND subject = %s
                    ORDER BY date_given
                    """, (student_id, sel_subject))
        grades = cur.fetchall()
        db.close()
        grade_combo['values'] = [
            f"ID:{gid} | {grade} | {dt.strftime('%d.%m.%Y')}" for gid, grade, dt in grades
        ]
        grade_combo.set("")

    def delete_selected():
        if not grade_combo.get():
            messagebox.showerror("Eroare", "Selectează o notă pentru ștergere.")
            return
        grade_id = int(grade_combo.get().split(":")[1].split("|")[0].strip())
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM grades WHERE id = %s", (grade_id,))
        db.commit()
        db.close()
        messagebox.showinfo("Șters", f"Nota a fost ștearsă.")
        win.destroy()

    subj_combo.bind("<<ComboboxSelected>>", on_subject_change)
    student_combo.bind("<<ComboboxSelected>>", on_student_change)
    tk.Button(win, text="Șterge selecția", command=delete_selected, bg="#b0413e", fg="white",
              font=("Segoe UI", 11, "bold")).pack(pady=14)


def delete_absence_ui(class_id, class_name):
    db = connect_db()
    cursor = db.cursor()
    # List all subjects present in attendance_history for this class
    cursor.execute("""
                   SELECT DISTINCT ah.subject_id, subj.name
                   FROM attendance_history ah
                            JOIN students s ON ah.student_id = s.id
                            JOIN subjects subj ON ah.subject_id = subj.id
                   WHERE s.class_id = %s
                   ORDER BY subj.name
                   """, (class_id,))
    subjects = cursor.fetchall()
    db.close()

    win = tk.Toplevel()
    win.title("Șterge absență")
    win.geometry("540x270")
    win.configure(bg="#f5f7fb")

    tk.Label(win, text="Materie:", font=("Segoe UI", 11), bg="#f5f7fb").pack(pady=(10, 2))
    subject_combo = ttk.Combobox(win, state="readonly", width=32)
    subject_combo['values'] = [f"{sid} - {name}" for sid, name in subjects]
    subject_combo.pack()

    tk.Label(win, text="Elev:", font=("Segoe UI", 11), bg="#f5f7fb").pack(pady=(10, 2))
    student_combo = ttk.Combobox(win, state="readonly", width=32)
    student_combo.pack()

    tk.Label(win, text="Absență:", font=("Segoe UI", 11), bg="#f5f7fb").pack(pady=(10, 2))
    absence_combo = ttk.Combobox(win, state="readonly", width=46)
    absence_combo.pack()

    def on_subject_change(event=None):
        sel_subject = subject_combo.get()
        if not sel_subject:
            return
        subject_id = int(sel_subject.split(" - ")[0])
        db = connect_db()
        cur = db.cursor()
        cur.execute("""
                    SELECT DISTINCT s.id, s.first_name, s.last_name
                    FROM attendance_history ah
                             JOIN students s ON ah.student_id = s.id
                    WHERE s.class_id = %s
                      AND ah.subject_id = %s
                    ORDER BY s.last_name, s.first_name
                    """, (class_id, subject_id))
        students = cur.fetchall()
        db.close()
        student_combo['values'] = [f"{sid} - {fname} {lname}" for sid, fname, lname in students]
        student_combo.set("")
        absence_combo.set("")
        absence_combo['values'] = []

    def on_student_change(event=None):
        sel_subject = subject_combo.get()
        sel_student = student_combo.get()
        if not sel_subject or not sel_student:
            return
        subject_id = int(sel_subject.split(" - ")[0])
        student_id = int(sel_student.split(" - ")[0])
        db = connect_db()
        cur = db.cursor()
        cur.execute("""
                    SELECT id, absent_date
                    FROM attendance_history
                    WHERE student_id = %s
                      AND subject_id = %s
                    ORDER BY absent_date
                    """, (student_id, subject_id))
        absences = cur.fetchall()
        db.close()
        absence_combo['values'] = [
            f"ID:{aid} | {dt.strftime('%d.%m.%Y')}" for aid, dt in absences
        ]
        absence_combo.set("")

    def delete_selected():
        if not absence_combo.get():
            messagebox.showerror("Eroare", "Selectează o absență pentru ștergere.")
            return
        absence_id = int(absence_combo.get().split(":")[1].split("|")[0].strip())
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM attendance_history WHERE id = %s", (absence_id,))
        db.commit()
        db.close()
        messagebox.showinfo("Șters", f"Absența a fost ștearsă.")
        win.destroy()

    subject_combo.bind("<<ComboboxSelected>>", on_subject_change)
    student_combo.bind("<<ComboboxSelected>>", on_student_change)
    tk.Button(win, text="Șterge selecția", command=delete_selected, bg="#b0413e", fg="white",
              font=("Segoe UI", 11, "bold")).pack(pady=16)


def show_notifications_window(teacher_id):
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
              command=lambda: mark_as_seen(teacher_id, notif_tree)).pack(pady=10)

    load_notifications(teacher_id, notif_tree)


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

def scan_headteacher_classes(teacher_id):
    db = connect_db()
    cur = db.cursor()

    # user_id = teacher_id (id-ul din `teachers` este deja user_id)
    user_id = teacher_id

    # Obține clasa (sau clasele) unde este diriginte
    cur.execute("SELECT class FROM head_teachers WHERE id = %s", (user_id,))
    class_rows = cur.fetchall()
    if not class_rows:
        db.close()
        messagebox.showinfo("Info", "Dirigintele nu este asignat la nicio clasă.")
        return

    class_ids = [row[0] for row in class_rows]

    # Obține elevii din clasele respective
    placeholders = ','.join(['%s'] * len(class_ids))
    cur.execute(f"""
        SELECT s.id, s.first_name, s.last_name, s.class_id
        FROM students s
        WHERE s.class_id IN ({placeholders})
    """, tuple(class_ids))
    students = cur.fetchall()

    for sid, fn, ln, cid in students:
        # Verifică mediile per materie
        cur.execute("""
                    SELECT subject, AVG(grade)
                    FROM grades
                    WHERE student_id = %s
                    GROUP BY subject
                    """, (sid,))
        subject_avgs = cur.fetchall()

        for subj, avg in subject_avgs:
            if avg is not None and avg < 4.4:
                msg = f"⚠️ Situație de corigență la elevul {fn} {ln} la materia {subj}"
                cur.execute("""
                            SELECT 1 FROM notifications
                            WHERE user_id=%s AND message=%s AND seen=FALSE
                            """, (user_id, msg))
                if not cur.fetchone():
                    cur.execute("""
                                INSERT INTO notifications (user_id, message)
                                VALUES (%s, %s)
                                """, (user_id, msg))

        # Verifică absențele
        cur.execute("SELECT COUNT(*) FROM attendance_history WHERE student_id = %s", (sid,))
        abs_count = cur.fetchone()[0]

        msg = None
        if abs_count >= 20:
            msg = f"⛔ Elevul {fn} {ln} are peste 20 de absențe — eligibil pentru scădere la purtare"
        elif abs_count >= 10:
            msg = f"⚠️ Elevul {fn} {ln} are peste 10 absențe — risc bursă"

        if msg:
            cur.execute("""
                        SELECT 1 FROM notifications
                        WHERE user_id=%s AND message=%s AND seen=FALSE
                        """, (user_id, msg))
            if not cur.fetchone():
                cur.execute("""
                            INSERT INTO notifications (user_id, message)
                            VALUES (%s, %s)
                            """, (user_id, msg))

    db.commit()
    db.close()
    messagebox.showinfo("Scanare completă", "Situația claselor a fost scanată cu succes.")

def open_absence_requests_window(teacher_id):
    db = connect_db()
    cur = db.cursor()

    # Obține clasele dirigintelui
    cur.execute("SELECT class FROM head_teachers WHERE id = %s", (teacher_id,))
    classes = [row[0] for row in cur.fetchall()]
    if not classes:
        db.close()
        messagebox.showinfo("Info", "Nu există clase asociate.")
        return

    # Obține cererile din acele clase
    cur.execute("""
        SELECT ar.id, s.first_name, s.last_name, ar.description, ar.image_path, ar.created_at
        FROM absence_requests ar
        JOIN students s ON ar.student_id = s.id
        WHERE ar.class_id IN (%s)
        ORDER BY ar.created_at DESC
    """ % ",".join(["%s"] * len(classes)), tuple(classes))
    requests = cur.fetchall()
    db.close()

    win = tk.Toplevel()
    win.title("Cereri motivări absențe")
    win.geometry("750x400")
    win.configure(bg="#f7f8fc")

    tree = ttk.Treeview(win, columns=("elev", "descriere", "data"), show="headings", height=15)
    tree.heading("elev", text="Elev")
    tree.heading("descriere", text="Descriere")
    tree.heading("data", text="Data")
    tree.column("elev", width=180)
    tree.column("descriere", width=380)
    tree.column("data", width=130)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    id_map = {}

    for rid, fn, ln, desc, img_path, created in requests:
        name = f"{fn} {ln}"
        tree.insert("", "end", iid=str(rid), values=(name, desc[:80]+"...", created.strftime("%d.%m.%Y %H:%M")))
        id_map[str(rid)] = (desc, img_path)

    def open_detail():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Selectează", "Selectează o cerere mai întâi.")
            return
        rid = selected[0]
        desc, img_path = id_map[rid]

        view = tk.Toplevel()
        view.title("Cerere motivare")
        view.geometry("500x500")
        view.configure(bg="#f0f6fa")

        tk.Label(view, text="Descriere:", font=("Segoe UI", 11, "bold"), bg="#f0f6fa").pack(pady=(12, 2))
        tk.Message(view, text=desc, width=460, bg="#f0f6fa", font=("Segoe UI", 10)).pack(padx=10)

        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                img.thumbnail((420, 420))
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(view, image=photo, bg="#f0f6fa")
                label.image = photo
                label.pack(pady=10)
            except Exception as e:
                tk.Label(view, text=f"Eroare la afișarea imaginii: {e}", bg="#f0f6fa", fg="red").pack()

    tk.Button(win, text="Vezi detalii", command=open_detail,
              bg="#344675", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=8)


def show_pie_promovabilitate(class_id):
    db = connect_db()
    cur = db.cursor()

    # Găsește toți elevii din clasă
    cur.execute("SELECT id FROM students WHERE class_id = %s", (class_id,))
    student_ids = [row[0] for row in cur.fetchall()]

    promovat = 0
    corigent = 0

    for sid in student_ids:
        cur.execute("""
                    SELECT AVG(grade)
                    FROM grades
                    WHERE student_id = %s
                    """, (sid,))
        avg = cur.fetchone()[0]
        if avg is not None:
            if avg >= 5:
                promovat += 1
            else:
                corigent += 1

    db.close()

    total = promovat + corigent
    if total == 0:
        messagebox.showinfo("Info", "Nu există suficiente note pentru a calcula promovabilitatea.")
        return

    labels = ['Promovați', 'Nepromovați']
    sizes = [promovat, corigent]
    colors = ['#4caf50', '#ef5350']

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops=dict(edgecolor='white')
    )
    ax.axis('equal')  # asigură centrare și formă rotundă
    ax.set_title("Promovabilitate clasa", fontsize=14)

    plt.tight_layout()
    plt.show()

root = tk.Tk()
root.title("Autentificare Diriginte")
root.geometry("370x250")
root.configure(bg="#eaf2fa")
tk.Label(root, text="Autentificare Diriginte", font=("Segoe UI", 14, "bold"), bg="#344675", fg="white", pady=10).pack(
    fill=tk.X)
tk.Label(root, text="Utilizator", font=("Segoe UI", 11), bg="#eaf2fa").pack(pady=(14, 2))
username_entry = tk.Entry(root, font=("Segoe UI", 11))
username_entry.pack()
tk.Label(root, text="Parolă", font=("Segoe UI", 11), bg="#eaf2fa").pack(pady=(8, 2))
password_entry = tk.Entry(root, show='*', font=("Segoe UI", 11))
password_entry.pack()
tk.Button(root, text="Autentificare", font=("Segoe UI", 11, "bold"), bg="#344675", fg="white", command=login).pack(
    pady=18)
root.mainloop()
