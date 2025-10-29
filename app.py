<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Preview Daily Log</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        img.thumbnail { height: 100px; margin: 5px; cursor: pointer; }
        .section { margin-bottom: 2rem; }
        .slider-label { display: flex; justify-content: space-between; align-items: center; }
        .slider-input { width: 100%; }
        .bar-container { background: #f0f0f0; border-radius: 4px; margin-top: 4px; }
        .bar { height: 10px; background-color: #4caf50; border-radius: 4px; }
        .scope-item { margin-bottom: 1rem; }
    </style>
    <script>
        function enlarge(imgSrc) {
            const win = window.open();
            win.document.write('<img src="' + imgSrc + '" style="width:100%">');
        }
        function updateTotal() {
            const sliders = document.querySelectorAll('.scope-slider');
            let sum = 0;
            sliders.forEach(s => sum += parseFloat(s.value));
            const avg = (sliders.length ? sum / sliders.length : 0).toFixed(1);
            document.getElementById('completion-total').innerText = avg + '%';
        }
    </script>
</head>
<body>
    <h2>Preview Your Daily Log</h2>
    <div class="section">
        <h3>Project Info</h3>
        <p><strong>Project Name:</strong> {{ data.project_name }}</p>
        <p><strong>Location:</strong> {{ data.location }}</p>
        <p><strong>Date:</strong> {{ data.date }}</p>
        <p><strong>General Contractor:</strong> {{ data.contractor }}</p>
        <p><strong>Weather:</strong> {{ data.weather }}</p>
    </div>

    <div class="section">
        <h3>Work Notes</h3>
        <p><strong>Work Performed:</strong> {{ data.work_done }}</p>
        <p><strong>Crew Notes:</strong> {{ data.crew_notes }}</p>
        <p><strong>Safety Notes:</strong> {{ data.safety_notes }}</p>
    </div>

    <div class="section">
        <h3>Jobsite Photos</h3>
        {% if image_paths %}
            {% for img in image_paths %}
                <img src="{{ url_for('static', filename='uploads/' + img) }}" class="thumbnail" onclick="enlarge(this.src)" />
            {% endfor %}
        {% else %}
            <p>No photos uploaded.</p>
        {% endif %}
    </div>

    <div class="section">
        <h3>AI Scope Comparison</h3>
        {% if ai_analysis %}
            <p><strong>Estimated Completion:</strong> <span id="completion-total">{{ ai_analysis.completion }}%</span></p>
            <div class="bar-container">
                <div class="bar" style="width: {{ ai_analysis.completion }}%"></div>
            </div>
            <p><strong>Scope of Work Interpretation:</strong> {{ ai_analysis.scope_summary }}</p>
            {% for item in ai_analysis.scored_items %}
                <div class="scope-item">
                    <div class="slider-label">
                        <span><strong>{{ item.section }}:</strong> {{ item.item }}</span>
                        <span>{{ item.score }}%</span>
                    </div>
                    <input type="range" min="0" max="100" value="{{ item.score }}" class="slider-input scope-slider" oninput="updateTotal()" />
                </div>
            {% endfor %}

            {% if ai_analysis.out_of_scope %}
                <h4>🔧 Flagged Items (Not in Original Scope)</h4>
                <ul>
                    {% for line in ai_analysis.out_of_scope %}
                        <li>{{ line }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        {% else %}
            <p>No AI analysis available.</p>
        {% endif %}
    </div>

    <div class="section">
        <h3>Safety Sheet</h3>
        {% if safety_sheet_path %}
            <img src="{{ url_for('static', filename='uploads/' + safety_sheet_path) }}" class="thumbnail" onclick="enlarge(this.src)" />
        {% else %}
            <p>No safety sheet uploaded.</p>
        {% endif %}
    </div>

    <form action="/generate_pdf" method="POST">
        <input type="hidden" name="session_id" value="{{ session_id }}">
        <button type="submit">Generate Final PDF</button>
    </form>
</body>
</html>
