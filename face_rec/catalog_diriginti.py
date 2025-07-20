import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime
import os
import bcrypt
from admin import hash_password, verify_password


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
    dash.geometry("320x450")
    dash.configure(bg="#f4f6fa")
    tk.Label(dash, text=f"Diriginte - Clasa {class_name}", font=("Segoe UI", 16, "bold"), bg="#344675", fg="white", pady=10).pack(fill=tk.X)
    btn_frame = tk.Frame(dash, bg="#f4f6fa")
    btn_frame.pack(pady=20)

    tk.Button(btn_frame, text="Vezi elevii clasei", font=("Segoe UI", 11, "bold"), width=25, bg="#324e7b", fg="white", activebackground="#203557", activeforeground="white", bd=0, cursor="hand2", command=lambda: view_students_ui(class_id, class_name)).pack(pady=10)
    tk.Button(btn_frame, text="Vezi catalogul clasei", font=("Segoe UI", 11, "bold"), width=25, bg="#324e7b", fg="white", activebackground="#203557", activeforeground="white", bd=0, cursor="hand2", command=lambda: view_marksheet_ui(class_id, class_name)).pack(pady=10)
    tk.Button(btn_frame, text="Șterge notă", font=("Segoe UI", 11, "bold"), width=25, bg="#324e7b", fg="white", activebackground="#203557", activeforeground="white", bd=0, cursor="hand2", command=lambda: delete_mark_ui(class_id, class_name)).pack(pady=10)
    tk.Button(btn_frame, text="Șterge absență", font=("Segoe UI", 11, "bold"), width=25, bg="#324e7b", fg="white", activebackground="#203557", activeforeground="white", bd=0, cursor="hand2", command=lambda: delete_absence_ui(class_id, class_name)).pack(pady=10)
    tk.Button(btn_frame, text="Ieșire", font=("Segoe UI", 11, "bold"), width=25, activebackground="#203557", activeforeground="white", bd=0, cursor="hand2", bg="#b0413e", fg="white", command=dash.destroy).pack(pady=18)
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
    tk.Label(win, text=f"Elevii clasei {class_name}", font=("Segoe UI", 15, "bold"), bg="#324e7b", fg="white", pady=8).pack(fill=tk.X, pady=(0,8))

    columns = ("nume", "utilizator", "absente", "media")
    tree = ttk.Treeview(win, columns=columns, show="headings", height=20)
    tree.heading("nume", text="Nume elev")
    tree.heading("utilizator", text="User")
    tree.heading("absente", text="Absente")
    tree.heading("media", text="Media generală")
    tree.column("nume", width=180)
    tree.column("utilizator", width=100)
    tree.column("absente", width=70)
    tree.column("media", width=110)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    for fname, lname, photo, username, sid in students:
        db = connect_db()
        c = db.cursor()
        # Count absences
        c.execute("SELECT COUNT(*) FROM attendance_history WHERE student_id=%s", (sid,))
        abs_count = c.fetchone()[0]
        # Average
        c.execute("SELECT AVG(grade) FROM grades WHERE student_id=%s", (sid,))
        avg = c.fetchone()[0]
        db.close()
        avg_disp = f"{avg:.2f}" if avg is not None else "-"
        tree.insert("", "end", values=(f"{fname} {lname}", username or "-", abs_count, avg_disp))
    # Make it non-editable
    tree.bind("<Key>", lambda e: "break")

def view_marksheet_ui(class_id, class_name):
    win = tk.Toplevel()
    win.title(f"Catalogul clasei {class_name}")
    win.geometry("950x540")
    win.configure(bg="#f5f7fb")

    tk.Label(win, text=f"Catalogul clasei {class_name}", font=("Segoe UI", 14, "bold"), bg="#324e7b", fg="white", pady=8).pack(fill=tk.X, pady=(0,8))

    # Subject dropdown
    db = connect_db()
    c = db.cursor()
    c.execute("SELECT DISTINCT subject FROM grades g JOIN students s ON g.student_id = s.id WHERE s.class_id = %s", (class_id,))
    subjects = [row[0] for row in c.fetchall()]
    db.close()
    subj_combo = ttk.Combobox(win, values=["Toate"] + subjects, state="readonly", width=18)
    subj_combo.set("Toate")
    subj_combo.pack(pady=7)

    columns = ("nume", "subject", "data", "nota")
    tree = ttk.Treeview(win, columns=columns, show="headings", height=20)
    tree.heading("nume", text="Nume elev")
    tree.heading("subject", text="Materie")
    tree.heading("data", text="Data")
    tree.heading("nota", text="Nota")
    tree.column("nume", width=160)
    tree.column("subject", width=120)
    tree.column("data", width=80)
    tree.column("nota", width=60)
    tree.pack(fill="both", expand=True, padx=8, pady=8)

    def load_grades(*args):
        subject = subj_combo.get()
        db = connect_db()
        c = db.cursor()
        if subject == "Toate":
            c.execute("""
                SELECT s.first_name, s.last_name, g.subject, g.grade, g.date_given
                FROM grades g JOIN students s ON g.student_id = s.id
                WHERE s.class_id = %s
                ORDER BY s.last_name, g.subject, g.date_given
            """, (class_id,))
        else:
            c.execute("""
                SELECT s.first_name, s.last_name, g.subject, g.grade, g.date_given
                FROM grades g JOIN students s ON g.student_id = s.id
                WHERE s.class_id = %s AND g.subject = %s
                ORDER BY s.last_name, g.subject, g.date_given
            """, (class_id, subject))
        rows = c.fetchall()
        db.close()
        tree.delete(*tree.get_children())
        for fname, lname, subj, grade, date in rows:
            tree.insert("", "end", values=(f"{fname} {lname}", subj, date.strftime("%d.%m.%Y"), grade))
    load_grades()
    subj_combo.bind("<<ComboboxSelected>>", load_grades)
    tree.bind("<Key>", lambda e: "break")

