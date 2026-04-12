import base64


def icon_svg(icon_type: str, color: str) -> str:
    if icon_type == "progression":
        return f"""
        <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
            <circle cx="15" cy="15" r="13" fill="white" stroke="{color}" stroke-width="2.2"/>
            <path d="M15 8.5V17" stroke="{color}" stroke-width="2.6" stroke-linecap="round"/>
            <circle cx="15" cy="21.5" r="1.9" fill="{color}"/>
        </svg>
        """

    if icon_type == "immunotherapy":
        return f"""
        <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
            <circle cx="15" cy="15" r="13" fill="white" stroke="{color}" stroke-width="2.2"/>
            <path d="M10 19L19.5 9.5" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>
            <path d="M17.8 10.8L21 14" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>
            <path d="M8.6 20.4L12.3 21.7L9.8 24.2L8.6 20.4Z" fill="{color}"/>
        </svg>
        """

    if icon_type == "surgery":
        return f"""
        <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
            <circle cx="15" cy="15" r="13" fill="white" stroke="{color}" stroke-width="2.2"/>
            <path d="M10 10L20 20" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>
            <path d="M20 10L10 20" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>
            <circle cx="10" cy="10" r="1.5" fill="{color}"/>
            <circle cx="20" cy="20" r="1.5" fill="{color}"/>
        </svg>
        """

    return f"""
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
        <circle cx="15" cy="15" r="13" fill="white" stroke="{color}" stroke-width="2.2"/>
        <path d="M15 9V21" stroke="{color}" stroke-width="2.6" stroke-linecap="round"/>
        <path d="M9 15H21" stroke="{color}" stroke-width="2.6" stroke-linecap="round"/>
    </svg>
    """


def resolve_timeline_icon(stage_name: str) -> str:
    s = stage_name.strip().lower()

    if "прогресс" in s:
        return "progression"

    if "хирург" in s or "операц" in s or "резекц" in s:
        return "surgery"

    if "+ ит" in s or "иммунотерап" in s or "anti-pd1" in s or "анти-pd1" in s:
        return "immunotherapy"

    return "treatment"


def svg_to_data_uri(svg_text: str) -> str:
    svg_bytes = svg_text.encode("utf-8")
    b64 = base64.b64encode(svg_bytes).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"
