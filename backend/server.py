
#server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3

import os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employees.db")

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ── Init tables ──
conn = get_conn()
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'student'
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, age INTEGER, gender TEXT,
        department TEXT, email TEXT,
        course TEXT, year TEXT
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, age INTEGER, gender TEXT,
        department TEXT, email TEXT,
        salary INTEGER, phone TEXT, address TEXT
    )
""")
for u in [("supervisor","super123","supervisor"),("employee1","emp123","employee"),("student1","stu123","student"),("admin","12345","supervisor")]:
    try:
        conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", u)
    except:
        pass
conn.commit()
conn.close()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def send_cors(self, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Content-Type", ctype)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_cors()

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except:
            return {}

    def write_json(self, data, code=200):
        self.send_cors(code)
        self.wfile.write(json.dumps(data).encode())

    # ── GET ──
    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/students":
            conn = get_conn()
            rows = conn.execute("SELECT * FROM students").fetchall()
            conn.close()
            self.write_json([dict(r) for r in rows])

        elif path == "/employees":
            conn = get_conn()
            rows = conn.execute("SELECT * FROM employees").fetchall()
            conn.close()
            self.write_json([dict(r) for r in rows])

        elif path == "/analytics":
            conn = get_conn()
            ts = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            te = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            conn.close()
            self.write_json({"total_students": ts, "total_employees": te})

        else:
            self.write_json({"error": "Not found"}, 404)

    # ── POST ──
    def do_POST(self):
        d = self.read_body()

        if self.path == "/login":
            conn = get_conn()
            row = conn.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (d.get("username",""), d.get("password",""))
            ).fetchone()
            conn.close()
            if row:
                self.write_json({"success": True, "role": row["role"], "username": row["username"]})
            else:
                self.write_json({"success": False, "message": "Invalid username or password"}, 401)

        elif self.path == "/students":
            conn = get_conn()
            conn.execute(
                "INSERT INTO students (name,age,gender,department,email,course,year) VALUES (?,?,?,?,?,?,?)",
                (d.get("name",""), d.get("age",""), d.get("gender",""),
                 d.get("department",""), d.get("email",""),
                 d.get("course",""), d.get("year",""))
            )
            conn.commit()
            conn.close()
            self.write_json({"message": "Student added"})

        elif self.path == "/employees":
            conn = get_conn()
            conn.execute(
                "INSERT INTO employees (name,age,gender,department,email,salary,phone,address) VALUES (?,?,?,?,?,?,?,?)",
                (d.get("name",""), d.get("age",""), d.get("gender",""),
                 d.get("department",""), d.get("email",""),
                 d.get("salary",0), d.get("phone",""), d.get("address",""))
            )
            conn.commit()
            conn.close()
            self.write_json({"message": "Employee added"})

        else:
            self.write_json({"error": "Not found"}, 404)

    # ── PUT ──
    def do_PUT(self):
        parts = self.path.strip("/").split("/")
        d = self.read_body()

        if len(parts) == 2 and parts[0] == "students":
            conn = get_conn()
            conn.execute(
                "UPDATE students SET name=?,age=?,gender=?,department=?,email=?,course=?,year=? WHERE id=?",
                (d.get("name",""), d.get("age",""), d.get("gender",""),
                 d.get("department",""), d.get("email",""),
                 d.get("course",""), d.get("year",""), int(parts[1]))
            )
            conn.commit()
            conn.close()
            self.write_json({"message": "Student updated"})

        elif len(parts) == 2 and parts[0] == "employees":
            conn = get_conn()
            conn.execute(
                "UPDATE employees SET name=?,age=?,gender=?,department=?,email=?,salary=?,phone=?,address=? WHERE id=?",
                (d.get("name",""), d.get("age",""), d.get("gender",""),
                 d.get("department",""), d.get("email",""),
                 d.get("salary",0), d.get("phone",""), d.get("address",""), int(parts[1]))
            )
            conn.commit()
            conn.close()
            self.write_json({"message": "Employee updated"})

        else:
            self.write_json({"error": "Not found"}, 404)

    # ── DELETE ──
    def do_DELETE(self):
        parts = self.path.strip("/").split("/")

        if len(parts) == 2 and parts[0] == "students":
            conn = get_conn()
            conn.execute("DELETE FROM students WHERE id=?", (int(parts[1]),))
            conn.commit()
            conn.close()
            self.write_json({"message": "Student deleted"})

        elif len(parts) == 2 and parts[0] == "employees":
            conn = get_conn()
            conn.execute("DELETE FROM employees WHERE id=?", (int(parts[1]),))
            conn.commit()
            conn.close()
            self.write_json({"message": "Employee deleted"})

        else:
            self.write_json({"error": "Not found"}, 404)


server = HTTPServer(("localhost", 8000), Handler)
print("API running on http://localhost:8000")
print("  student1 / stu123")
print("  employee1 / emp123")
print("  supervisor / super123")
server.serve_forever()