def delete_mark_ui(class_id, class_name):
    db = connect_db()
    cursor = db.cursor()
    # First: find all subjects for this class
    cursor.execute("""
        SELECT DISTINCT subject FROM grades g JOIN students s ON g.student_id = s.id WHERE s.class_id=%s
    """, (class_id,))
    subjects = [row[0] for row in cursor.fetchall()]

    # Now all students in class
    cursor.execute("""
        SELECT id, first_name, last_name FROM students WHERE class_id=%s
    """, (class_id,))
    students = cursor.fetchall()
    db.close()

    win = tk.Toplevel()
    win.title("Șterge notă")
    win.geometry("580x250")
    win.configure(bg="#f5f7fb")

    tk.Label(win, text="Materie:", font=("Segoe UI",11), bg="#f5f7fb").pack(pady=(8,2))
    subj_combo = ttk.Combobox(win, values=subjects, state="readonly", width=24)
    subj_combo.pack()

    tk.Label(win, text="Elev:", font=("Segoe UI",11), bg="#f5f7fb").pack(pady=(14,2))
    student_combo = ttk.Combobox(win, state="readonly", width=34)
    student_combo.pack()

    tk.Label(win, text="Notă:", font=("Segoe UI",11), bg="#f5f7fb").pack(pady=(14,2))
    grade_combo = ttk.Combobox(win, state="readonly", width=60)
    grade_combo.pack()

    # Filter students for selected subject
    def on_subject_change(event=None):
        sel_subject = subj_combo.get()
        db = connect_db()
        cur = db.cursor()
        cur.execute("""
            SELECT DISTINCT s.id, s.first_name, s.last_name
            FROM grades g JOIN students s ON g.student_id = s.id
            WHERE s.class_id=%s AND g.subject=%s
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
            WHERE student_id=%s AND subject=%s
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
    tk.Button(win, text="Șterge selecția", command=delete_selected, bg="#b0413e", fg="white", font=("Segoe UI",11,"bold")).pack(pady=14)

def delete_absence_ui(class_id, class_name):
    db = connect_db()
    cursor = db.cursor()
    # List all subjects present in attendance_history for this class
    cursor.execute("""
        SELECT DISTINCT ah.subject_id, subj.name
        FROM attendance_history ah
        JOIN students s ON ah.student_id = s.id
        JOIN subjects subj ON ah.subject_id = subj.id
        WHERE s.class_id=%s
        ORDER BY subj.name
    """, (class_id,))
    subjects = cursor.fetchall()
    db.close()

    win = tk.Toplevel()
    win.title("Șterge absență")
    win.geometry("540x270")
    win.configure(bg="#f5f7fb")

    tk.Label(win, text="Materie:", font=("Segoe UI",11), bg="#f5f7fb").pack(pady=(10,2))
    subject_combo = ttk.Combobox(win, state="readonly", width=32)
    subject_combo['values'] = [f"{sid} - {name}" for sid, name in subjects]
    subject_combo.pack()

    tk.Label(win, text="Elev:", font=("Segoe UI",11), bg="#f5f7fb").pack(pady=(10,2))
    student_combo = ttk.Combobox(win, state="readonly", width=32)
    student_combo.pack()

    tk.Label(win, text="Absență:", font=("Segoe UI",11), bg="#f5f7fb").pack(pady=(10,2))
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
            WHERE s.class_id = %s AND ah.subject_id = %s
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
            WHERE student_id=%s AND subject_id=%s
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
    tk.Button(win, text="Șterge selecția", command=delete_selected, bg="#b0413e", fg="white", font=("Segoe UI",11,"bold")).pack(pady=16)


root = tk.Tk()
root.title("Autentificare Diriginte")
root.geometry("370x250")
root.configure(bg="#eaf2fa")
tk.Label(root, text="Autentificare Diriginte", font=("Segoe UI", 14, "bold"), bg="#344675", fg="white", pady=10).pack(fill=tk.X)
tk.Label(root, text="Utilizator", font=("Segoe UI",11), bg="#eaf2fa").pack(pady=(14,2))
username_entry = tk.Entry(root, font=("Segoe UI",11))
username_entry.pack()
tk.Label(root, text="Parolă", font=("Segoe UI",11), bg="#eaf2fa").pack(pady=(8,2))
password_entry = tk.Entry(root, show='*', font=("Segoe UI",11))
password_entry.pack()
tk.Button(root, text="Autentificare", font=("Segoe UI",11,"bold"), bg="#344675", fg="white", command=login).pack(pady=18)
root.mainloop()