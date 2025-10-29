<!-- templates/preview.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview Daily Log</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        h2 { border-bottom: 2px solid #ccc; padding-bottom: 5px; }
        img.thumbnail { max-height: 150px; cursor: pointer; margin-right: 10px; }
        .ai-section, .photo-section, .safety-section { margin-top: 2rem; }
        .slider-container { display: flex; align-items: center; margin: 10px 0; }
        .slider-container input[type="range"] { margin: 0 10px; }
        .slider-label { width: 60px; text-align: right; }
        .generate-btn { margin-top: 2rem; }
    </style>
    <script>
        function updateSliderValue(id, value) {
            document.getElementById('slider-value-' + id).innerText = value + '%';
            calculateOverallCompletion();
        }

        function calculateOverallCompletion() {
            const sliders = document.querySelectorAll("input[type='range']");
            let total = 0;
            sliders.forEach(slider => {
                total += parseInt(slider.value);
            });
            const average = sliders.length > 0 ? Math.round(total / sliders.length) : 0;
            document.getElementById('overall-completion').innerText = average + '%';
        }

        window.onload = calculateOverallCompletion;
    </script>
</head>
<body>
    <h1>Preview Your Daily Log</h1>

    <h2>Project Info</h2>
    <p><strong>Project Name:</strong> {{ data.project_name }}</p>
    <p><strong>Client:</strong> {{ data.client_name }}</p>
    <p><strong>Location:</strong> {{ data.project_location }}</p>
    <p><strong>Date:</strong> {{ data.date }}</p>

    <h2>Work Notes</h2>
    <p><strong>Crew Notes:</strong> {{ data.crew_notes }}</p>
    <p><strong>Work Performed:</strong> {{ data.work_done }}</p>
    <p><strong>Safety Notes:</strong> {{ data.safety_notes }}</p>

    <div class="photo-section">
        <h2>Jobsite Photos</h2>
        {% for i, image_url in enumerate(image_urls) %}
            <a href="{{ image_url }}" target="_blank">
                <img src="{{ image_url }}" class="thumbnail">
            </a>
        {% endfor %}
    </div>

    <div class="ai-section">
        <h2>AI Scope Comparison</h2>
        <p><strong>Estimated Completion:</strong> <span id="overall-completion">0%</span></p>

        <p><strong>Scope of Work (Keywords, Not Exact):</strong></p>
        <p>{{ ai_results.scope_summary }}</p>

        {% for i, item in enumerate(ai_results.scored_items) %}
        <div class="slider-container">
            <span>{{ item.text }}</span>
            <input type="range" min="0" max="100" value="{{ item.score }}" name="slider_{{ i }}" id="slider_{{ i }}" onchange="updateSliderValue('{{ i }}', this.value)">
            <span class="slider-label" id="slider-value-{{ i }}">{{ item.score }}%</span>
        </div>
        {% endfor %}

        <p><strong>Out of Scope Items (Review):</strong></p>
        <ul>
        {% for item in ai_results.out_of_scope %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    </div>

    <div class="safety-section">
        <h2>Safety Sheet</h2>
        {% if safety_sheet_url %}
            <a href="{{ safety_sheet_url }}" target="_blank">
                <img src="{{ safety_sheet_url }}" class="thumbnail">
            </a>
        {% else %}
            <p>No safety sheet uploaded.</p>
        {% endif %}
    </div>

    <form action="/generate_pdf/{{ session_id }}" method="post">
        <div class="generate-btn">
            <button type="submit">Generate Final PDF</button>
        </div>
    </form>
</body>
</html>
