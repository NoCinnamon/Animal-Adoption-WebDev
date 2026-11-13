import sqlite3
import csv
import bcrypt


class AnimalDatabase:
    def __init__(self, db="data/adoption.db"):
        self.db = db

    def connect(self):
        con = sqlite3.connect(self.db)
        return con

    def create_table(self):
        con = self.connect()
        con.execute("""
            CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            image TEXT NOT NULL
            )
        """)
        columns = [row[1] for row in con.execute("PRAGMA table_info(animals)")]             # PRAGMA schema.table_info(table-name);
        if "image" not in columns:
            con.execute("ALTER TABLE animals ADD COLUMN image TEXT")
        con.commit()
        con.close()

    def list_animals(self):
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM animals") 
        list = cur.fetchall()
        con.close()
        return list

    def get(self, animal_id):
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM animals WHERE id = ?", (animal_id,)) 
        row = cur.fetchone()
        con.close() 
        return row

    def create(self, animal):
        con = self.connect()
        cur = con.cursor()
        cur.execute("INSERT INTO animals (name, species, breed, gender, age, description, status, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", animal)
        con.commit()
        rowId = cur.lastrowid
        con.close()
        return rowId

    def replace(self, animal_id, animal):
        con = self.connect()
        cur = con.cursor()
        cur.execute(
            "UPDATE animals SET name = ?, species = ?, breed = ?, gender = ?, age = ?, description = ?, status = ?, image = ? WHERE id = ?",
            (*animal, animal_id)
        )
        con.commit()
        rowCount = cur.rowcount
        con.close()
        return rowCount

    def delete(self, animal_id):
        con = self.connect()
        cur = con.cursor()
        cur.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
        rowId = cur.rowcount
        con.commit()
        con.close()
        return rowId

    def delete_all(self):
        con = self.connect()
        cur = con.cursor()
        cur.execute("DELETE FROM animals")
        cur.execute("DELETE FROM sqlite_sequence WHERE name = 'animals'")
        con.commit()
        con.close()
        
#------------------------------ UserDatabase ----------------------------------------------------------------

class UserDatabase:
    def __init__(self, db="data/adoption.db"):
        self.db = db

    def connect(self):
        con = sqlite3.connect(self.db)
        return con

    def create_table(self):
        con = self.connect()
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
            )
        """)
        con.commit()
        con.close()

    def create(self, user):
        con = self.connect()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users (first_name, last_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            user,
        )
        con.commit()
        row_id = cur.lastrowid
        con.close()
        return row_id

    def list_users(self):
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM users") 
        list = cur.fetchall()
        con.close()
        return list

    def get_by_email(self, email):
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        con.close()
        return row


#------------------------------ ApplicationDatabase -----------------------------------------------


class ApplicationDatabase:
    def __init__(self, db="data/adoption.db"):
        self.db = db

    def connect(self):
        con = sqlite3.connect(self.db)
        return con
    
    def create_table(self):
        con = self.connect()
        con.execute("""
            CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL DEFAULT CURRENT_DATE,
            user_id INTEGER NOT NULL,
            phone TEXT NOT NULL,
            animal_id INTEGER NOT NULL,
            message TEXT NOT NULL
            )
        """)
        con.commit()
        con.close()
    
    def create(self, application):
        con = self.connect()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO applications (user_id, animal_id, phone, message) VALUES (?, ?, ?, ?)",
            application,
        )
        con.commit()
        row_id = cur.lastrowid
        con.close()
        return row_id

    def list_applications(self):
        con = self.connect()
        cur = con.cursor()
        cur.execute("""
            SELECT applications.id, applications.date,
                users.first_name, users.last_name,
                applications.phone,
                animals.name,
                applications.message
            FROM applications
            JOIN users ON users.id = applications.user_id
            JOIN animals ON animals.id = applications.animal_id 
        """)
        rows = cur.fetchall()
        con.close()
        return rows

    def list_by_user(self, user_id):
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM applications WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()
        con.close()
        return rows

    def get_Application(self, application_id):
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT * FROM applications WHERE id = ?", (application_id,))
        row = cur.fetchone()
        con.close()
        return row

    def delete_Application(self, application_id):
        con = self.connect()
        cur = con.cursor()
        cur.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        con.commit()
        row_count = cur.rowcount
        con.close()
        return row_count






if __name__ == "__main__":
    db = AnimalDatabase()
    db.create_table()
    UserDatabase().create_table()
    ApplicationDatabase().create_table()

    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM animals")
    count = cur.fetchone()[0]
    if count == 0:
        with open("animal-list.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            data = []
            for name, species, breed, gender, age, description, status, image in reader:
                data.append(
                    (None, 
                    name, 
                    species, 
                    breed, 
                    gender, 
                    float(age), 
                    description or None, 
                    status,
                    image or None)
                )
        
            cur.executemany("INSERT INTO animals VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    
    con.commit()
    con.close()

    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        with open("user-list.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            data = []
            for first_name, last_name, email, password, role in reader:
                password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                data.append(
                    (None, 
                    first_name, 
                    last_name, 
                    email, 
                    password_hash, 
                    role)
                )  
            cur.executemany("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?)", data)
    con.commit()
    con.close()

    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM applications")
    count = cur.fetchone()[0]
    if count == 0:
        with open("application-list.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            data = []
            for date, user_id, phone, animal_id, message in reader:
                data.append(
                    (date,
                    int(user_id),
                    phone,
                    int(animal_id),
                    message)
                )
            cur.executemany(
                "INSERT INTO applications (date, user_id, phone, animal_id, message) VALUES (?, ?, ?, ?, ?)",
                data,
            )
    con.commit()
    con.close()

    # db.get(1)
    # db.create(("Smokey", "Dog", "Border Collie", "Male", 2, "cutest forevery", "Available"))
    # db.delete(1)
    # db.replace(10, ("Rockey", "Dog", "Border Collie", "Male", 2, "Funny dog", "Available", "images/dog-Rockey"))
    
    for animal in db.list_animals():
        print(animal)
    print("\n")

    for user in UserDatabase().list_users():
        print(user)
    print("\n")

    for application in ApplicationDatabase().list_applications():
        print(application) 

    
