## README for assignment Resourceful:

* Resource name: animal 
* Attributes:

```
  id                Unique identifier 
  name              The animal's name 
  species           Species, like dog/cat/rabbit/... 
  breed             Breed 
  gender            Gender 
  age               Age in years  (float; if age < 1year, it will be a float) 
  description       A short description 
  status            Availability, such as Available or Adopted 
  image             Path to the animal's photo 
```

* Resource name: user
* Attributes:

```
  id                Unique identifier
  first_name        First name
  last_name         Last name
  email             Email address. Must be unique
  password_hash     bcrypt hash of the password. Not sent back to the client
  role              user, or worker
```

* Resource name: application
* Attributes:

```
  id                Unique identifier
  date              Date of the application, YYYY-MM-DD. Filled in by SQLite
  user_id           Id of the user who submitted it. Taken from the session
  phone             Phone number
  animal_id         Id of the animal they want to adopt
  message           Why they want to adopt this animal
```

`first_name`, `last_name`, and the animal's name are not columns on `applications`. `GET /applications` joins `users` and `animals` so those names can be shown.

## Database

The file is `data/adoption.db`.

```sql
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
);
```



## START THE SERVER:
python3 server.py


## REST

```
* Name:               Method                  Path for all:           in server.py:
  List                GET                     /animals                do_GET
  Retrieve            GET                     ..                      do_GET
  Create              POST                    ..                      do_POST
  Replace             PUT                     ..                      do_PUT
  Delete              DELETE                  ..                      do_DELETE

  Upload image        POST                    /upload 
  Register            POST                    /users 
  Log in              POST                    /sessions 
  Current user        GET                     /sessions |
  Log out             DELETE                  /sessions |
  List my applications  GET                   /applications |
  Create application    POST                  /applications |
```

## Description

* path: /animals

  path +  GET: list all animals  
  path +  POST: Add a new animal
* If a animal's id = 3:  

  path/3  + GET: list the animal whos id = 3  
  + PUT: edit the animal whos id = 3  
  + DLETE: delete the animal whos id = 3

--------------------------------------------------------------------------------------------------------------------------------------------
well i need to admit that in server.py i let AI wrote the def save_uploaded_files(content_type, raw). 

### List：GET /animals

`do_GET` sees the path is /animals, it then call `db.list_animals()`, change each line into JSON then send back with status code 200.   
The 3 preview animal in index.html and the all animal cards listed in animals.html use this.


Retrieve 1 animal with its id：GET /animals/<id>
if i want to extract animal id=3: GET /animals/3

path will atach the id number -> /animals/3.The server uses db.get(3) to get the row. If find, response in JSON of this animal with status code 200. if not found in database, reply with {"error": "Not found"}，and status code 404。

### Create：POST /animals

In animals.html, there is a form for Edit and Add a animal to database. 
this form starts empty, when editingId === null, Submit adds a new animal (POST). 
                        when editingId !== null, Submit is editing that animal (PUT).

the request body is a animal in JSON: name、species、breed、gender、age、description、status、image, server call db.create function to add that animal, then response with taht information with status code 201, means successful create taht animal.

### Edit Replace：PUT /animals/id

in `animal.html` page, each animal card has edit/delete button, click the edit button for taht animal, all its value will appear in the form. `editingId` is taht animal's id. 
change the filed as wish then click submit, the path becoms /animals/ followed by that id. 
request body for edit still are every field. server replaces the whole existing row with these new values by calling db.replace(...). if succeeds, it will return the updated animal with status code 200; or if the id not exsit, it will return the code 404. (but this shouldn't happen)

### Delete：DELETE /animals/id

still in`animal.html` page, on each animal card, if wish to delete a animal, click delete.
then it will call comfirm(), ask "Delete + NAME?" first. After user comfirm, send delete request, with empty request body. The server calls db.delete(...)。if successful deleted, replay with 200, otherwise, if id not exsit, or path not right, returns code 404.



------------------ Authentication ---------------------------------------
## Authentication 

### User login
user logs in with email and password.
server checks the credentials against the users table. 
if success, the identity is stored in an in memory mession, and sets a cookie, so browser will recongnize it on later requests.
if failed, error is returned and the page shows a message.
  
  If the email is not in the users table, or 
  the password does not match the stored bcrypt hash, 
  POST /sessions responds with status 401 and the error message: "Invalid email or password"

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
);
```

The bcrypt hash of the password is used to check the login. It is not returned to the client and it is not stored in the session.

### Password hashing

Registration, `POST /users`, saves the password with:

```python
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

`gensalt()` uses bcrypt's default cost. The plain password is not saved.

Login does not call `hashpw`. It calls:

```python
bcrypt.checkpw(password.encode(), password_hash.encode())
```

If the email is not in the table, or `checkpw` returns false, the server responds with status 401 and `{"error": "Invalid email or password"}`.

### session

session holdes id, first and last name, email and role.
Creates a session id with secrets.token_hex(16) and saves sessions[session_id] = user.
Sends Set-Cookie: session_id=<id>; HttpOnly; Path=/.

logout will removed the id from sessions and reset cookie.
session_id=; HttpOnly; Path=/; Max-Age=0

### REST:
Name	            Method	    Path	        Status
Log in            POST        /sessions     200 user obj/401
Current user      GET         ...           200 cookie mateches session, user obj; 
                                            401: cookie missing or unknown
Log out           DELETE      ...           200, and session cookie is cleared
Register          POST |      /users        201，new user.
                                            409 if that email is already registered 

`POST /users` reads `first_name`, `last_name`, `email`, and `password`. 
The password is hashed before the row is saved. 
The response does not include `password_hash`. 
The register page says "Registration successful." or "That email is already registered."


## Applications for adoption

Login is required. Anyone who is logged in can list their own applications and submit a new one. The server uses the session user's id, so you can only see your own application, not others.

```sql
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT CURRENT_DATE,
    user_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    animal_id INTEGER NOT NULL,
    message TEXT NOT NULL
);
```

Name                      Method        Path               Status |
List my applications      GET           /applications      200, or 401 if not logged in 
Create application        POST          /applications      201 and `{"id": <new id>}`                                                          401   if not logged in |

`POST /applications` reads `animal_id`, `phone`, and `message`. 
`user_id` comes from the session. 
SQLite fills in `date`.
