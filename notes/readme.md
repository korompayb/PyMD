<h1>PyMD</h1>
<h3>Python alapú Online jegyzetszerkesztő program<br></h3>
<h4>Írta: Korompay Bertalan</h4>
<br>
<br>
Hogyan működik? <br>
<br>Flask Backend:
<pre class="language-python"><code>from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os

app = Flask(__name__)
notes_dir = os.path.join(os.getcwd(), 'notes')

# Ellenőrizz&uuml;k, hogy a notes mappa l&eacute;tezik-e, ha nem, l&eacute;trehozzuk.
if not os.path.exists(notes_dir):
    os.makedirs(notes_dir)

@app.route('/')
def index():
    notes = os.listdir(notes_dir)
    now = datetime.now()  # Aktu&aacute;lis d&aacute;tum &eacute;s idő
    return render_template('index.html', notes=notes, now=now)

# &Uacute;j jegyzet &iacute;r&aacute;sa
@app.route('/new_note', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        note_name = request.form['note_name']
        file_path = os.path.join(notes_dir, f"{note_name}.md")
        with open(file_path, 'w') as f:
            f.write(request.form['content'])
        return redirect(url_for('index'))
    return render_template('edit.html', note=None)

# Jegyzet szerkeszt&eacute;se
@app.route('/edit/&lt;filename&gt;', methods=['GET', 'POST'])
def edit_note(filename):
    file_path = os.path.join(notes_dir, filename)
    if request.method == 'POST':
        with open(file_path, 'w') as f:
            f.write(request.form['content'])
        return redirect(url_for('index'))
    with open(file_path, 'r') as f:
        content = f.read()
    return render_template('edit.html', note=content, filename=filename)

# Jegyzet megtekint&eacute;se olvas&oacute; m&oacute;dban
@app.route('/view/&lt;filename&gt;')
def view_note(filename):
    file_path = os.path.join(notes_dir, filename)
    with open(file_path, 'r') as f:
        content = f.read()
    return render_template('view.html', content=content)

# Jegyzet t&ouml;rl&eacute;se
@app.route('/delete/&lt;filename&gt;')
def delete_note(filename):
    file_path = os.path.join(notes_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
</code></pre>
<p>&nbsp;</p>
<p>&Eacute;s ez a base.htm erre &eacute;p&uuml;l fel a teljes oldal:</p>
<pre class="language-markup"><code>&lt;!DOCTYPE html&gt;
&lt;html lang="en"&gt;
&lt;head&gt;
    &lt;link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&amp;display=swap" rel="stylesheet"&gt;
    &lt;link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined&amp;amp;display=swap"&gt;
    &lt;link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet"&gt;
    &lt;link href="https://cdnjs.cloudflare.com/ajax/libs/angular-material/1.1.24/angular-material.min.css"
        rel="stylesheet"&gt;
    &lt;link href="https://fonts.googleapis.com/icon?family=Material+Icons"
      rel="stylesheet"&gt;
      &lt;link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"&gt;
    &lt;meta charset="UTF-8"&gt;

    &lt;script src="https://cdn.tiny.cloud/1/8yauam9wk26s9zipy53adu6mzj02690i9jw1hpbd5opo66a6/tinymce/7/tinymce.min.js"
    referrerpolicy="origin"&gt;&lt;/script&gt;
    &lt;link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&amp;display=swap" rel="stylesheet"&gt;
  &lt;script type="importmap"&gt;
    {
      "imports": {
        "@material/web/": "https://esm.run/@material/web/"
      }
    }
  &lt;/script&gt;
  &lt;style&gt;
    form {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }
  &lt;/style&gt;
  &lt;/style&gt;
  &lt;script&gt;
    import '@material/web/button/filled-button.js';
import '@material/web/button/outlined-button.js';
import '@material/web/checkbox/checkbox.js';
  &lt;/script&gt;
  &lt;script type="module"&gt;
    import * as d3 from 'https://esm.run/d3';
    import '@material/web/all.js';
    import {styles as typescaleStyles} from '@material/web/typography/md-typescale-styles.js';

    document.adoptedStyleSheets.push(typescaleStyles.styleSheet);
  &lt;/script&gt;
  &lt;script&gt;
    tinymce.init({
        selector: 'textarea',
        plugins: 'anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount linkchecker',
        toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table | align lineheight | numlist bullist indent outdent | emoticons charmap | removeformat',
    });
&lt;/script&gt;
    &lt;meta charset="UTF-8"&gt;
    &lt;meta http-equiv="X-UA-Compatible" content="IE=edge"&gt;
    &lt;meta name="viewport" content="width=device-width, initial-scale=1.0"&gt;
    
    &lt;link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}"&gt;
&lt;/head&gt;
&lt;body&gt;
    &lt;div class="sidebar"&gt;
        &lt;div class="nav-item " &gt;
            &lt;md-icon slot="icon"&gt;home&lt;/md-icon&gt;
            Főoldal
        &lt;/div&gt;
        &lt;div class="nav-item "&gt;
            &lt;md-icon slot="icon"&gt;grade&lt;/md-icon&gt;
            Jegyeim
        &lt;/div&gt;
        &lt;div class="nav-item " &gt;
            &lt;md-icon slot="icon"&gt;calendar_month&lt;/md-icon&gt;
            &Oacute;rarend
        &lt;/div&gt;
        &lt;div class="nav-item " &gt;
            &lt;md-icon slot="icon"&gt;edit_document&lt;/md-icon&gt;
            Dolgozatok
        &lt;/div&gt;
        &lt;div class="nav-item " &gt;
            &lt;md-icon slot="icon"&gt;logout&lt;/md-icon&gt;
            Kil&eacute;p&eacute;s
        &lt;/div&gt;
        &lt;md-fab class="mode-switch" variant="primary" data-label="Switch Theme" size="medium"&gt;
            &lt;md-icon slot="icon" aria-hidden="true" id="theme-icon"&gt;dark_mode&lt;/md-icon&gt;
        &lt;/md-fab&gt;
    &lt;/div&gt;
    
    
    &lt;div class="container"&gt;
        {% block content %}{% endblock %}
    &lt;/div&gt;
    
       
    &lt;script&gt;
        document.addEventListener("DOMContentLoaded", function () {
            const switchButton = document.querySelector('.mode-switch');
            const themeIcon = document.getElementById('theme-icon');
    
            // Function to toggle the dark and light modes
            const toggleTheme = () =&gt; {
                if (document.documentElement.classList.contains('dark-mode')) {
                    document.documentElement.classList.remove('dark-mode');
                    document.documentElement.classList.add('light-mode');
                    themeIcon.textContent = 'light_mode'; // Change icon to light mode
                    localStorage.setItem('theme', 'light'); // Save the theme in localStorage
                } else {
                    document.documentElement.classList.remove('light-mode');
                    document.documentElement.classList.add('dark-mode');
                    themeIcon.textContent = 'dark_mode'; // Change icon to dark mode
                    localStorage.setItem('theme', 'dark'); // Save the theme in localStorage
                }
            };
    
            // Load the saved theme from localStorage
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                if (savedTheme === 'dark') {
                    document.documentElement.classList.add('dark-mode');
                    themeIcon.textContent = 'dark_mode';
                } else {
                    document.documentElement.classList.add('light-mode');
                    themeIcon.textContent = 'light_mode';
                }
            } else {
                // If no theme is saved, default to light mode
                document.documentElement.classList.add('light-mode');
                themeIcon.textContent = 'light_mode';
            }
    
            // Event listener for the switch button
            switchButton.addEventListener('click', toggleTheme);
        });
    &lt;/script&gt;
