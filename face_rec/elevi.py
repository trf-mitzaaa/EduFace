import tkinter as tk
from tkinter import ttk, messagebox
import pymysql

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "yournewpassword"
DB_NAME = "school"

def connect_db():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)

def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    db = connect_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s AND password=%s AND role='student'", (username, password))
    user_row = cur.fetchone()
    if not user_row:
        messagebox.showerror("Autentificare eșuată", "Credențiale invalide sau nu sunteți elev.")
        db.close()
        return
    user_id = user_row[0]
    cur.execute("SELECT id, first_name, last_name FROM students WHERE user_id=%s", (user_id,))
    student_row = cur.fetchone()
    db.close()
    if not student_row:
        messagebox.showerror("Autentificare eșuată", "Acest cont nu este legat de niciun elev.")
        return
    student_id, first, last = student_row
    root.destroy()
    open_dashboard(student_id, f"{first} {last}")

def open_dashboard(student_id, student_name):
    dash = tk.Tk()
    dash.title("Panou Elev")
    dash.geometry("650x480")
    dash.configure(bg="#f6f8fa")
    tk.Label(dash, text=f"Bine ai venit, {student_name}", font=("Segoe UI", 16, "bold"), bg="#344675", fg="white", pady=10).pack(fill=tk.X)
    tab_control = ttk.Notebook(dash)
    marks_tab = tk.Frame(tab_control, bg="#f6f8fa")
    att_tab = tk.Frame(tab_control, bg="#f6f8fa")
    tab_control.add(marks_tab, text="Note")
    tab_control.add(att_tab, text="Absențe")
    tab_control.pack(expand=1, fill="both", padx=10, pady=10)

    # TAB NOTE
    marks_tree = ttk.Treeview(marks_tab, columns=("subject", "date", "grade"), show="headings")
    marks_tree.heading("subject", text="Materie")
    marks_tree.heading("date", text="Dată")
    marks_tree.heading("grade", text="Notă")
    marks_tree.column("subject", width=150)
    marks_tree.column("date", width=110)
    marks_tree.column("grade", width=70)
    marks_tree.pack(fill="both", expand=True, pady=10, padx=10)
    avg_text = tk.Text(marks_tab, height=4, width=50, font=("Segoe UI",10), bg="#eaf2fa")
    avg_text.pack(pady=3)
    load_marks(student_id, marks_tree, avg_text)

    # TAB ABSENȚE
    att_tree = ttk.Treeview(att_tab, columns=("date", "subject"), show="headings")
    att_tree.heading("date", text="Data absenței")
    att_tree.heading("subject", text="Materie")
    att_tree.column("date", width=120)
    att_tree.column("subject", width=160)
    att_tree.pack(fill="both", expand=True, pady=10, padx=10)
    load_attendance(student_id, att_tree)


    dash.mainloop()

def load_marks(student_id, tree, avg_box):
    db = connect_db()
    cur = db.cursor()
    cur.execute("""
        SELECT subject, grade, date_given
        FROM grades
        WHERE student_id=%s
        ORDER BY subject, date_given
    """, (student_id,))
    rows = cur.fetchall()
    db.close()
    tree.delete(*tree.get_children())
    subjects = {}
    for subj, grade, date in rows:
        tree.insert("", "end", values=(subj, date.strftime("%d.%m.%Y"), grade))
        subjects.setdefault(subj, []).append(grade)
    avg_box.config(state=tk.NORMAL)
    avg_box.delete("1.0", tk.END)
    if not rows:
        avg_box.insert(tk.END, "Nicio notă momentan.")
    else:
        for subj, grades in subjects.items():
            avg = sum(grades) / len(grades)
            avg_box.insert(tk.END, f"Media la {subj}: {avg:.2f}\n")
    avg_box.config(state=tk.DISABLED)

def load_attendance(student_id, tree):
    db = connect_db()
    cur = db.cursor()
    cur.execute("""
        SELECT ah.absent_date, subj.name
        FROM attendance_history ah
        JOIN subjects subj ON ah.subject_id = subj.id
        WHERE ah.student_id=%s
        ORDER BY ah.absent_date
    """, (student_id,))
    absences = cur.fetchall()
    db.close()
    tree.delete(*tree.get_children())
    for date, subject_name in absences:
        tree.insert("", "end", values=(date.strftime("%d.%m.%Y"), subject_name))

root = tk.Tk()
root.title("Autentificare Elev")
root.geometry("340x250")
root.configure(bg="#eaf2fa")
tk.Label(root, text="Autentificare Elev", font=("Segoe UI", 14, "bold"), bg="#344675", fg="white", pady=10).pack(fill=tk.X)
tk.Label(root, text="Utilizator", font=("Segoe UI",11), bg="#eaf2fa").pack(pady=(14,2))
username_entry = tk.Entry(root, font=("Segoe UI",11))
username_entry.pack()
tk.Label(root, text="Parolă", font=("Segoe UI",11), bg="#eaf2fa").pack(pady=(8,2))
password_entry = tk.Entry(root, show='*', font=("Segoe UI",11))
password_entry.pack()
tk.Button(root, text="Autentificare", font=("Segoe UI",11,"bold"), bg="#344675", fg="white", command=login).pack(pady=18)
root.mainloop()
