from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from pymongo import MongoClient
import uuid  # UUID generálásához
import re
from html import escape
from bs4 import BeautifulSoup

BADGE_MAP = {
    'switch': 'topo-switch',
    'router': 'topo-router',
    'server': 'topo-server',
    'pc': 'topo-pc',
    'laptop': 'topo-pc',
    'cisco': 'topo-vendor-cisco',
    'linksys': 'topo-vendor-linksys',
    'dhcp': 'topo-proto-dhcp',
    'ospf': 'topo-proto-ospf',
    'eigrp': 'topo-proto-eigrp',
    'stp': 'topo-proto-stp',
    'nat': 'topo-proto-nat',
    'acl': 'topo-proto-acl',
    'vlan': 'topo-proto-vlan',
}

iface_ip_map = {
    "Fa0/1": "192.168.0.10",
    "Gig1/0": "10.0.0.1",
    "S0/0/0": "172.16.0.1"
}


RE_DEVICE_NAME = re.compile(r'\b([SR]?\d{1,2}|PC\d{1,2})\b', re.IGNORECASE)

RE_VLAN_RANGE = re.compile(r'\bVLAN(\d+)(?:-(\d+))?\b', re.IGNORECASE)

# Interfészek
RE_FAST   = re.compile(r'\b(?:FastEthernet|Fa|Fast|F)(\d+(?:/\d+)*)\b', re.IGNORECASE)
RE_GIG    = re.compile(r'\b(?:GigabitEthernet|Gi|Gig|G)(\d+(?:/\d+)*)\b', re.IGNORECASE)
RE_SERIAL = re.compile(r'\b(?:Serial|Se)(\d+(?:/\d+)*)\b', re.IGNORECASE)

def make_device_box(dev_type, name, address, mask):
    # Biztonságos kiírás, üres stringgel ha None
    name = name or ''
    address = address or ''
    mask = mask or ''

    icon_svg = f'''
    <svg class="device-icon {escape(dev_type)}" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="4" y="4" width="16px" height="16px" rx="3" ry="3" />
    </svg>
    '''
    icon_png = f'''
    <img class="device-icon" src="/static/{escape(dev_type)}.png">
    '''

    return f'''
    <div class="device-box {escape(dev_type)}">
      {icon_png}
      <div class="device-name">{escape(name)}</div>
      <div class="device-ip">{escape(address)}</div>
      <div class="device-mask">{escape(mask)}</div>
    </div>
    '''


def annotate_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    topo_section = soup.find('section', class_='topology')
    if not topo_section:
        return html, {}

    summary = {"devices": [], "vlans": [], "interfaces": []}

    # --- Eszköz dobozok a section class + data-* alapján ---
    for dev_section in topo_section.find_all('section'):
        classes = dev_section.get('class') or []
        # csak ha pontosan eszköz class van
        dev_classes = {'switch', 'router', 'pc', 'server'}
        matched = [c for c in classes if c in dev_classes]
        if not matched:
            continue

        dev_type = matched[0]
        dev = {
            "type": dev_type,
            "name": dev_section.get("data-name"),
            "address": dev_section.get("data-address"),
            "mask": dev_section.get("data-mask"),
        }
        summary["devices"].append(dev)

        # Helyettesítés dobozzal
        box_html = make_device_box(dev['type'], dev['name'], dev['address'], dev['mask'])
        dev_section.replace_with(BeautifulSoup(box_html, 'html.parser'))

    # --- Szöveges kulcsszavak badge-elése ---
    def badge_keyword(m):
        word = m.group(0)
        cls = BADGE_MAP.get(word.lower(), 'topo-badge')
        return f'<span class="topo-badge {cls}">{escape(word)}</span>'

    pattern = re.compile(r'\b(' + '|'.join(BADGE_MAP.keys()) + r')\b', re.IGNORECASE)

    for tnode in topo_section.find_all(string=True):
        if tnode.parent.name in ['script', 'style']:
            continue
        original = tnode
        text = str(tnode)
        def vlan_badge(m):
            start = m.group(1)
            end = m.group(2)
            if end:
                rng = f"VLAN{start}-{end}"
            else:
                rng = f"VLAN{start}"
            if rng not in summary["vlans"]:
                summary["vlans"].append(rng)
            return f'<span class="topo-badge topo-proto-vlan">{rng}</span>'
        text = RE_VLAN_RANGE.sub(vlan_badge, text)

        # FastEthernet
        def fast_badge(m):
            iface = f"Fa{m.group(1)}"
            if iface not in summary["interfaces"]:
                summary["interfaces"].append(iface)
            return f'<span class="topo-badge topo-if-fast">{iface}</span>'

        text = RE_FAST.sub(fast_badge, text)

        # GigabitEthernet
        def gig_badge(m):
            iface = f"Gig{m.group(1)}"
            if iface not in summary["interfaces"]:
                summary["interfaces"].append(iface)
            return f'<span class="topo-badge topo-if-gig">{iface}</span>'
        text = RE_GIG.sub(gig_badge, text)

        # Serial
        def serial_badge(m):
            iface = f"S{m.group(1)}"
            if iface not in summary["interfaces"]:
                summary["interfaces"].append(iface)
            return f'<span class="topo-badge topo-if-serial">{iface}</span>'
        text = RE_SERIAL.sub(serial_badge, text)
        
        text = pattern.sub(lambda m: badge_keyword(m), original)
        if text != original:
            new_fragment = BeautifulSoup(text, 'html.parser')
            tnode.replace_with(new_fragment)

    return str(soup), summary

