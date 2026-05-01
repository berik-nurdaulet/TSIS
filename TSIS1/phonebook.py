import psycopg2
import json

# CONNECTION
def connect():
    return psycopg2.connect(
        host="localhost",
        database="phonebook_db",
        user="nur",
        password="1234"
    )

# ADD CONTACT
def add_contact(conn):
    name = input("Name: ")
    email = input("Email: ")
    birthday = input("Birthday (YYYY-MM-DD): ")
    group = input("Group: ")
    phone = input("Phone: ")
    ptype = input("Type (home/work/mobile): ")

    with conn.cursor() as cur:
        # group
        cur.execute("""
            INSERT INTO groups(name)
            VALUES (%s)
            ON CONFLICT DO NOTHING
        """, (group,))
        
        cur.execute("SELECT id FROM groups WHERE name=%s", (group,))
        gid = cur.fetchone()[0]

        # contact
        cur.execute("""
            INSERT INTO contacts(name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (name, email, birthday, gid))

        cid = cur.fetchone()[0]

        # phone
        cur.execute("""
            INSERT INTO phones(contact_id, phone, type)
            VALUES (%s, %s, %s)
        """, (cid, phone, ptype))

    conn.commit()
    print(" Contact added")


# FILTER BY GROUP
def filter_by_group(conn):
    group = input("Enter group: ")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.name, c.email
            FROM contacts c
            JOIN groups g ON c.group_id = g.id
            WHERE g.name = %s
        """, (group,))

        rows = cur.fetchall()
        for r in rows:
            print(r)


# SEARCH CONTACTS (ALL FIELDS)
def search_contacts(conn):
    query = input("Search: ")

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM search_contacts(%s)", (query,))
        rows = cur.fetchall()

        for r in rows:
            print(r)


# SORT CONTACTS
def sort_contacts(conn):
    print("Sort by: name / birthday")
    sort_by = input("> ")

    if sort_by not in ["name", "birthday"]:
        sort_by = "name"

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT name, email, birthday
            FROM contacts
            ORDER BY {sort_by}
        """)

        for row in cur.fetchall():
            print(row)


# PAGINATION
def paginate(conn):
    limit = 5
    offset = 0

    while True:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
            rows = cur.fetchall()

        if not rows:
            print("No data.")
            break

        for r in rows:
            print(r)

        cmd = input("next / prev / quit: ")

        if cmd == "next":
            offset += limit
        elif cmd == "prev" and offset >= limit:
            offset -= limit
        elif cmd == "quit":
            break


# ADD PHONE (PROCEDURE)
def add_phone(conn):
    name = input("Contact name: ")
    phone = input("Phone: ")
    ptype = input("Type: ")

    with conn.cursor() as cur:
        cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))

    conn.commit()
    print(" Phone added")


# MOVE TO GROUP (PROCEDURE)
def move_group(conn):
    name = input("Contact name: ")
    group = input("New group: ")

    with conn.cursor() as cur:
        cur.execute("CALL move_to_group(%s, %s)", (name, group))

    conn.commit()
    print(" Moved")


# EXPORT JSON
def export_json(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.name, c.email, c.birthday, g.name, p.phone, p.type
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            LEFT JOIN phones p ON c.id = p.contact_id
        """)
        
        data = cur.fetchall()

    with open("contacts.json", "w") as f:
        json.dump(data, f, default=str, indent=4)

    print(" Exported to contacts.json")


# IMPORT JSON
def import_json(conn):
    with open("contacts.json") as f:
        data = json.load(f)

    with conn.cursor() as cur:
        for row in data:
            name, email, birthday, group, phone, ptype = row

            cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
            exists = cur.fetchone()

            if exists:
                choice = input(f"{name} exists (skip/overwrite): ")
                if choice == "skip":
                    continue
                else:
                    cur.execute("DELETE FROM contacts WHERE name=%s", (name,))

            # group
            cur.execute("""
                INSERT INTO groups(name)
                VALUES (%s)
                ON CONFLICT DO NOTHING
            """, (group,))

            cur.execute("SELECT id FROM groups WHERE name=%s", (group,))
            gid = cur.fetchone()[0]

            # contact
            cur.execute("""
                INSERT INTO contacts(name, email, birthday, group_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (name, email, birthday, gid))

            cid = cur.fetchone()[0]

            # phone
            cur.execute("""
                INSERT INTO phones(contact_id, phone, type)
                VALUES (%s, %s, %s)
            """, (cid, phone, ptype))

    conn.commit()
    print(" Imported")


# MENU
def menu():
    conn = connect()

    while True:
        print("\n--- PHONEBOOK ---")
        print("1. Add contact")
        print("2. Filter by group")
        print("3. Search")
        print("4. Sort")
        print("5. Pagination")
        print("6. Add phone")
        print("7. Move group")
        print("8. Export JSON")
        print("9. Import JSON")
        print("0. Exit")

        choice = input("Choose: ")

        if choice == "1":
            add_contact(conn)
        elif choice == "2":
            filter_by_group(conn)
        elif choice == "3":
            search_contacts(conn)
        elif choice == "4":
            sort_contacts(conn)
        elif choice == "5":
            paginate(conn)
        elif choice == "6":
            add_phone(conn)
        elif choice == "7":
            move_group(conn)
        elif choice == "8":
            export_json(conn)
        elif choice == "9":
            import_json(conn)
        elif choice == "0":
            conn.close()
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    menu()

