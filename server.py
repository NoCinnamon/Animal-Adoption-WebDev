from http.server import BaseHTTPRequestHandler, HTTPServer
from email.parser import BytesParser
from email.policy import default
import json
import os
import re
import bcrypt
import secrets
from database import AnimalDatabase, UserDatabase, ApplicationDatabase

db = AnimalDatabase()
user_db = UserDatabase()
sessions = {}
application_db = ApplicationDatabase()

ANIMAL_COLUMNS = ("id", "name", "species", "breed", "gender", "age", "description", "status", "image")
USER_COLUMNS = ("id", "first_name", "last_name", "email", "password_hash", "role")
APPLICATION_COLUMNS = ("id", "date", "first_name", "last_name", "phone", "animal_id", "animal_name", "message")

def row_to_obj(row):
    return dict(zip(ANIMAL_COLUMNS, row))

def user_to_obj(row):
    user = dict(zip(USER_COLUMNS, row))
    del user["password_hash"]
    return user

def application_to_obj(row):
    return dict(zip(APPLICATION_COLUMNS, row))

def current_user(handler):
    cookie = handler.headers.get("Cookie")
    if not cookie:
        return None
    session_id = None
    for part in cookie.split(";"):
        name, _, value = part.strip().partition("=")
        if name == "session_id":
            session_id = value
    if session_id is None:
        return None
    return sessions.get(session_id)

def allow_cors(handler):
    origin = handler.headers.get("Origin")
    if origin:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Access-Control-Allow-Credentials", "true")
    else:
        handler.send_header("Access-Control-Allow-Origin", "*")

def serve_static(handler):
    rel = handler.path.split("?", 1)[0]
    if rel == "/":
        rel = "/index.html"
    if not rel.startswith("/") or ".." in rel:
        return False
    root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(root, rel.lstrip("/")))
    if path != root and not path.startswith(root + os.sep):
        return False
    if not os.path.isfile(path):
        return False
    types = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
    }
    content_type = types.get(os.path.splitext(path)[1].lower())
    if content_type is None:
        return False
    with open(path, "rb") as f:
        data = f.read()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.end_headers()
    handler.wfile.write(data)
    return True

def require_login(handler):
    user = current_user(handler)
    if user is None:
        body = json.dumps({"error": "Got to log in first Baby!"}).encode()
        handler.send_response(401)
        handler.send_header("Content-Type", "application/json")
        allow_cors(handler)
        handler.end_headers()
        handler.wfile.write(body)
        return False
    return True

def require_worker(handler):
    user = current_user(handler)
    if user is None:
        body = json.dumps({"error": "Not logged in"}).encode()
        handler.send_response(401)
        handler.send_header("Content-Type", "application/json")
        allow_cors(handler)
        handler.end_headers()
        handler.wfile.write(body)
        return False
    if user["role"] != "worker":
        body = json.dumps({"error": "Forbidden"}).encode()
        handler.send_response(403)
        handler.send_header("Content-Type", "application/json")
        allow_cors(handler)
        handler.end_headers()
        handler.wfile.write(body)
        return False
    return True


def save_uploaded_files(content_type, raw):
    header = ("Content-Type: " + content_type + "\r\n\r\n").encode()
    message = BytesParser(policy=default).parsebytes(header + raw)
    folder = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(folder, exist_ok=True)
    saved = []
    for part in message.iter_parts():
        filename = part.get_filename()
        if not filename:
            continue
        filename = os.path.basename(filename)
        filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
        if not filename:
            continue
        stem, ext = os.path.splitext(filename)
        path = os.path.join(folder, filename)
        number = 1
        while os.path.exists(path):
            filename = stem + "-" + str(number) + ext
            path = os.path.join(folder, filename)
            number += 1
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        with open(path, "wb") as image_file:
            image_file.write(payload)
        saved.append("images/" + filename)
    return saved