app = Flask(__name__)
app.secret_key = 'guzuzgu67686'  # Use a more secure key in production

# MongoDB connection
connection_string = "mongodb+srv://kberci06:DUoBaBgSuw14S2js@maincluster.arwdvps.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)
db = client.PyMD
users_collection = db.users
notes_collection = db.notes  # Create a new collection for notes

version = "2.0.4 (Networking Topology)"  # Verzió szám


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
    return render_template('index.html', notes=notes, now=now, username = username, show_popup='false', version=version)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # GET-ből vagy POST-ból is jöhet
    next_url = request.args.get('next') or request.form.get('next')
    if next_url is None:
        next_url = "/"
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_collection.find_one({"username": username})

        if user is None:
            return render_template('login.html', message='Felhasználó nem található', next=next_url)
        elif password != user['password']:
            return render_template('login.html', message='Hibás jelszó', next=next_url)
        else:
            session["username"] = username
            if next_url:
                return redirect(next_url)
            return redirect(url_for('index', show_popup='true', version=version))
    else:
        return render_template('login.html', next=next_url)


@app.route('/admin_console')
def about():
    if "username" not in session:
        return redirect(url_for('login'))
    else:
        username = session["username"]
    return render_template('about.html', username = username, version=version)


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

    return render_template('register.html', version=version)  # A regisztrációs űrlap


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
            return redirect(url_for('view_note', note_id=new_note_id))
        else:
            # Ha meglévő jegyzetet frissítünk
            notes_collection.update_one(
                {"note_id": note_id},  # Keresés UUID alapján
                {"$set": {"note_name": note_name, "content": content}}
            )
            return redirect(url_for('view_note', note_id=note_id))

       

    # Ha GET kérés érkezik
    note = None
    if note_id != "new":
        note = notes_collection.find_one({"note_id": note_id})  # Keresés UUID alapján

    return render_template('edit.html', note=note, note_id=note_id, username = username)


@app.route('/view/<note_id>')
def view_note(note_id):
    if "username" not in session:
        return redirect(url_for('login', next=url_for('view_note', note_id=note_id)))

    username = session["username"]

    note = notes_collection.find_one({"note_id": note_id})
    annotated_html, topo_summary = annotate_text(note['content'])

    return render_template(
        'view.html',
        content=annotated_html,
        topo=topo_summary,
        username=username,
        note=note,
        version=version
    )


@app.route('/settings')
def settings():
    if "username" not in session:
        return redirect(url_for('login'))
    else:
        username = session["username"]
        user = users_collection.find_one({"username": username})
    return render_template('settings.html', username=username, version=version)


@app.route('/delete/<note_id>')
def delete_note(note_id):
    if "username" not in session:
        return redirect(url_for('login'))

    # Törlés UUID alapján
    notes_collection.delete_one({"note_id": note_id})
    return redirect(url_for('index'), version=version)


@app.route('/myprofile')
def myprofile():
    if "username" not in session:
        return redirect(url_for('login'))
    else:
        username = session["username"]
        email = users_collection.find_one({"username": username}).get("email", "N/A")
        created_at = users_collection.find_one({"username": username}).get("created_at", "N/A")
        note_count = notes_collection.count_documents({"username": username})  # Jegyzetek száma
        return render_template('myprofile.html', username = username, email=email, created_at=created_at, note_count=note_count, version=version)


@app.route('/history')
def history():
    if "username" not in session:
        return redirect(url_for('login'))
    else:
        username = session["username"]
    return render_template('history.html', username = username, version=version)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
