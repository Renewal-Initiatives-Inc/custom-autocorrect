"""Generate a pillow icon for the system tray.

Run this script once on Windows after installing dependencies:
    python resources/create_icon.py

This creates a 64x64 PNG icon with a pillow design (a play on PIL/Pillow).
"""

from PIL import Image, ImageDraw


def create_icon(output_path: str = "icon.png", size: int = 64) -> None:
    """Create a pillow-shaped tray icon.

    Args:
        output_path: Where to save the icon.
        size: Icon size in pixels.
    """
    # Create a new image with a soft blue background
    img = Image.new("RGBA", (size, size), (52, 152, 219, 255))  # Nice blue
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    margin = size // 8
    pillow_width = size - 2 * margin
    pillow_height = size - 2 * margin

    # Pillow body (soft rectangle with rounded appearance)
    # Main pillow shape - a puffy rectangle
    pillow_left = margin
    pillow_right = size - margin
    pillow_top = margin + size // 8
    pillow_bottom = size - margin - size // 12

    # Draw pillow body as a rounded rectangle
    # Using ellipses at corners for rounded effect
    corner_radius = size // 6

    # Draw the main pillow body (white/cream colored)
    pillow_color = (255, 250, 240, 255)  # Cream white

    # Draw rounded rectangle for pillow
    draw.rounded_rectangle(
        [(pillow_left, pillow_top), (pillow_right, pillow_bottom)],
        radius=corner_radius,
        fill=pillow_color,
        outline=(200, 195, 185, 255),  # Subtle outline
        width=1,
    )

    # Add pillow "puffiness" - a curved line in the middle to show it's stuffed
    mid_y = (pillow_top + pillow_bottom) // 2
    # Draw a subtle curve to show pillow stuffing
    curve_points = []
    for i in range(pillow_left + corner_radius, pillow_right - corner_radius + 1, 2):
        # Gentle sine wave for puffiness
        import math

        offset = int(math.sin((i - pillow_left) / (pillow_width) * math.pi) * 3)
        curve_points.append((i, mid_y + offset))

    if len(curve_points) >= 2:
        draw.line(curve_points, fill=(220, 215, 205, 255), width=1)

    # Add corner tufts/ruffles (little decorative marks at corners)
    tuft_color = (230, 225, 215, 255)
    tuft_size = size // 16

    # Top-left tuft
    draw.arc(
        [
            (pillow_left - tuft_size // 2, pillow_top - tuft_size // 2),
            (pillow_left + tuft_size, pillow_top + tuft_size),
        ],
        start=0,
        end=90,
        fill=tuft_color,
        width=2,
    )

    # Top-right tuft
    draw.arc(
        [
            (pillow_right - tuft_size, pillow_top - tuft_size // 2),
            (pillow_right + tuft_size // 2, pillow_top + tuft_size),
        ],
        start=90,
        end=180,
        fill=tuft_color,
        width=2,
    )

    # Add a small "Z" or "zzz" to suggest sleep/comfort (optional cute touch)
    z_x = size - margin - size // 6
    z_y = margin + size // 16
    z_size = size // 10

    # Draw small z's
    z_color = (255, 255, 255, 200)
    draw.text((z_x, z_y), "z", fill=z_color)
    draw.text((z_x + z_size // 2, z_y - z_size // 3), "z", fill=z_color)

    # Save the icon
    img.save(output_path, "PNG")
    print(f"Pillow icon saved to {output_path}")


if __name__ == "__main__":
    import os

    # Save in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "icon.png")
    create_icon(icon_path)
