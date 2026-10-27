# Smart-Library-Management-System-3
# 📚 Smart Library Management System

A desktop library management app built with **Python (Tkinter)** and an **Oracle Database** backend. Business logic (issuing books, returning books, fine calculation, resetting data) is implemented in **PL/SQL** stored procedures and functions, while the Tkinter GUI handles user interaction.

---

## Features

- **Issue a book** – validates member status, duplicate issues and stock via the `issue_book_proc` procedure.
- **Auto due date** – due date is automatically set to *issue date + 15 days*.
- **Fine calculation** – ₹10 per overdue day, shown per member (active issued books only).
- **View issued books** – search by Member ID, Book ID, or both.
- **All issued books window** – searchable by Member ID or name, with 10-per-page pagination (Oracle `OFFSET … FETCH NEXT`).
- **Return a book** – "Done" button calls `return_book_proc`, which records the return date, fine, and restocks the book.
- **Low stock report** – lists books with 2 or fewer copies.
- **Reset database** – clears all transactions and resets every book's stock to 5.

---

## Tech Stack

| Layer      | Technology                         |
|------------|------------------------------------|
| GUI        | Python 3, Tkinter / ttk            |
| Database   | Oracle Database (XE) + PL/SQL      |
| Driver     | `oracledb`                         |
| Config     | `python-dotenv` (`.env` file)      |

---

## Project Structure

```
.
├── 4 code.py          # Main Tkinter application
├── system.sql         # Tables, sequence, sample data, PL/SQL function & procedures
├── requirement.txt    # Python dependencies
├── .env               # Database credentials (not committed)
└── .gitignore         # Ignores .env
```

---

## Database Schema

**books** – `book_id` (PK), `title`, `author`, `available_copies`

**members** – `member_id` (PK), `name`, `email`, `membership_status` (default `ACTIVE`)

**library_transactions** – `transaction_id` (PK), `member_id` (FK), `book_id` (FK), `issue_date`, `due_date`, `return_date`, `status` (`ISSUED` / `RETURNED`), `fine_amount`

**Sequence:** `trans_seq` generates transaction IDs.

### PL/SQL Objects

| Object                    | Type      | Purpose                                                        |
|---------------------------|-----------|----------------------------------------------------------------|
| `calculate_library_fine`  | Function  | Returns ₹10 × overdue days between due and return date         |
| `issue_book_proc`         | Procedure | Validates member/stock/duplicates, decrements stock, inserts transaction |
| `return_book_proc`        | Procedure | Marks transaction returned, computes fine, increments stock    |
| `reset_library_data`      | Procedure | Deletes all transactions and resets all book stock to 5        |

---

## Setup

### 1. Prerequisites

- Python 3.8+ (Tkinter is bundled with most Python installers)
- Oracle Database (e.g., Oracle XE) running locally
- A SQL client (SQL*Plus, SQL Developer, etc.)

### 2. Install dependencies

```bash
pip install -r requirement.txt
```

### 3. Create the database objects

1. Open `system.sql` and **make sure the first line is a clean comment** (`-- 1. Tables Creation`). If it begins with stray characters (e.g. `rf--`), remove them or the first `CREATE TABLE` will fail.
2. **Uncomment the `fine_amount` column**, which `return_book_proc` requires:
   ```sql
   ALTER TABLE library_transactions ADD fine_amount NUMBER DEFAULT 0;
   ```
   Run it after the `CREATE TABLE library_transactions` statement.
3. Run the whole script in your SQL client, including the PL/SQL blocks terminated by `/`.

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_DSN=localhost:1521/XEPDB1
```

> ⚠️ `.env` is already listed in `.gitignore`. Never commit real credentials. Prefer a dedicated schema user over `SYSTEM` for anything beyond local testing.

### 5. Run the app

```bash
python "4 code.py"
```

---

## Usage

1. Enter a **Member ID** and **Book ID** (sample data: members 1–11, books 1–3).
2. Set the **Issue Date** (`YYYY-MM-DD`); the due date fills in automatically.
3. Use the action cards:
   - **Issue Book** – issues the book via PL/SQL.
   - **Calculate Fine** – shows overdue fines for the member's active issues.
   - **View Issued** – looks up active issues by member and/or book.
   - **Book Issued** – opens the paginated, searchable list where you can mark books as returned.
   - **Low Stock** – shows books with ≤ 2 copies.
4. **Reset Database Data** (red card) wipes transactions and restores stock — use with care.

---

## Sample Data

| Book ID | Title              | Author            | Copies |
|---------|--------------------|-------------------|--------|
| 1       | Python Programming | Guido van Rossum  | 5      |
| 2       | Database Systems   | Elmasri           | 4      |
| 3       | ACN                | Elers             | 1      |

Eleven sample members (IDs 1–11) are inserted, all with `ACTIVE` status.

---

## Notes & Known Limitations

- Fine rate is fixed at ₹10 per day and the loan period at 15 days.
- Reset sets **every** book's stock to 5, regardless of its original quantity.
- The "Calculate Fine" and report views compute fines in Python from the current date; stored fines are only written when a book is returned.
- Mouse-wheel scrolling uses Windows-style `<MouseWheel>` events.

---

## License

For educational / academic use. Add a license of your choice if you plan to distribute.
