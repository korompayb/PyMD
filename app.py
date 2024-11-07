from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from pymongo import MongoClient
import uuid  # UUID generálásához

app = Flask(__name__)
app.secret_key = 'guzuzgu67686'  # Use a more secure key in production

# MongoDB connection
connection_string = "mongodb+srv://kberci06:DUoBaBgSuw14S2js@maincluster.arwdvps.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)
db = client.PyMD
users_collection = db.users
notes_collection = db.notes  # Create a new collection for notes



@app.route('/')
def index():
    if "username" not in session:
        return redirect(url_for('login'))

    username = session["username"]
    # Fetch user's notes from the database
    notes = notes_collection.find({"username": username})
    # Konvertáljuk az _id-t stringgé, mielőtt a sablonba küldjük
    notes = [{"note_id": str(note["note_id"]), "note_name": note["note_name"], "created_at": note["created_at"], "content": note["content"]} for note in notes]
    
    now = datetime.now()  # Current date and time
    return render_template('index.html', notes=notes, now=now, username = username)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_collection.find_one({"username": username})

        if user is None:
            return render_template('login.html', message='Felhasználó nem található')
        elif password != user['password']:
            return render_template('login.html', message='Hibás jelszó')
        else:
            session["username"] = username
            return redirect(url_for('index'))
    else:
        return render_template('login.html')

@app.route('/admin_console')
def about():
    if "username" not in session:
        return redirect(url_for('login'))
    else:
        username = session["username"]
    return render_template('about.html', username = username)


# Create a new note
@app.route('/new_note', methods=['GET', 'POST'])
def new_note():
    if "username" not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        note_name = request.form['note_name']  # A note name
        content = request.form['content']  # A jegyzet tartalma
        username = session["username"]  # A felhasználó neve

        # Generáljunk egy új UUID-t a jegyzet azonosítójának
        note_id = str(uuid.uuid4())

        # Save note to MongoDB
        notes_collection.insert_one({
            "note_id": note_id,
            "username": username,
            "note_name": note_name,
            "content": content,
            "created_at": datetime.now()
        })

        return redirect(url_for('index'))

    return render_template('edit.html', note=None, username = session["username"])  # Ha GET kérés van, akkor üres form

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Ellenőrizzük, hogy a felhasználó már létezik-e
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return render_template('login.html', message='Ez a felhasználónév már foglalt.')

        # Új felhasználó létrehozása
        users_collection.insert_one({
            "username": username,
            "password": password  # Érdemes lenne titkosítani a jelszót
        })

        return redirect(url_for('login'))

    return render_template('register.html')  # A regisztrációs űrlap


@app.route('/edit/<note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if "username" not in session:
        return redirect(url_for('login'))

    username = session["username"]

    if request.method == 'POST':
        note_name = request.form.get('note_name')
        content = request.form.get('content')

        # Ha új jegyzetet hozunk létre
        if note_id == "new":
            # Generáljunk egy új UUID-t a jegyzet azonosítójának
            new_note_id = str(uuid.uuid4())
            notes_collection.insert_one({
                "note_id": new_note_id,
                "username": username,
                "note_name": note_name,
                "content": content,
                "created_at": datetime.now()
            })
        else:
            # Ha meglévő jegyzetet frissítünk
            notes_collection.update_one(
                {"note_id": note_id},  # Keresés UUID alapján
                {"$set": {"note_name": note_name, "content": content}}
            )

        return redirect(url_for('index'))

    # Ha GET kérés érkezik
    note = None
    if note_id != "new":
        note = notes_collection.find_one({"note_id": note_id})  # Keresés UUID alapján

    return render_template('edit.html', note=note, note_id=note_id, username = username)


@app.route('/view/<note_id>')
def view_note(note_id):
    if "username" not in session:
        return redirect(url_for('login'))
    else:
        username = session["username"]
    # Keresés UUID alapján
    note = notes_collection.find_one({"note_id": note_id})
    return render_template('view.html', content=note['content'], username= username)


@app.route('/delete/<note_id>')
def delete_note(note_id):
    if "username" not in session:
        return redirect(url_for('login'))

    # Törlés UUID alapján
    notes_collection.delete_one({"note_id": note_id})
    return redirect(url_for('index'))


@app.route('/myprofile')
def myprofile():
    if "username" not in session:
        return redirect(url_for('login'))
    else:
        username = session["username"]
        return render_template('myprofile.html', username = username)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
