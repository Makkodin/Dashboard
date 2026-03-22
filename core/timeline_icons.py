import base64


def icon_svg(icon_type: str, color: str) -> str:
    if icon_type == "progression":
        return f"""
        <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="11" fill="white" stroke="{color}" stroke-width="2"/>
            <path d="M12 6.5V13.5" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>
            <circle cx="12" cy="17.2" r="1.5" fill="{color}"/>
        </svg>
        """

    if icon_type == "immunotherapy":
        return f"""
        <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="11" fill="white" stroke="{color}" stroke-width="2"/>
            <path d="M8 15L15.5 7.5" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
            <path d="M14.2 8.8L16.8 11.4" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
            <path d="M6.8 16.2L9.8 17.2L7.8 19.2L6.8 16.2Z" fill="{color}"/>
        </svg>
        """

    return f"""
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="11" fill="white" stroke="{color}" stroke-width="2"/>
        <path d="M12 7V17" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>
        <path d="M7 12H17" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>
    </svg>
    """


def resolve_timeline_icon(stage_name: str) -> str:
    s = stage_name.strip().lower()

    if "прогресс" in s:
        return "progression"

    if "+ ит" in s or "иммунотерап" in s or "anti-pd1" in s or "анти-pd1" in s:
        return "immunotherapy"

    return "treatment"


def svg_to_data_uri(svg_text: str) -> str:
    svg_bytes = svg_text.encode("utf-8")
    b64 = base64.b64encode(svg_bytes).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"