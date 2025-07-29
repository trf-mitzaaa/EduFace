import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import bcrypt
from admin import hash_password, verify_password
from datetime import datetime, timedelta
from tkinter import filedialog
import os

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

    # First get the hashed password from database
    cur.execute("""
                SELECT u.id, u.password
                FROM users u
                         JOIN user_roles ur ON u.id = ur.user_id
                WHERE u.username = %s
                  AND ur.role = 'student'
                """, (username,))
    user_row = cur.fetchone()

    if not user_row or not verify_password(password, user_row[1]):
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
    dash.geometry("950x700")
    dash.configure(bg="#f6f8fa")

    # Welcome + Tabs
    tk.Label(dash, text=f"Bine ai venit, {student_name}", font=("Segoe UI", 16, "bold"),
             bg="#344675", fg="white", pady=10).pack(fill=tk.X)
    tab_control = ttk.Notebook(dash)
    marks_tab = tk.Frame(tab_control, bg="#f6f8fa")
    att_tab = tk.Frame(tab_control, bg="#f6f8fa")
    tab_control.add(marks_tab, text="Note")
    tab_control.add(att_tab, text="Absențe")
    tab_control.pack(expand=1, fill="both", padx=10, pady=10)

    # Action Buttons
    tk.Button(dash, text="Deschide Notificări", bg="#2a6786", fg="white",
              font=("Segoe UI", 11, "bold"),
              command=lambda: show_notifications_window(student_id)).pack(pady=(4, 10))
    tk.Button(dash, text="Solicită motivare absență", bg="#e68a00", fg="white",
              font=("Segoe UI", 11, "bold"),
              command=lambda: open_absence_request_form(student_id)).pack(pady=(4, 10))
    tk.Button(dash, text="Scanează statutul meu", bg="#2a6786", fg="white",
              font=("Segoe UI", 11, "bold"),
              command=lambda: scan_student_status(student_id)).pack(pady=(4, 10))

    # Materie filter
    db = connect_db(); cur = db.cursor()
    cur.execute("SELECT DISTINCT subject FROM grades WHERE student_id = %s", (student_id,))
    materii = [row[0] for row in cur.fetchall()]
    db.close()
    materii.insert(0, "Toate materiile")

    filter_frame = tk.Frame(marks_tab, bg="#f6f8fa")
    filter_frame.pack(pady=(10, 2), fill="x", padx=10)
    tk.Label(filter_frame, text="Filtrează după materie:", bg="#f6f8fa",
             font=("Segoe UI", 10)).pack(side="left", padx=(0, 4))
    materie_combo = ttk.Combobox(filter_frame, state="readonly", values=materii)
    materie_combo.current(0)
    materie_combo.pack(side="left")

    # Treeview
    tree_frame = tk.Frame(marks_tab, bg="#f6f8fa")
    tree_frame.pack(fill="both", expand=True, pady=10, padx=10)

    marks_tree = ttk.Treeview(tree_frame, columns=("subject", "date", "grade"), show="headings")
    for col, txt, w in [("subject", "Materie", 150), ("date", "Dată", 110), ("grade", "Notă", 70)]:
        marks_tree.heading(col, text=txt)
        marks_tree.column(col, width=w, anchor="center" if col != "subject" else "w")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=marks_tree.yview)
    marks_tree.configure(yscrollcommand=vsb.set)
    marks_tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)

    # TWO AVG BOXES: left = purtare + generală, right = detalii pe materii
    avg_frame = tk.Frame(marks_tab, bg="#f6f8fa")
    avg_frame.pack(pady=(0, 10))
    left_avg_text = tk.Text(avg_frame, height=4, width=35, font=("Segoe UI", 10), bg="#eaf2fa")
    left_avg_text.pack(side="left", padx=(4, 10))
    right_avg_text = tk.Text(avg_frame, height=8, width=45, font=("Segoe UI", 10), bg="#eaf2fa")
    right_avg_text.pack(side="left", padx=(10, 4))

    # Combo filter
    materie_combo.bind(
        "<<ComboboxSelected>>",
        lambda e: load_marks_filtered(student_id, marks_tree, left_avg_text, right_avg_text, materie_combo.get())
    )

    # Initial load
    load_marks(student_id, marks_tree, left_avg_text, right_avg_text)

    # Attendance TAB
    att_tree = ttk.Treeview(att_tab, columns=("date", "subject"), show="headings")
    att_tree.heading("date", text="Data absenței")
    att_tree.heading("subject", text="Materie")
    att_tree.column("date", width=120)
    att_tree.column("subject", width=160)
    att_tree.pack(fill="both", expand=True, pady=10, padx=10)
    load_attendance(student_id, att_tree)

    dash.mainloop()


