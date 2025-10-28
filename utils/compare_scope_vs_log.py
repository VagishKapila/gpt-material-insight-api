def analyze_scope_vs_log(scope_items, daily_log_data, threshold=0.65):
    """
    Compares log entries against scope using sentence embeddings + fuzzy matching.
    Ensures all embeddings are 2D arrays for cosine similarity.
    """
    work_done = daily_log_data.get("work_done", "")
    crew_notes = daily_log_data.get("crew_notes", "")
    safety_notes = daily_log_data.get("safety_notes", "")
    full_log = f"{work_done}\n{crew_notes}\n{safety_notes}".strip()

    if not scope_items or not full_log:
        return {
            "completion": 0,
            "scored_items": [],
            "out_of_scope": ["⚠️ Missing scope items or log data."]
        }

    # ✅ Make sure both log_embedding and scope_embed are 2D
    log_embedding = model.encode([full_log])  # Shape: [1, 384]
    scope_embeddings = model.encode(scope_items)  # Shape: [N, 384]

    matched = 0
    scored_items = []

    for item, scope_embed in zip(scope_items, scope_embeddings):
        # ✅ Ensure scope_embed is also reshaped to 2D
        scope_embed_2d = scope_embed.reshape(1, -1)  # Shape: [1, 384]

        cosine_score = cosine_similarity(scope_embed_2d, log_embedding)[0][0]
        fuzzy_score = fuzz.partial_ratio(item.lower(), full_log.lower()) / 100
        final_score = max(cosine_score, fuzzy_score)
        is_match = final_score >= threshold

        if is_match:
            matched += 1

        scored_items.append({
            "scope": item,
            "confidence": round(final_score * 100, 1),
            "match": is_match
        })

    # 🔎 Out-of-Scope Detection (lines not matching any scope item)
    known_ignore = ["ppe", "tailgate", "safety", "meeting"]
    log_lines = [line.strip() for line in full_log.split("\n") if line.strip()]
    out_of_scope = []
    for line in log_lines:
        if any(kw in line.lower() for kw in known_ignore):
            continue
        if all(fuzz.partial_ratio(line.lower(), item.lower()) < 60 for item in scope_items):
            out_of_scope.append(line)

    percent_complete = round((matched / len(scope_items)) * 100, 1) if scope_items else 0

    return {
        "completion": percent_complete,
        "scored_items": scored_items,
        "out_of_scope": out_of_scope[:10]
    }
