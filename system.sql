-- 1. Tables Creation
CREATE TABLE books (
    book_id NUMBER PRIMARY KEY,
    title VARCHAR2(100),
    author VARCHAR2(100),
    available_copies NUMBER
);

CREATE TABLE members (
    member_id NUMBER PRIMARY KEY,
    name VARCHAR2(100),
    email VARCHAR2(100),
    membership_status VARCHAR2(20) DEFAULT 'ACTIVE'
);

CREATE TABLE library_transactions (
    transaction_id NUMBER PRIMARY KEY,
    member_id NUMBER REFERENCES members(member_id),
    book_id NUMBER REFERENCES books(book_id),
    issue_date DATE,
    due_date DATE,
    return_date DATE,
    status VARCHAR2(20)
);

--ALTER TABLE library_transactions ADD fine_amount NUMBER DEFAULT 0;
CREATE SEQUENCE trans_seq START WITH 1 INCREMENT BY 1;

-- --- Sample Data Insertion (Added to prevent NO_DATA_FOUND errors) ---
INSERT INTO books (book_id, title, author, available_copies) VALUES (1, 'Python Programming', 'Guido van Rossum', 5);
INSERT INTO books (book_id, title, author, available_copies) VALUES (2, 'Database Systems', 'Elmasri', 4);
INSERT INTO books (book_id, title, author, available_copies) VALUES (3, 'ACN', 'Elers', 1);
--UPDATE books SET available_copies = 15 WHERE book_id = 1;
--COMMIT;
INSERT INTO members (member_id, name, email, membership_status) VALUES (1, 'Rahul Sharma', 'rahul@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (2, 'Priya Verma', 'priya@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (3, 'Priyas', 'priyas@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (4, 'Verma', 'riya@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (5, 'erma', 'riya12@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (6, 'rma', 'ri3ya@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (7, 'Vema', 'ri5ya@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (8, 'Vma', 'r5iya@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (9, 'Vrma', 'r75iya@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (10, 'erm', 'r45iya@gmail.com', 'ACTIVE');
INSERT INTO members (member_id, name, email, membership_status) VALUES (11, 'ma', 'ri676ya@gmail.com', 'ACTIVE');
COMMIT;

-------------------------------------------------------------------------

-- 2. User-Defined Function: Fine Calculation based on overdue days
CREATE OR REPLACE FUNCTION calculate_library_fine(
    p_due_date IN DATE,
    p_return_date IN DATE
) RETURN NUMBER IS
    v_days NUMBER;
    v_fine NUMBER := 0;
BEGIN
    IF p_return_date > p_due_date THEN
        v_days := p_return_date - p_due_date;
        v_fine := v_days * 10; -- ₹10 per day fine
    END IF;
    RETURN v_fine;
END;
/

CREATE OR REPLACE PROCEDURE reset_library_data(
    p_message OUT VARCHAR2
) IS
BEGIN
    -- 1. Sare transactions delete kar do
    DELETE FROM library_transactions;
    
    -- 2. Books ki available copies ko wapas original state (jaise sabhi ki 5 copies kar do ya unhe reset kar do) par set kar do
    -- Yahan hum sabhi books ki copies ko 5 set kar rahe hain (aap apne hisab se change kar sakte hain)
    UPDATE books SET available_copies = 5;
    
    COMMIT;
    p_message := 'Success: All transactions cleared and database reset successfully!';
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        p_message := 'Error: ' || SQLERRM;
END;
/


CREATE OR REPLACE PROCEDURE return_book_proc(
    p_transaction_id IN NUMBER,
    p_message OUT VARCHAR2
) IS
    v_book_id NUMBER;
    v_due_date DATE;
    v_fine NUMBER := 0;
BEGIN
    -- 1. Get book_id and due_date from transaction
    SELECT book_id, due_date INTO v_book_id, v_due_date 
    FROM library_transactions 
    WHERE transaction_id = p_transaction_id AND status = 'ISSUED';

    -- 2. Calculate fine if returned after due date (SYSDATE is return date)
    IF TRUNC(SYSDATE) > TRUNC(v_due_date) THEN
        v_fine := (TRUNC(SYSDATE) - TRUNC(v_due_date)) * 10;
    END IF;

    -- 3. Update transaction status to 'RETURNED' and save fine/return date
    UPDATE library_transactions 
    SET status = 'RETURNED', 
        return_date = SYSDATE, 
        fine_amount = v_fine 
    WHERE transaction_id = p_transaction_id;

    -- 4. Increase book stock copies by 1
    UPDATE books 
    SET available_copies = available_copies + 1 
    WHERE book_id = v_book_id;

    COMMIT;
    p_message := 'Success: Book returned successfully! Fine charged: Rs. ' || v_fine;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        p_message := 'Error: Invalid or already returned transaction ID!';
    WHEN OTHERS THEN
        p_message := 'Error: ' || SQLERRM;
END;
/



-- 3. Stored Procedure with Validation: Process Book Issue & Stock Update
CREATE OR REPLACE PROCEDURE issue_book_proc(
    p_member_id IN NUMBER,
    p_book_id IN NUMBER,
    p_issue_date IN DATE,    
    p_due_date IN DATE,      
    p_message OUT VARCHAR2
) IS
    v_copies NUMBER;
    v_status VARCHAR2(20);
    v_count NUMBER;
BEGIN
    -- 1. Validation: Check if member account is active
    SELECT membership_status INTO v_status FROM members WHERE member_id = p_member_id;
    IF v_status <> 'ACTIVE' THEN
        p_message := 'Error: Member account is not active!';
        RETURN;
    END IF;

    -- 2. Validation: Check if the user already has this book issued and not returned
    SELECT COUNT(*) INTO v_count 
    FROM library_transactions 
    WHERE member_id = p_member_id AND book_id = p_book_id AND status = 'ISSUED';
    
    IF v_count > 0 THEN
        p_message := 'Error: You have already issued this book! First return it before re-issuing.';
        RETURN;
    END IF;

    -- 3. Validation: Check book stock availability
    SELECT available_copies INTO v_copies FROM books WHERE book_id = p_book_id;
    
    IF v_copies <= 0 THEN
        p_message := 'Error: Book is out of stock!';
    ELSE
        -- Update stock (Decrease by 1)
        UPDATE books SET available_copies = available_copies - 1 WHERE book_id = p_book_id;
        
        -- Insert Transaction details
        INSERT INTO library_transactions(transaction_id, member_id, book_id, issue_date, due_date, status)
        VALUES(trans_seq.NEXTVAL, p_member_id, p_book_id, p_issue_date, p_due_date, 'ISSUED');
        
        COMMIT;
        p_message := 'Success: Book issued successfully!';
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        p_message := 'Error: Invalid Member ID or Book ID!';
    WHEN OTHERS THEN
        p_message := 'Error: ' || SQLERRM;
END;
/