def load_marks(student_id, tree, left_box, right_box):
    db = connect_db()
    cur = db.cursor()

    # 1. Obține toate notele
    cur.execute("""
        SELECT subject, grade, date_given
        FROM grades
        WHERE student_id = %s
        ORDER BY subject, date_given
    """, (student_id,))
    rows = cur.fetchall()

    # 2. Media la purtare
    cur.execute("SELECT grade FROM conduct_grades WHERE student_id = %s", (student_id,))
    res = cur.fetchone()
    conduct_grades = res[0] if res and res[0] is not None else 10.0
    db.close()

    # 3. Populate treeview
    tree.delete(*tree.get_children())
    subjects = {}
    all_grades = []

    for subj, grade, date in rows:
        tree.insert("", "end", values=(subj, date.strftime("%d.%m.%Y"), grade))
        subjects.setdefault(subj, []).append(grade)
        all_grades.append(grade)

    # === LEFT BOX ===
    left_box.config(state=tk.NORMAL)
    left_box.delete("1.0", tk.END)
    left_box.insert(tk.END, f"Media la purtare: {conduct_grades:.2f}\n")
    if all_grades:
        general_avg = sum(all_grades) / len(all_grades)
        left_box.insert(tk.END, f"Media generală: {general_avg:.2f}")
    else:
        left_box.insert(tk.END, "Media generală: -")
    left_box.config(state=tk.DISABLED)

    # === RIGHT BOX ===
    right_box.config(state=tk.NORMAL)
    right_box.delete("1.0", tk.END)
    if not rows:
        right_box.insert(tk.END, "Nicio notă momentan.")
    else:
        for subj, grades in subjects.items():
            avg = sum(grades) / len(grades)
            right_box.insert(tk.END, f"Media la {subj}: {avg:.2f}\n")
    right_box.config(state=tk.DISABLED)


def load_attendance(student_id, tree):
    db = connect_db()
    cur = db.cursor()
    cur.execute("""
                SELECT ah.absent_date, subj.name
                FROM attendance_history ah
                         JOIN subjects subj ON ah.subject_id = subj.id
                WHERE ah.student_id = %s
                ORDER BY ah.absent_date
                """, (student_id,))
    absences = cur.fetchall()
    db.close()
    tree.delete(*tree.get_children())
    for date, subject_name in absences:
        tree.insert("", "end", values=(date.strftime("%d.%m.%Y"), subject_name))


def show_notifications_window(student_id):
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
              command=lambda: mark_as_seen(student_id, notif_tree)).pack(pady=10)

    load_notifications(student_id, notif_tree)


def load_notifications(student_id, tree):
    from datetime import datetime
    db = connect_db()
    cur = db.cursor()

    # Șterge notificări vechi confirmate (peste 2 zile)
    cur.execute("""
                DELETE
                FROM notifications
                WHERE user_id = (SELECT user_id
                                 FROM students
                                 WHERE id = %s)
                  AND seen = TRUE
                  AND created_at < (NOW() - INTERVAL 2 DAY)
                """, (student_id,))
    db.commit()

    # Încarcă notificări active
    cur.execute("""
                SELECT n.id, n.message, n.created_at, n.seen
                FROM notifications n
                         JOIN students s ON n.user_id = s.user_id
                WHERE s.id = %s
                ORDER BY n.created_at DESC
                """, (student_id,))
    rows = cur.fetchall()
    db.close()

    tree.delete(*tree.get_children())
    for notif_id, msg, created, seen in rows:
        label = f"[✔]" if seen else ""
        tree.insert("", "end", iid=notif_id, values=(created.strftime("%d.%m.%Y %H:%M"), f"{msg} {label}"))


