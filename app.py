from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os

app = Flask(__name__)
notes_dir = os.path.join(os.getcwd(), 'notes')

# Ellenőrizzük, hogy a notes mappa létezik-e, ha nem, létrehozzuk.
if not os.path.exists(notes_dir):
    os.makedirs(notes_dir)

@app.route('/')
def index():
    notes = os.listdir(notes_dir)
    now = datetime.now()  # Aktuális dátum és idő
    return render_template('index.html', notes=notes, now=now)

# Új jegyzet írása
@app.route('/new_note', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        now = datetime.now()
        note_name = request.form['note_name']
        file_path = os.path.join(notes_dir, f"{note_name}.md")
        # UTF-8 kódolással mentés
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.form['content'])
        return redirect(url_for('index'))
    return render_template('edit.html', note=None, now=datetime.now())

# Jegyzet szerkesztése
@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_note(filename):
    file_path = os.path.join(notes_dir, filename)
    if request.method == 'POST':
        # UTF-8 kódolással mentés
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.form['content'])
        return redirect(url_for('index'))
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return render_template('edit.html', note=content, filename=filename)

# Jegyzet megtekintése olvasó módban
@app.route('/view/<filename>')
def view_note(filename):
    file_path = os.path.join(notes_dir, filename)
    with open(file_path, 'r') as f:
        content = f.read()
    return render_template('view.html', content=content)

# Jegyzet törlése
@app.route('/delete/<filename>')
def delete_note(filename):
    file_path = os.path.join(notes_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
