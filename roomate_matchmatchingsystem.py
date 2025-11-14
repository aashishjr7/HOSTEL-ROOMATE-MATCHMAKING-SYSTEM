#STILL IN PROGRESS I HAVEN'T COMPLETED THIS PROJECT
from flask import Flask, request, redirect, url_for, render_template_string, send_file, flash
import itertools
import io
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_me"

SURVEY_QUESTIONS = {
    "upperorlower_sleepberth": ["Upper", "Lower"],
    "sleep_schedule": ["Early riser", "Night owl","normal schedule(11pm-7am)"],
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


users = []

def parse_weight(value):
    try:
        v = int(value)
        if 1 <= v <= 10:
            return v
    except:
        pass
    return 5

def calculate_score_full(u1, u2):
    score = 0
    for key in SURVEY_QUESTIONS:
        if u1.get(key) == u2.get(key):
            w1 = u1["weights"].get(key, 5)
            w2 = u2["weights"].get(key, 5)
            score += (w1 + w2) / 2.0
    return score

def calculate_score(u1, u2):
    # If either user wants single-criterion matchmaking
    if u1["match_mode"] == "single" or u2["match_mode"] == "single":
        # pick whichever user has chosen a match_key
        key = u1["match_key"] or u2["match_key"]

        # fallback to full if invalid
        if not key or key not in SURVEY_QUESTIONS:
            return calculate_score_full(u1, u2)

        # single-criterion logic
        if u1.get(key) == u2.get(key):
            w1 = u1["weights"].get(key, 5)
            w2 = u2["weights"].get(key, 5)
            return (w1 + w2) / 2.0
        return 0.0

    # default: full matching
    return calculate_score_full(u1, u2)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter a valid name.")
            return redirect(url_for("index"))

        # Create user object
        user = {
            "name": name,
            "created": datetime.utcnow().isoformat(),
            "match_mode": request.form.get("match_mode", "full"),
            "match_key": request.form.get("match_key") or None,
            "weights": {}
        }

        for key in SURVEY_QUESTIONS:
            user[key] = request.form.get(key)
            user["weights"][key] = parse_weight(request.form.get(f"w_{key}"))

        users.append(user)
        flash(f"Added user: {name}")
        return redirect(url_for("index"))

    return render_template_string(TEMPLATE_INDEX, users=users, questions=SURVEY_QUESTIONS)


@app.route("/matches")
def matches():
    if len(users) < 2:
        flash("Add at least two users to view matches.")
        return redirect(url_for("index"))

    pairs = []
    for u1, u2 in itertools.combinations(users, 2):
        score = calculate_score(u1, u2)
        pairs.append({"a": u1["name"], "b": u2["name"], "score": score})

    pairs.sort(key=lambda x: x["score"], reverse=True)
    return render_template_string(TEMPLATE_MATCHES, pairs=pairs)


@app.route("/export")
def export_users():
    if not users:
        flash("No users to export.")
        return redirect(url_for("index"))

    output = io.StringIO()
    fieldnames = ["name", "match_mode", "match_key"] + \
        list(SURVEY_QUESTIONS) + \
        [f"w_{k}" for k in SURVEY_QUESTIONS]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for u in users:
        row = {
            "name": u["name"],
            "match_mode": u["match_mode"],
            "match_key": u["match_key"],
        }
        for key in SURVEY_QUESTIONS:
            row[key] = u.get(key)
            row[f"w_{key}"] = u["weights"][key]
        writer.writerow(row)

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="hostel_users.csv")


@app.route("/clear", methods=["POST"])
def clear_users():
    users.clear()
    flash("Cleared all users.")
    return redirect(url_for("index"))

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
      .weight { width: 80px; display: inline-block; }
    </style>
  </head>

  <body class="container">

    <h1 class="mb-4">🏠 Hostel Roommate Matchmaking</h1>

    {% for m in get_flashed_messages() %}
      <div class="alert alert-info">{{ m }}</div>
    {% endfor %}

    <div class="row">

      <!-- LEFT: ADD USER -->
      <div class="col-md-6">

        <div class="card mb-3">
          <div class="card-body">
            <h5>Add a User</h5>

            <form method="post">

              <!-- NAME -->
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input class="form-control" name="name" required>
              </div>

              <!-- MATCH MODE -->
              <div class="mb-3">
                <label class="form-label">Matchmaking Mode</label>
                <select class="form-select" name="match_mode">
                  <option value="full">Use ALL criteria (best match)</option>
                  <option value="single">Use ONLY one chosen criterion</option>
                </select>
              </div>

              <!-- MATCH KEY -->
              <div class="mb-3">
                <label class="form-label">If Single Criterion Selected, Choose:</label>
                <select class="form-select" name="match_key">
                  <option value="">-- select --</option>
                  {% for key in questions %}
                    <option value="{{ key }}">{{ key.replace('_',' ').title() }}</option>
                  {% endfor %}
                </select>
              </div>

              <!-- QUESTIONS -->
              {% for key, opts in questions.items() %}
                <div class="mb-3">
                  <label class="form-label">{{ key.replace('_',' ').title() }}</label>
                  <select class="form-select" name="{{ key }}">
                    {% for opt in opts %}
                      <option value="{{ opt }}">{{ opt }}</option>
                    {% endfor %}
                  </select>

                  <div class="form-text">
                    Importance (1–10):
                    <input type="number" min="1" max="10" name="w_{{ key }}" value="5" class="form-control weight">
                  </div>
                </div>
              {% endfor %}

              <button class="btn btn-primary mt-2">Add User</button>
              <a href="{{ url_for('matches') }}" class="btn btn-secondary mt-2">View Matches</a>

            </form>
          </div>
        </div>

        <form action="{{ url_for('clear_users') }}" method="post">
          <button class="btn btn-warning">Clear All Users</button>
          <a class="btn btn-success" href="{{ url_for('export_users') }}">Export CSV</a>
        </form>

      </div>

      <!-- RIGHT: CURRENT USERS -->
      <div class="col-md-6">
        <h4>Current Users ({{ users|length }})</h4>

        {% if not users %}
          <p>No users yet.</p>
        {% else %}
          {% for u in users %}
            <div class="card mb-2">
              <div class="card-body">
                <strong>{{ u.name }}</strong>
                <br>
                <small>Added: {{ u.created }}</small>
                <br>
                <small><b>Mode:</b> {{ u.match_mode }}
                  {% if u.match_mode == 'single' %}
                    ({{ u.match_key.replace('_',' ').title() }})
                  {% endif %}
                </small>

                <div class="mt-2">
                  {% for k in questions %}
                    <span class="badge text-bg-light">{{ k.replace('_',' ').title() }}: {{ u[k] }}</span>
                  {% endfor %}
                </div>

              </div>
            </div>
          {% endfor %}
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
  </head>

  <body class="container">

    <h1 class="my-3">🔗 Compatibility Matches</h1>
    <a href="{{ url_for('index') }}">&larr; Back</a>

    {% if not pairs %}
      <p>No pairs found.</p>
    {% else %}
      <table class="table table-bordered table-striped mt-3">
        <thead>
          <tr>
            <th>Rank</th>
            <th>User A</th>
            <th>User B</th>
            <th>Score</th>
          </tr>
        </thead>

        <tbody>
          {% for p in pairs %}
            <tr>
              <td>{{ loop.index }}</td>
              <td>{{ p.a }}</td>
              <td>{{ p.b }}</td>
              <td><strong>{{ "%.2f"|format(p.score) }}</strong></td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% endif %}

  </body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)