def mark_as_seen(student_id, tree):
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
    load_notifications(student_id, tree)


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

def scan_student_status(student_id):
    db = connect_db()
    cur = db.cursor()

    # Obține user_id-ul asociat
    cur.execute("SELECT user_id FROM students WHERE id = %s", (student_id,))
    user_row = cur.fetchone()
    if not user_row:
        db.close()
        return
    user_id = user_row[0]

    # Verifică mediile pe materii
    cur.execute("""
                SELECT subject, AVG(grade) as avg
                FROM grades
                WHERE student_id = %s
                GROUP BY subject
                """, (student_id,))
    subject_avgs = cur.fetchall()

    for subject, avg in subject_avgs:
        if avg < 4.4:
            message = f"⚠️ Ai media sub 4.40 la {subject} — risc de corigență."
            # Nu adăuga dacă deja există același mesaj necitit
            cur.execute("""
                        SELECT 1 FROM notifications WHERE user_id=%s AND message=%s AND seen=FALSE
                        """, (user_id, message))
            if not cur.fetchone():
                cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, message))

    # Verifică absențele
    cur.execute("""
                SELECT COUNT(*) FROM attendance_history WHERE student_id = %s
                """, (student_id,))
    total_abs = cur.fetchone()[0]

    if total_abs >= 20:
        msg = "⛔ Ai peste 20 de absențe — riști scăderea notei la purtare."
    elif total_abs >= 10:
        msg = "⚠️ Ai acumulat peste 10 absențe — riști pierderea bursei."
    else:
        msg = None

    if msg:
        cur.execute("""
                    SELECT 1 FROM notifications WHERE user_id=%s AND message=%s AND seen=FALSE
                    """, (user_id, msg))
        if not cur.fetchone():
            cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, msg))

    db.commit()
    db.close()
    messagebox.showinfo("Scanare finalizată", "Verificarea statutului a fost finalizată.")

def open_absence_request_form(student_id):
    db = connect_db()
    cur = db.cursor()

    # Găsim clasa elevului
    cur.execute("SELECT class_id FROM students WHERE id = %s", (student_id,))
    row = cur.fetchone()
    if not row:
        db.close()
        messagebox.showerror("Eroare", "Nu s-a putut găsi clasa elevului.")
        return
    class_id = row[0]
    db.close()

    win = tk.Toplevel()
    win.title("Solicită motivare absență")
    win.geometry("500x350")
    win.configure(bg="#f0f6fa")

    tk.Label(win, text="Descriere motivare:", font=("Segoe UI", 10), bg="#f0f6fa").pack(pady=(14, 4))
    desc_entry = tk.Text(win, height=5, width=55)
    desc_entry.pack(padx=10)

    img_path = tk.StringVar()

    def choose_image():
        file = filedialog.askopenfilename(filetypes=[("Imagini", "*.jpg *.jpeg *.png")])
        if file:
            img_path.set(file)
            tk.Label(win, text=os.path.basename(file), bg="#f0f6fa", fg="#344675").pack()

    tk.Button(win, text="Încarcă poză", command=choose_image, bg="#5c6bc0", fg="white").pack(pady=6)

    def submit_request():
        desc = desc_entry.get("1.0", tk.END).strip()
        if not desc:
            messagebox.showerror("Eroare", "Introduceți o descriere.")
            return

        filename = None
        if img_path.get():
            folder = "absente"
            os.makedirs(folder, exist_ok=True)
            ext = os.path.splitext(img_path.get())[1]
            filename = f"{student_id}_{int(datetime.now().timestamp())}{ext}"
            dest_path = os.path.join(folder, filename)
            with open(img_path.get(), "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())

        db = connect_db()
        cur = db.cursor()
        cur.execute("""
                    INSERT INTO absence_requests (student_id, class_id, description, image_path)
                    VALUES (%s, %s, %s, %s)
                    """, (student_id, class_id, desc, dest_path if filename else None))

        # Găsim user_id-ul dirigintelui clasei
        cur.execute("""
                    SELECT id FROM head_teachers WHERE class = %s
                    """, (class_id,))
        dir_row = cur.fetchone()
        if dir_row:
            notif_msg = f"Elevul #{student_id} a trimis o cerere de motivare a absenței."
            cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (dir_row[0], notif_msg))

        db.commit()
        db.close()
        messagebox.showinfo("Succes", "Cererea a fost trimisă.")
        win.destroy()

    tk.Button(win, text="Trimite cererea", command=submit_request, bg="#344675", fg="white",
              font=("Segoe UI", 10, "bold")).pack(pady=14)