&lt;/body&gt;
&lt;/html&gt;
</code></pre>
<p>&nbsp;</p>
<h2><span style="text-decoration: underline; color: #e03e2d;"><em>A jegyzetek a .md (markdown) f&aacute;jlokb&oacute;l k&eacute;rődik le. Ez&aacute;ltal teljesen kompatabilis az Obsidian nev&uuml; jegyzetkezelővel!</em></span><br><br><img src="https://obsidian.md/images/screenshot-1.0-hero-combo.png" alt="Obsidian" width="615" height="363"><br>Ezen a linken let&ouml;lthető az <a title="Download" href="https://obsidian.md/" target="_blank" rel="noopener">Obsidian!</a></h2>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%; height: 108.586px;" border="1"><colgroup><col style="width: 33.2863%;"><col style="width: 33.2863%;"><col style="width: 33.2863%;"></colgroup>
<tbody>
<tr style="height: 36.1953px;">
<td>El&ouml;ny&ouml;k</td>
<td>H&aacute;tr&aacute;nyok</td>
<td>V&eacute;lem&eacute;ny</td>
</tr>
<tr style="height: 36.1953px;">
<td>Az Obsidian alapvetően ingyenes</td>
<td>Nincsen szinkroniz&aacute;l&aacute;s az esk&ouml;z&ouml;k k&ouml;z&ouml;tt</td>
<td>&nbsp;</td>
</tr>
<tr style="height: 36.1953px;">
<td>&nbsp;</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>