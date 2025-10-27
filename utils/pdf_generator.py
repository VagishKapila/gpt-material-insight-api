# --- AI Scope Analysis ---
if ai_analysis:
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
    completion = ai_analysis.get("completion", 0)

    # -- Visual Completion Bar --
    try:
        drawing = Drawing(200, 20)
        percent_width = 2 * completion  # scale to 200px max
        drawing.add(Rect(0, 0, 200, 20, fillColor=colors.lightgrey))
        drawing.add(Rect(0, 0, percent_width, 20, fillColor=colors.green))
        elements.append(drawing)
        elements.append(Paragraph(f"<b>Completion:</b> {completion:.1f}%", styles["Normal"]))
    except Exception:
        elements.append(Paragraph(f"<b>Completion:</b> {completion:.1f}%", styles["Normal"]))

    elements.append(Spacer(1, 8))

    # -- Scored Items Table --
    scored = ai_analysis.get("scored_items", [])
    if scored:
        table_data = [["Scope Item", "Confidence %", "Match"]]
        for s in scored:
            item = s.get("scope", "N/A")
            confidence = s.get("confidence", 0.0)
            is_match = s.get("match", False)
            table_data.append([
                item[:75] + ("..." if len(item) > 75 else ""),
                f"{confidence:.1f}%",
                "✅" if is_match else "❌"
            ])
        table = Table(table_data, repeatRows=1, colWidths=[300, 80, 40])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    # -- Out-of-Scope Items --
    oos = ai_analysis.get("out_of_scope", [])
    if oos:
        elements.append(Paragraph("<b>Out-of-Scope Items:</b>", styles["Heading3"]))
        for line in oos:
            elements.append(Paragraph(f"• {line}", styles["Normal"]))
        elements.append(Spacer(1, 12))