def load_marks_filtered(student_id, tree, left_box, right_box, filter_subject=None):
    db = connect_db()
    cur = db.cursor()

    if filter_subject and filter_subject != "Toate materiile":
        cur.execute("""
            SELECT subject, grade, date_given
            FROM grades
            WHERE student_id=%s AND subject=%s
            ORDER BY subject, date_given
        """, (student_id, filter_subject))
    else:
        cur.execute("""
            SELECT subject, grade, date_given
            FROM grades
            WHERE student_id=%s
            ORDER BY subject, date_given
        """, (student_id,))
    rows = cur.fetchall()

    # Media la purtare
    cur.execute("SELECT grade FROM conduct_grades WHERE student_id=%s", (student_id,))
    r = cur.fetchone()
    conduct = r[0] if r else 10.0
    db.close()

    tree.delete(*tree.get_children())
    subjects = {}
    all_grades = []

    for subj, grade, date in rows:
        tree.insert("", "end", values=(subj, date.strftime("%d.%m.%Y"), grade))
        subjects.setdefault(subj, []).append(grade)
        all_grades.append(grade)

    # === LEFT BOX ===
    left_box.config(state=tk.NORMAL)
    left_box.delete("1.0", tk.END)
    left_box.insert(tk.END, f"Media la purtare: {conduct:.2f}\n")

    if filter_subject == "Toate materiile" and all_grades:
        gen = sum(all_grades) / len(all_grades)
        left_box.insert(tk.END, f"Media generală: {gen:.2f}")
    elif filter_subject == "Toate materiile":
        left_box.insert(tk.END, "Media generală: -")

    left_box.config(state=tk.DISABLED)

    # === RIGHT BOX ===
    right_box.config(state=tk.NORMAL)
    right_box.delete("1.0", tk.END)

    if not rows:
        right_box.insert(tk.END, "Nicio notă momentan.")
    elif filter_subject and filter_subject != "Toate materiile":
        grades = subjects.get(filter_subject, [])
        if grades:
            avg = sum(grades) / len(grades)
            right_box.insert(tk.END, f"Media la {filter_subject}: {avg:.2f}")
        else:
            right_box.insert(tk.END, f"Nicio notă la {filter_subject}.")
    else:
        for subj, grades in subjects.items():
            avg = sum(grades) / len(grades)
            right_box.insert(tk.END, f"Media la {subj}: {avg:.2f}\n")

    right_box.config(state=tk.DISABLED)


root = tk.Tk()
root.title("Autentificare Elev")
root.geometry("340x250")
root.configure(bg="#eaf2fa")
tk.Label(root, text="Autentificare Elev", font=("Segoe UI", 14, "bold"), bg="#344675", fg="white", pady=10).pack(
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
