@app.route("/submit", methods=["POST"])
def submit_log():
    try:
        form = request.form
        files = request.files.getlist("photos")
        logo_file = request.files.get("logo")

        saved_files = []
        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(filepath)
                saved_files.append(filepath)

        logo_path = None
        if logo_file and logo_file.filename:
            logo_name = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_name)
            logo_file.save(logo_path)

        # Determine weather (either auto or override)
        weather = form.get("weather_override") or form.get("weather")

        data = {
            "date": form.get("date"),
            "project_name": form.get("project_name"),
            "client_name": form.get("client_name"),
            "job_number": form.get("job_number"),
            "prepared_by": form.get("prepared_by"),
            "location": form.get("location"),
            "gc_or_sub": form.get("gc_or_sub"),
            "crew_notes": form.get("crew_notes"),
            "work_done": form.get("work_done"),
            "deliveries": form.get("deliveries"),
            "inspections": form.get("inspections"),
            "equipment_used": form.get("equipment_used"),
            "safety_notes": form.get("safety_notes"),
            "weather": weather,
            "notes": form.get("notes")
        }

        include_page_2 = "include_page_2" in form

        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, "Daily_Log.pdf")

        # ✅ Now call the full 5-argument version
        create_daily_log_pdf(data, output_path, saved_files, logo_path, include_page_2)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print(f"[Server Error] {e}")
        return "Error occurred while submitting the log.", 500
