"""Generate a simple placeholder icon for the system tray.

Run this script once on Windows after installing dependencies:
    python resources/create_icon.py

This creates a 64x64 PNG icon with a simple "A" letter design.
"""

from PIL import Image, ImageDraw, ImageFont


def create_icon(output_path: str = "icon.png", size: int = 64) -> None:
    """Create a simple tray icon.

    Args:
        output_path: Where to save the icon.
        size: Icon size in pixels.
    """
    # Create a new image with a blue background
    img = Image.new("RGBA", (size, size), (52, 152, 219, 255))  # Nice blue
    draw = ImageDraw.Draw(img)

    # Draw a white "A" in the center (for Autocorrect)
    # Use default font since we don't want to depend on specific fonts
    try:
        # Try to use a larger built-in font
        font = ImageFont.truetype("arial.ttf", size // 2)
    except OSError:
        # Fall back to default font
        font = ImageFont.load_default()

    text = "A"
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]  # Adjust for font baseline

    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Save the icon
    img.save(output_path, "PNG")
    print(f"Icon saved to {output_path}")


if __name__ == "__main__":
    import os

    # Save in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "icon.png")
    create_icon(icon_path)
