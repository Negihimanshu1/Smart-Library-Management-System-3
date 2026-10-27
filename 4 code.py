# ==============================================================================
# SMART LIBRARY MANAGEMENT SYSTEM (Optimized UI & Logic)
# Python + Tkinter + Oracle Database + PL/SQL
# ==============================================================================

from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import oracledb
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


class LibraryApp:
    # Modern Indigo & Slate Theme Palette
    BG = "#F8FAFC"
    CARD_BG = "#FFFFFF"
    PRIMARY = "#4F46E5"      # Indigo
    PRIMARY_HOVER = "#4338CA"
    SUCCESS = "#10B981"      # Emerald
    SUCCESS_HOVER = "#059669"
    INFO = "#3B82F6"         # Blue
    INFO_HOVER = "#2563EB"
    WARNING = "#F59E0B"      # Amber
    WARNING_HOVER = "#D97706"
    DANGER = "#EF4444"       # Red
    DANGER_HOVER = "#DC2626"
    TEXT = "#0F172A"
    MUTED = "#64748B"
    BORDER = "#E2E8F0"

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Library Management System")
        self.root.geometry("600x750")
        self.root.minsize(520, 640)
        self.root.configure(bg=self.BG)

        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TEntry", padding=10, font=("Segoe UI", 11))

    def build_ui(self):
        # Main Scrollable Container
        self.canvas = tk.Canvas(self.root, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.main = tk.Frame(self.canvas, bg=self.BG, padx=20, pady=20)
        self.window_id = self.canvas.create_window((0, 0), window=self.main, anchor="nw")

        self.main.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window_id, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))

        # Header Section
        header = tk.Frame(self.main, bg=self.PRIMARY, padx=20, pady=18)
        header.pack(fill="x", pady=(0, 16))

        tk.Label(header, text="📚 Smart Library Dashboard", font=("Segoe UI", 18, "bold"), bg=self.PRIMARY, fg="#FFFFFF").pack(anchor="w")
        tk.Label(header, text="Manage books, members, issues & fines efficiently", font=("Segoe UI", 10), bg=self.PRIMARY, fg="#E0E7FF").pack(anchor="w", pady=(4, 0))

        # Input Section Card
        self.section_label("Transaction Details", "Enter identifiers and auto-calculated due dates")
        form = tk.Frame(self.main, bg=self.CARD_BG, padx=16, pady=14, highlightbackground=self.BORDER, highlightthickness=1)
        form.pack(fill="x", pady=(0, 16))

        self.member_entry = self.create_input(form, "Member ID")
        self.book_entry = self.create_input(form, "Book ID")

        # Issue Date with automatic tracking
        tk.Label(form, text="Issue Date (YYYY-MM-DD)", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, fg=self.TEXT).pack(anchor="w", pady=(6, 2))
        self.issue_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.issue_date_var.trace_add("write", self.update_due_date)
        self.issue_entry = ttk.Entry(form, textvariable=self.issue_date_var)
        self.issue_entry.pack(fill="x", pady=(0, 4))

        # Due Date (Read-Only / Automatically Calculated as Issue Date + 15 Days)
        tk.Label(form, text="Due Date (Auto-calculated: +15 Days)", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, fg=self.TEXT).pack(anchor="w", pady=(6, 2))
        self.due_date_var = tk.StringVar()
        self.due_entry = ttk.Entry(form, textvariable=self.due_date_var, state="readonly")
        self.due_entry.pack(fill="x", pady=(0, 4))
        
        # Initialize due date on startup
        self.update_due_date()

        # Actions Section Card
        self.section_label("Library Operations", "Select a transaction or report action")
        actions = tk.Frame(self.main, bg=self.BG)
        actions.pack(fill="x", pady=(0, 16))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        self.action_card(actions, "📗 Issue Book", "PL/SQL Procedure", self.issue_book, self.SUCCESS, 0, 0)
        self.action_card(actions, "💰 Calculate Fine", "Check Overdue Fees", self.calculate_fine, self.INFO, 0, 1)
        self.action_card(actions, "🔎 View Issued", "Search Active Issues", self.view_issued_books_smart, self.PRIMARY, 1, 0)
        self.action_card(actions, "📦 Low Stock", "Inventory Status", self.show_report, self.WARNING, 2, 0)
        self.action_card(actions, "📘 Book Issued", "All Issued & Pagination", self.open_issued_books_window, self.INFO, 1, 1)
        # Danger Zone / Reset Card
        reset_card = tk.Frame(self.main, bg="#FEF2F2", padx=16, pady=14, highlightbackground="#FCA5A5", highlightthickness=1)
        reset_card.pack(fill="x", pady=(0, 10))

        tk.Label(reset_card, text="⚠️ System Maintenance", font=("Segoe UI", 11, "bold"), bg="#FEF2F2", fg="#991B1B").pack(anchor="w")
        tk.Label(reset_card, text="Clear transactional records and restore book inventory stock.", font=("Segoe UI", 9), bg="#FEF2F2", fg="#B91C1C").pack(anchor="w", pady=(2, 8))
        
        self.make_button(reset_card, "Reset Database Data", self.reset_database_data, self.DANGER, self.DANGER_HOVER).pack(fill="x")

        # Footer note
        tk.Label(self.main, text="Powered by Python, Tkinter & Oracle PL/SQL", font=("Segoe UI", 9), bg=self.BG, fg=self.MUTED).pack(pady=10)

    def update_due_date(self, *args):
        """Automatically calculates Due Date as Issue Date + 15 days."""
        try:
            issue_date_str = self.issue_date_var.get().strip()
            issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d")
            due_date = issue_date + timedelta(days=15)
            
            # Temporarily enable to update value, then set back to readonly
            self.due_entry.config(state="normal")
            self.due_date_var.set(due_date.strftime("%Y-%m-%d"))
            self.due_entry.config(state="readonly")
        except ValueError:
            # If the user is typing an invalid intermediate date format, show placeholder/warning
            self.due_entry.config(state="normal")
            self.due_date_var.set("Invalid Issue Date format")
            self.due_entry.config(state="readonly")

    def section_label(self, title, subtitle):
        f = tk.Frame(self.main, bg=self.BG)
        f.pack(fill="x", pady=(0, 6))
        tk.Label(f, text=title, font=("Segoe UI", 12, "bold"), bg=self.BG, fg=self.TEXT).pack(anchor="w")
        tk.Label(f, text=subtitle, font=("Segoe UI", 9), bg=self.BG, fg=self.MUTED).pack(anchor="w")

    def create_input(self, parent, label):
        tk.Label(parent, text=label, font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, fg=self.TEXT).pack(anchor="w", pady=(6, 2))
        entry = ttk.Entry(parent)
        entry.pack(fill="x", pady=(0, 4))
        return entry

    def action_card(self, parent, title, subtitle, command, color, row, col):
        card = tk.Frame(parent, bg=self.CARD_BG, padx=12, pady=12, highlightbackground=self.BORDER, highlightthickness=1)
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        
        tk.Label(card, text=title, font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, fg=self.TEXT).pack(anchor="w")
        tk.Label(card, text=subtitle, font=("Segoe UI", 8), bg=self.CARD_BG, fg=self.MUTED).pack(anchor="w", pady=(2, 8))
        
        hover_map = {
            self.SUCCESS: self.SUCCESS_HOVER,
            self.INFO: self.INFO_HOVER,
            self.PRIMARY: self.PRIMARY_HOVER,
            self.WARNING: self.WARNING_HOVER
        }
        self.make_button(card, "Execute", command, color, hover_map.get(color, self.PRIMARY_HOVER)).pack(fill="x")

    def make_button(self, parent, text, command, bg_color, hover_color):
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg_color, fg="#FFFFFF",
            activebackground=hover_color, activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, cursor="hand2", padx=8, pady=8
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))
        return btn

    def connect_db(self):
       # dsn = oracledb.makedsn("localhost", 1521, service_name="XEPDB1")
        return oracledb.connect(user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), dsn=os.getenv("DB_DSN"))

    def issue_book(self):
        m_id, b_id = self.member_entry.get().strip(), self.book_entry.get().strip()
        issue_str = self.issue_date_var.get().strip()
        due_str = self.due_date_var.get().strip()

        if not m_id or not b_id:
            messagebox.showerror("Input Error", "Enter both Member ID and Book ID.")
            return

        try:
            member_id, book_id = int(m_id), int(b_id)
            
            # Convert string dates to datetime objects for Oracle compatibility
            issue_date_obj = datetime.strptime(issue_str, "%Y-%m-%d")
            due_date_obj = datetime.strptime(due_str, "%Y-%m-%d")

            with self.connect_db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT title, available_copies FROM books WHERE book_id = :1", [book_id])
                    book = cursor.fetchone()

                    if not book:
                        messagebox.showwarning("Book Not Found", "This Book ID does not exist in the library.")
                        return

                    title, copies = book
                    if not copies or copies <= 0:
                        messagebox.showinfo("Book Unavailable", f"📚 {title}\n\nThis book is currently out of stock.")
                        return

                    out_msg = cursor.var(oracledb.STRING)
                    # Pass issue_date and due_date to the updated PL/SQL procedure
                    cursor.callproc("issue_book_proc", [member_id, book_id, issue_date_obj, due_date_obj, out_msg])
                    messagebox.showinfo("Result", out_msg.getvalue())

        except ValueError:
            messagebox.showerror("Format Error", "IDs must be valid numbers and dates must be in YYYY-MM-DD format.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def calculate_fine(self):
        m_id = self.member_entry.get().strip()
        if not m_id:
            messagebox.showerror("Input Error", "Enter Member ID to check fine.")
            return

        try:
            with self.connect_db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT t.book_id, b.title, t.issue_date, t.due_date
                           FROM library_transactions t JOIN books b ON t.book_id = b.book_id
                           WHERE t.member_id = :1 AND t.status = 'ISSUED'""",
                        [int(m_id)]
                    )
                    rows = cursor.fetchall()

            if not rows:
                self.show_scrollable_popup("Fine & Status Details", f"Member ID {m_id} has no active issued books.")
                return

            today, report, total_fine, has_overdue = datetime.now().date(), f"FINE & ISSUED BOOKS | MEMBER {m_id}\n\n", 0, False
            for b_id, title, issue_dt, due_dt in rows:
                due = due_dt.date() if hasattr(due_dt, "date") else due_dt
                if today > due:
                    days_late = (today - due).days
                    fine = days_late * 10
                    total_fine += fine
                    has_overdue = True
                    status = f"OVERDUE | Rs. {fine} ({days_late} days)"
                else:
                    status = "ON TIME | No Charge"

                report += f"Book ID: {b_id} | Title: {title}\nIssue Date: {issue_dt:%Y-%m-%d}\nDue Date: {due_dt:%Y-%m-%d}\nStatus: {status}\n{'-'*45}\n"

            report += f"\nTotal Overdue Fine: Rs. {total_fine}" if has_overdue else "\nAll books are on time. No charge!"
            self.show_scrollable_popup("Fine & Status Details", report)

        except ValueError:
            messagebox.showerror("Format Error", "Member ID must be numeric.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def view_issued_books_smart(self):
        m_id, b_id = self.member_entry.get().strip(), self.book_entry.get().strip()
        if not m_id and not b_id:
            messagebox.showerror("Input Error", "Enter Member ID or Book ID.")
            return

        try:
            if m_id: int(m_id)
            if b_id: int(b_id)

            with self.connect_db() as connection:
                with connection.cursor() as cursor:
                    if b_id and not m_id:
                        cursor.execute(
                            """SELECT t.member_id, m.name, t.book_id, b.title, t.issue_date, t.due_date
                               FROM library_transactions t JOIN members m ON t.member_id = m.member_id
                               JOIN books b ON t.book_id = b.book_id WHERE t.book_id = :1 AND t.status = 'ISSUED'""",
                            [int(b_id)]
                        )
                        rows = cursor.fetchall()
                        report = f"ISSUED RECORDS | BOOK {b_id}\n\n"
                        if not rows:
                            report = f"Book ID {b_id} has no active issue records."
                        else:
                            today = datetime.now().date()
                            for mem_id, name, bk_id, title, issue_dt, due_dt in rows:
                                due = due_dt.date() if hasattr(due_dt, "date") else due_dt
                                fine = (today - due).days * 10 if today > due else 0
                                report += f"Member ID: {mem_id} | Name: {name}\nBook: {title}\nDue Date: {due_dt:%Y-%m-%d}\nFine: Rs. {fine}\n{'-'*45}\n"
                    elif b_id:
                        cursor.execute(
                            """SELECT t.book_id, b.title, t.issue_date, t.due_date, t.status
                               FROM library_transactions t JOIN books b ON t.book_id = b.book_id
                               WHERE t.member_id = :1 AND t.book_id = :2 AND t.status = 'ISSUED'""",
                            [int(m_id), int(b_id)]
                        )
                        rows = cursor.fetchall()
                        report = self.format_member_rows(rows, f"MEMBER {m_id} | BOOK {b_id}\n\n")
                    else:
                        cursor.execute(
                            """SELECT t.book_id, b.title, t.issue_date, t.due_date, t.status
                               FROM library_transactions t JOIN books b ON t.book_id = b.book_id
                               WHERE t.member_id = :1 AND t.status = 'ISSUED'""",
                            [int(m_id)]
                        )
                        rows = cursor.fetchall()
                        report = self.format_member_rows(rows, f"ISSUED BOOKS | MEMBER {m_id}\n\n")

            self.show_scrollable_popup("Issued Books Records", report)

        except ValueError:
            messagebox.showerror("Format Error", "IDs must be valid numeric values.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def format_member_rows(self, rows, report):
        if not rows:
            return report + "No active issued books found."
        today = datetime.now().date()
        for bk_id, title, issue_dt, due_dt, status in rows:
            due = due_dt.date() if hasattr(due_dt, "date") else due_dt
            fine = (today - due).days * 10 if today > due else 0
            report += f"Book ID: {bk_id}\nTitle: {title}\nIssue Date: {issue_dt:%Y-%m-%d}\nDue Date: {due_dt:%Y-%m-%d}\nFine: Rs. {fine}\n{'-'*45}\n"
        return report

    def show_report(self):
        try:
            with self.connect_db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT book_id, title, available_copies FROM books WHERE available_copies <= 2")
                    rows = cursor.fetchall()

            report = "LOW STOCK BOOKS REPORT (<= 2 COPIES)\n\n"
            if rows:
                for b_id, title, copies in rows:
                    report += f"Book ID: {b_id} | Title: {title}\nRemaining Copies: {copies}\n{'-'*45}\n"
            else:
                report = "All books have sufficient stock (> 2 copies)."

            self.show_scrollable_popup("Low Stock Report", report)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def reset_database_data(self):
        if not messagebox.askyesno("Confirm Reset", "Delete transaction data and reset stock?"):
            return
        try:
            with self.connect_db() as connection:
                with connection.cursor() as cursor:
                    out_msg = cursor.var(oracledb.STRING)
                    cursor.callproc("reset_library_data", [out_msg])
                    messagebox.showinfo("Reset Status", out_msg.getvalue())
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def show_scrollable_popup(self, title_text, info_text):
        popup = tk.Toplevel(self.root)
        popup.title(title_text)
        popup.geometry("520x420")
        popup.minsize(360, 280)
        popup.configure(bg=self.BG)

        header = tk.Frame(popup, bg=self.PRIMARY, padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="📋 " + title_text, font=("Segoe UI", 12, "bold"), bg=self.PRIMARY, fg="#FFFFFF").pack(anchor="w")

        content = tk.Frame(popup, bg=self.CARD_BG, padx=8, pady=8)
        content.pack(fill="both", expand=True, padx=12, pady=12)

        text = tk.Text(content, wrap="word", font=("Consolas", 10), bg=self.CARD_BG, fg=self.TEXT, relief="flat", padx=8, pady=8)
        scroll = ttk.Scrollbar(content, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        text.insert(tk.END, info_text)
        text.config(state="disabled")

        self.make_button(popup, "Close Report", popup.destroy, self.PRIMARY, self.PRIMARY_HOVER).pack(pady=(0, 12))

    def open_issued_books_window(self):
            """Opens a window displaying all issued books with a scrollable list, search, fixed pagination, and Done button."""
            win = tk.Toplevel(self.root)
            win.title("All Issued Books Management")
            win.geometry("920x650")
            win.configure(bg=self.BG)

            # Top Search Frame
            search_frame = tk.Frame(win, bg=self.CARD_BG, padx=12, pady=12, highlightbackground=self.BORDER, highlightthickness=1)
            search_frame.pack(fill="x", padx=16, pady=16)

            tk.Label(search_frame, text="Search by Member ID or Member Name:", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, fg=self.TEXT).pack(side="left", padx=(0, 8))
            
            search_var = tk.StringVar()
            search_entry_box = ttk.Entry(search_frame, textvariable=search_var, width=25)
            search_entry_box.pack(side="left", padx=(0, 8))

            def on_search():
                self.load_issued_page(win, container_frame, pagination_frame, search_var.get().strip(), page=1)

            self.make_button(search_frame, "Search", on_search, self.PRIMARY, self.PRIMARY_HOVER).pack(side="left")

            # Pagination Footer Frame (Fixed at bottom so it's always visible)
            pagination_frame = tk.Frame(win, bg=self.BG, pady=10)
            pagination_frame.pack(side="bottom", fill="x", padx=16)

            # Scrollable Container for List
            container_outer = tk.Frame(win, bg=self.BG)
            container_outer.pack(fill="both", expand=True, padx=16, pady=(0, 8))

            canvas = tk.Canvas(container_outer, bg=self.BG, highlightthickness=0)
            scrollbar = ttk.Scrollbar(container_outer, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            container_frame = tk.Frame(canvas, bg=self.BG)
            window_id = canvas.create_window((0, 0), window=container_frame, anchor="nw")

            container_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
            canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

            # Initial Load (Page 1)
            self.load_issued_page(win, container_frame, pagination_frame, "", page=1)

    def load_issued_page(self, win, list_frame, pagination_frame, search_query, page):
            """Fetches 10 records per page using Oracle OFFSET-FETCH pagination and renders UI with scroll & pagination."""
            for widget in list_frame.winfo_children():
                widget.destroy()
            for widget in pagination_frame.winfo_children():
                widget.destroy()

            try:
                offset_val = (page - 1) * 10

                with self.connect_db() as connection:
                    with connection.cursor() as cursor:
                        # 1. Total Count safely fetch karo
                        if search_query:
                            if search_query.isdigit():
                                count_sql = "SELECT COUNT(*) FROM library_transactions WHERE status = 'ISSUED' AND member_id = :1"
                                cursor.execute(count_sql, [int(search_query)])
                            else:
                                count_sql = """SELECT COUNT(*) FROM library_transactions t 
                                            JOIN members m ON t.member_id = m.member_id 
                                            WHERE t.status = 'ISSUED' AND LOWER(m.name) LIKE LOWER(:1)"""
                                cursor.execute(count_sql, [f"%{search_query}%"])
                        else:
                            count_sql = "SELECT COUNT(*) FROM library_transactions WHERE status = 'ISSUED'"
                            cursor.execute(count_sql)

                        res_count = cursor.fetchone()
                        total_records = res_count[0] if res_count else 0

                        # 2. Paginated Rows fetch karo using OFFSET / FETCH NEXT
                        if search_query:
                            if search_query.isdigit():
                                sql = """
                                    SELECT t.transaction_id, t.book_id, b.title, b.author, 
                                        t.member_id, m.name, t.issue_date, t.due_date
                                    FROM library_transactions t
                                    JOIN books b ON t.book_id = b.book_id
                                    JOIN members m ON t.member_id = m.member_id
                                    WHERE t.status = 'ISSUED' AND t.member_id = :1
                                    ORDER BY t.issue_date DESC
                                    OFFSET :2 ROWS FETCH NEXT 10 ROWS ONLY
                                """
                                cursor.execute(sql, [int(search_query), offset_val])
                            else:
                                sql = """
                                    SELECT t.transaction_id, t.book_id, b.title, b.author, 
                                        t.member_id, m.name, t.issue_date, t.due_date
                                    FROM library_transactions t
                                    JOIN books b ON t.book_id = b.book_id
                                    JOIN members m ON t.member_id = m.member_id
                                    WHERE t.status = 'ISSUED' AND LOWER(m.name) LIKE LOWER(:1)
                                    ORDER BY t.issue_date DESC
                                    OFFSET :2 ROWS FETCH NEXT 10 ROWS ONLY
                                """
                                cursor.execute(sql, [f"%{search_query}%", offset_val])
                        else:
                            sql = """
                                SELECT t.transaction_id, t.book_id, b.title, b.author, 
                                    t.member_id, m.name, t.issue_date, t.due_date
                                FROM library_transactions t
                                JOIN books b ON t.book_id = b.book_id
                                JOIN members m ON t.member_id = m.member_id
                                WHERE t.status = 'ISSUED'
                                ORDER BY t.issue_date DESC
                                OFFSET :1 ROWS FETCH NEXT 10 ROWS ONLY
                            """
                            cursor.execute(sql, [offset_val])

                        rows = cursor.fetchall()

                if not rows:
                    tk.Label(list_frame, text="No active issued books found.", font=("Segoe UI", 11), bg=self.BG, fg=self.MUTED).pack(pady=20)
                    return

                # Table Header
                hdr = tk.Frame(list_frame, bg=self.PRIMARY, padx=8, pady=8)
                hdr.pack(fill="x", pady=(0, 4))
                
                headers = ["Book ID", "Title & Author", "Member", "Issue / Due", "Fine Status", "Action"]
                for h in headers:
                    tk.Label(hdr, text=h, font=("Segoe UI", 9, "bold"), bg=self.PRIMARY, fg="#FFFFFF", width=12, anchor="w").pack(side="left", padx=2)

                # Rows Rendering
                today = datetime.now().date()
                for row in rows:
                    trans_id, b_id, title, author, m_id, m_name, issue_dt, due_dt = row
                    due = due_dt.date() if hasattr(due_dt, "date") else due_dt
                    
                    days_late = (today - due).days if today > due else 0
                    fine = days_late * 10

                    row_card = tk.Frame(list_frame, bg=self.CARD_BG, padx=8, pady=6, highlightbackground=self.BORDER, highlightthickness=1)
                    row_card.pack(fill="x", pady=2)

                    tk.Label(row_card, text=str(b_id), font=("Segoe UI", 9), bg=self.CARD_BG, width=12, anchor="w").pack(side="left", padx=2)
                    
                    book_info = f"{title}\nBy {author}"
                    tk.Label(row_card, text=book_info, font=("Segoe UI", 8), bg=self.CARD_BG, width=25, anchor="w", justify="left").pack(side="left", padx=2)
                    
                    mem_info = f"ID: {m_id}\n{m_name}"
                    tk.Label(row_card, text=mem_info, font=("Segoe UI", 8), bg=self.CARD_BG, width=18, anchor="w", justify="left").pack(side="left", padx=2)
                    
                    dates_info = f"Iss: {issue_dt:%Y-%m-%d}\nDue: {due_dt:%Y-%m-%d}"
                    tk.Label(row_card, text=dates_info, font=("Segoe UI", 8), bg=self.CARD_BG, width=18, anchor="w", justify="left").pack(side="left", padx=2)
                    
                    fine_txt = f"Rs. {fine}\n({days_late}d late)" if fine > 0 else "On Time (₹0)"
                    fine_color = self.DANGER if fine > 0 else self.SUCCESS
                    tk.Label(row_card, text=fine_txt, font=("Segoe UI", 8, "bold"), bg=self.CARD_BG, fg=fine_color, width=15, anchor="w", justify="left").pack(side="left", padx=2)

                    # Done Button (Return Book)
                    def return_action(t_id=trans_id):
                        if messagebox.askyesno("Confirm Return", "Has the user returned this book?"):
                            try:
                                with self.connect_db() as connection:
                                    with connection.cursor() as cursor:
                                        out_msg = cursor.var(oracledb.STRING)
                                        cursor.callproc("return_book_proc", [t_id, out_msg])
                                        messagebox.showinfo("Result", out_msg.getvalue())
                                        self.load_issued_page(win, list_frame, pagination_frame, search_query, page)
                            except Exception as ex:
                                messagebox.showerror("Database Error", str(ex))

                    self.make_button(row_card, "Done", return_action, self.SUCCESS, self.SUCCESS_HOVER).pack(side="left", padx=2)

                # Pagination Footer Controls
                total_pages = max(1, (total_records + 9) // 10)
                
                tk.Label(pagination_frame, text=f"Page {page} of {total_pages} (Total Records: {total_records})", font=("Segoe UI", 9, "bold"), bg=self.BG, fg=self.TEXT).pack(side="left", padx=4)

                pages_container = tk.Frame(pagination_frame, bg=self.BG)
                pages_container.pack(side="right")

                for p in range(1, total_pages + 1):
                    btn_bg = self.PRIMARY if p == page else self.CARD_BG
                    btn_fg = "#FFFFFF" if p == page else self.TEXT
                    
                    def create_page_handler(target_page=p):
                        return lambda: self.load_issued_page(win, list_frame, pagination_frame, search_query, target_page)

                    p_btn = tk.Button(
                        pages_container, text=str(p), command=create_page_handler(),
                        bg=btn_bg, fg=btn_fg, font=("Segoe UI", 9, "bold"), relief="flat", padx=8, pady=2, cursor="hand2"
                    )
                    p_btn.pack(side="left", padx=2)

            except Exception as e:
                messagebox.showerror("Database Error", str(e))
if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()