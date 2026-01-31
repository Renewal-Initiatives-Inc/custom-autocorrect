"""Generate icons for Custom Autocorrect.

Run this script to generate both PNG and ICO icons:
    python resources/create_icon.py

Creates:
- icon.png: 64x64 PNG for system tray
- icon.ico: Multi-size ICO for Windows executable
"""

import math
from PIL import Image, ImageDraw


def create_icon_image(size: int = 64) -> Image.Image:
    """Create a pillow-shaped icon image.

    Args:
        size: Icon size in pixels.

    Returns:
        PIL Image object.
    """
    # Create a new image with a soft blue background
    img = Image.new("RGBA", (size, size), (52, 152, 219, 255))  # Nice blue
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    margin = size // 8
    pillow_width = size - 2 * margin

    # Pillow body (soft rectangle with rounded appearance)
    pillow_left = margin
    pillow_right = size - margin
    pillow_top = margin + size // 8
    pillow_bottom = size - margin - size // 12

    # Draw pillow body as a rounded rectangle
    corner_radius = size // 6

    # Draw the main pillow body (white/cream colored)
    pillow_color = (255, 250, 240, 255)  # Cream white

    draw.rounded_rectangle(
        [(pillow_left, pillow_top), (pillow_right, pillow_bottom)],
        radius=corner_radius,
        fill=pillow_color,
        outline=(200, 195, 185, 255),  # Subtle outline
        width=1,
    )

    # Add pillow "puffiness" - a curved line in the middle
    mid_y = (pillow_top + pillow_bottom) // 2
    curve_points = []
    for i in range(pillow_left + corner_radius, pillow_right - corner_radius + 1, 2):
        offset = int(math.sin((i - pillow_left) / pillow_width * math.pi) * 3)
        curve_points.append((i, mid_y + offset))

    if len(curve_points) >= 2:
        draw.line(curve_points, fill=(220, 215, 205, 255), width=1)

    # Add corner tufts/ruffles
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

    # Add small "z"s for sleep motif
    z_x = size - margin - size // 6
    z_y = margin + size // 16
    z_size = size // 10
    z_color = (255, 255, 255, 200)
    draw.text((z_x, z_y), "z", fill=z_color)
    draw.text((z_x + z_size // 2, z_y - z_size // 3), "z", fill=z_color)

    return img


def create_png(output_path: str, size: int = 64) -> None:
    """Create and save a PNG icon.

    Args:
        output_path: Where to save the icon.
        size: Icon size in pixels.
    """
    img = create_icon_image(size)
    img.save(output_path, "PNG")
    print(f"PNG icon saved to {output_path}")


def create_ico(output_path: str) -> None:
    """Create and save a Windows ICO file with multiple sizes.

    Windows .ico files should contain multiple sizes for different contexts:
    - 16x16: small icons in lists
    - 32x32: standard toolbar/taskbar
    - 48x48: large icons
    - 64x64: extra large icons
    - 256x256: high-DPI displays

    Args:
        output_path: Where to save the .ico file.
    """
    sizes = [16, 32, 48, 64, 256]
    images = []

    for size in sizes:
        img = create_icon_image(size)
        images.append(img)

    # Save as ICO with all sizes
    # The first image is used as the base, others are appended
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"ICO icon saved to {output_path} (sizes: {sizes})")


if __name__ == "__main__":
    import os

    # Save in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create PNG (for tray icon)
    png_path = os.path.join(script_dir, "icon.png")
    create_png(png_path)

    # Create ICO (for Windows executable)
    ico_path = os.path.join(script_dir, "icon.ico")
    create_ico(ico_path)