class Request_Handler(BaseHTTPRequestHandler):
    def do_GET(self):                                               # list/retrive

        if self.path == "/sessions":
            user = current_user(self)
            if user is None:
                body = json.dumps({"error": "Not logged in"}).encode()
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                allow_cors(self)
                self.end_headers()
                self.wfile.write(body)
                return

            body = json.dumps(user).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        parse = self.path.split("/")

        if parse == ["", "applications"]:
            if not require_login(self):
                return
            user = current_user(self)
            applications = []
            for row in application_db.list_by_user(user["id"]):
                applications.append(application_to_obj(row))
            body = json.dumps(applications).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if parse == ["", "animals"]:
            animals = []
            for row in db.list_animals():
                animals.append(row_to_obj(row))
            body = json.dumps(animals).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if len(parse) == 3 and parse[1] == "animals":
            animal_id = int(parse[2])
            row = db.get(animal_id)
            if row is None:
                body = json.dumps({"error": "Not found"}).encode()
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                allow_cors(self)
                self.end_headers()
                self.wfile.write(body)
                return

            body = json.dumps(row_to_obj(row)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if serve_static(self):
            return

        body = json.dumps({"error": "Not found"}).encode()
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        allow_cors(self)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):                                                     # Create

        if self.path == "/applications":
            if not require_login(self):
                return
            user = current_user(self)
            length = int(self.headers["Content-Length"])
            raw = self.rfile.read(length)
            data = json.loads(raw)
            application = (
                user["id"],
                int(data["animal_id"]),
                data["phone"],
                data["message"],
            )
            new_id = application_db.create(application)
            body = json.dumps({"id": new_id}).encode()
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/upload":
            if not require_worker(self):
                return
            length = int(self.headers["Content-Length"])
            raw = self.rfile.read(length)
            saved = save_uploaded_files(self.headers.get("Content-Type", ""), raw)
            body = json.dumps({"saved": saved}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/users":
            length = int(self.headers["Content-Length"])
            raw = self.rfile.read(length)
            data = json.loads(raw)
            
            if user_db.get_by_email(data["email"]) is not None:
                body = json.dumps({"Error": "Email already registered"}).encode()
                self.send_response(409)
                self.send_header("Content-Type", "application/json")                                       
                allow_cors(self)
                self.end_headers()
                self.wfile.write(body)
                return

            password_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
            user = (
                data["first_name"],
                data["last_name"],
                data["email"],
                password_hash,
                "user",
            )
            user_db.create(user)
            row = user_db.get_by_email(data["email"])

            body = json.dumps(user_to_obj(row)).encode()
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/sessions":
            length = int(self.headers["Content-Length"])
            raw = self.rfile.read(length)
            data = json.loads(raw)

            row = user_db.get_by_email(data["email"])
            password_hash = row[4] if row is not None else None                                      # row[4] 是 password_hash   
            if password_hash is None or not bcrypt.checkpw(data["password"].encode(), password_hash.encode()):
                body = json.dumps({"error": "Invalid email or password"}).encode()
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                allow_cors(self)
                self.end_headers()
                self.wfile.write(body)
                return

            user = user_to_obj(row)                                            # ！！！
            session_id = secrets.token_hex(16)
            sessions[session_id] = user

            body = json.dumps(user).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.send_header("Set-Cookie", "session_id=" + session_id + "; HttpOnly; Path=/")
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path != "/animals":
            body = json.dumps({"Error 404: not fund"}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")                                       
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if not require_worker(self):
            return
        
        length = int(self.headers["Content-Length"])
        raw = self.rfile.read(length)
        data = json.loads(raw)
        animal = (
            data["name"],
            data["species"],
            data["breed"],
            data["gender"],
            float(data["age"]),
            data["description"],
            data["status"],
            data["image"],
        )

        new_id = db.create(animal)
        row = db.get(new_id)

        body = json.dumps(row_to_obj(row)).encode()
        self.send_response(201)
        self.send_header("Content-Type", "application/json")                                     
        allow_cors(self)
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):                                                      # Replace
        parse = self.path.split("/")                                       # after parsing: [ "", "animals",3(id)]
        if len(parse) != 3 or parse[1] != "animals":
            body = json.dumps({"Error 404: not fund"}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")                                       
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if not require_worker(self):
            return

        animal_id = int(parse[2])

        length = int(self.headers["Content-Length"])
        raw = self.rfile.read(length)
        data = json.loads(raw)
        animal = (
            data["name"],
            data["species"],
            data["breed"],
            data["gender"],
            float(data["age"]),
            data["description"],
            data["status"],
            data["image"],
        )

        changed = db.replace(animal_id, animal)
        if changed == 0: 
            body = json.dumps({"error": "Not found"}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")                                     
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return 

        row = db.get(animal_id)
        body = json.dumps(row_to_obj(row)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        allow_cors(self)
        self.end_headers()
        self.wfile.write(body)

    def do_DELETE(self):
        if self.path == "/sessions":
            cookie = self.headers.get("Cookie") or ""
            session_id = None
            for part in cookie.split(";"):
                name, _, value = part.strip().partition("=")
                if name == "session_id":
                    session_id = value
            if session_id is not None:
                sessions.pop(session_id, None)
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            allow_cors(self)
            self.send_header("Set-Cookie", "session_id=; HttpOnly; Path=/; Max-Age=0")
            self.end_headers()
            self.wfile.write(body)
            return

        parse = self.path.split("/")                                       # after parsing: [ "", "animals",3(id)]
        if len(parse) != 3 or parse[1] != "animals":
            body = json.dumps({"Error 404: not fund"}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")                                       
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return

        if not require_worker(self):
            return

        animal_id = int(parse[2])        
        changed = db.delete(animal_id)

        if changed == 0: 
            body = json.dumps({"error": "Not found"}).encode()
            self.send_response(404)
            self.send_header("Content-Type", "application/json")                                     
            allow_cors(self)
            self.end_headers()
            self.wfile.write(body)
            return 

        body = json.dumps({"deleted": animal_id}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        allow_cors(self)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        allow_cors(self)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    HTTPServer(("", 8000), Request_Handler).serve_forever()
    