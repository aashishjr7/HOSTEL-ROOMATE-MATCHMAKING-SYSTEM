
from flask import Flask, request, redirect, url_for, render_template_string, send_file, flash
import itertools
import io
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_me"

# Survey questions and options
SURVEY_QUESTIONS = {
    "upperorlower_sleepberth": ["Upper", "Lower"],
    "sleep_schedule": ["Early riser", "Night owl"],
    "study_preference": ["Silence", "Group study"],
    "noise_tolerance": ["Low", "Medium", "High"],
    "personality_type": ["Introvert", "Extrovert", "Ambivert"],
    "geographical_compatibility": ["Same area", "Doesn't matter"],
    "cultural_preference": ["Same cultural/religious background", "Doesn't matter"],
    "food_preference": ["Same food habits", "Doesn't matter"],
    "academic_preference": ["Same course/class", "Doesn't matter"],
    "room_temperature_preference": ["Cold", "Hot"],
    "leisure_interests": ["Sports", "Gaming", "Movies", "Other hobbies"],
    "entertainment_style": ["Energetic", "Relaxed"],
}

# In-memory users list (list of dicts)
users = []

# Utility: calculate compatibility score between two users
def calculate_score(u1, u2):
    score = 0.0
    for key in SURVEY_QUESTIONS.keys():
        if u1.get(key) == u2.get(key):
            # average of both weights for that key
            w1 = int(u1["weights"].get(key, 5))
            w2 = int(u2["weights"].get(key, 5))
            score += (w1 + w2) / 2.0
    return score

# Route: Home - add user & list users
@app.route("/", methods=["GET", "POST"])
def index():
    global users
    if request.method == "POST":
        # collect form data
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter a name.")
            return redirect(url_for("index"))

        user = {"name": name, "created": datetime.utcnow().isoformat()}
        weights = {}
        for key in SURVEY_QUESTIONS.keys():
            val = request.form.get(key)
            user[key] = val
            w = request.form.get(f"w_{key}", "5")
            try:
                w_int = int(w)
                if w_int < 1 or w_int > 10:
                    w_int = 5
            except ValueError:
                w_int = 5
            weights[key] = w_int
        user["weights"] = weights
        users.append(user)
        flash(f"Added user: {name}")
        return redirect(url_for("index"))

    # Render form and current users
    return render_template_string(TEMPLATE_INDEX, questions=SURVEY_QUESTIONS, users=users)

# Route: Matches
@app.route("/matches")
def matches():
    pairs = []
    for u1, u2 in itertools.combinations(users, 2):
        score = calculate_score(u1, u2)
        pairs.append({"a": u1["name"], "b": u2["name"], "score": score})
    pairs = sorted(pairs, key=lambda x: x["score"], reverse=True)
    return render_template_string(TEMPLATE_MATCHES, pairs=pairs)

# Route: Export CSV
@app.route("/export")
def export_users():
    if not users:
        flash("No users to export.")
        return redirect(url_for("index"))

    output = io.StringIO()
    fieldnames = ["name"] + list(SURVEY_QUESTIONS.keys()) + [f"w_{k}" for k in SURVEY_QUESTIONS.keys()]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for u in users:
        row = {"name": u.get("name", "")}
        for k in SURVEY_QUESTIONS.keys():
            row[k] = u.get(k, "")
            row[f"w_{k}"] = u.get("weights", {}).get(k, "")
        writer.writerow(row)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="hostel_users.csv")

# Route: Clear users
@app.route("/clear", methods=["POST"])
def clear_users():
    global users
    users = []
    flash("Cleared all users.")
    return redirect(url_for("index"))

# Basic templates as strings (single-file convenience)
TEMPLATE_INDEX = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hostel Roommate Matchmaking</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { padding-top: 2rem; }
      .question { margin-bottom: 1rem; }
      .weight { width: 100px; }
      .card-user { margin-bottom: 0.5rem; }
    </style>
  </head>
  <body class="container">
    <h1>🏠 Hostel Roommate Matchmaking</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="mt-3">
          {% for m in messages %}
            <div class="alert alert-info">{{ m }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="row">
      <div class="col-md-6">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Add a user</h5>
            <form method="post">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input class="form-control" name="name" required>
              </div>

              {% for key, opts in questions.items() %}
                <div class="question">
                  <label class="form-label">{{ key.replace('_', ' ').title() }}</label>
                  <select class="form-select" name="{{ key }}">
                    {% for opt in opts %}
                      <option value="{{ opt }}">{{ opt }}</option>
                    {% endfor %}
                  </select>
                  <div class="form-text">Importance (1-10):
                    <input type="number" name="w_{{ key }}" class="form-control d-inline-block weight" min="1" max="10" value="5">
                  </div>
                </div>
              {% endfor %}

              <div class="mt-3">
                <button class="btn btn-primary" type="submit">Add User</button>
                <a class="btn btn-secondary" href="{{ url_for('matches') }}">View Matches</a>
              </div>
            </form>
          </div>
        </div>

        <form method="post" action="{{ url_for('clear_users') }}" class="mt-2">
          <button type="submit" class="btn btn-warning">Clear All Users</button>
          <a class="btn btn-success" href="{{ url_for('export_users') }}">Export CSV</a>
        </form>
      </div>

      <div class="col-md-6">
        <h4>Current Users ({{ users|length }})</h4>
        {% if users %}
          {% for u in users %}
            <div class="card card-user">
              <div class="card-body small">
                <strong>{{ u.name }}</strong><br>
                <em>Added: {{ u.created }}</em>
                <div class="mt-1">
                  {% for k in questions.keys() %}
                    <span class="badge bg-light text-dark">{{ k.replace('_',' ').title() }}: {{ u[k] }}</span>
                  {% endfor %}
                </div>
              </div>
            </div>
          {% endfor %}
        {% else %}
          <p>No users yet — add some!</p>
        {% endif %}
      </div>
    </div>
  </body>
</html>
"""

TEMPLATE_MATCHES = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Matches</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style> body { padding-top: 1rem; } </style>
  </head>
  <body class="container">
    <h1>🔗 Matches</h1>
    <p><a href="{{ url_for('index') }}">&larr; Back</a></p>

    {% if pairs %}
      <table class="table table-striped">
        <thead>
          <tr><th>Rank</th><th>User A</th><th>User B</th><th>Compatibility Score</th></tr>
        </thead>
        <tbody>
          {% for p in pairs %}
            <tr>
              <td>{{ loop.index }}</td>
              <td>{{ p.a }}</td>
              <td>{{ p.b }}</td>
              <td><strong>{{ '%.2f' % p.score }}</strong></td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No pairs to show. Add at least two users.</p>
    {% endif %}

  </body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)

