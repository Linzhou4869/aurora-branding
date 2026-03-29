"""
Frame Composer Module

Helper functions for creating and composing animation frames.
"""

from PIL import Image, ImageDraw
from typing import Tuple, Optional


def create_blank_frame(width: int, height: int, color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """
    Create a blank frame with solid color background.
    
    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        color: RGB color tuple
        
    Returns:
        PIL Image object
    """
    return Image.new('RGB', (width, height), color)


def create_gradient_background(width: int, height: int, 
                                color1: Tuple[int, int, int], 
                                color2: Tuple[int, int, int],
                                direction: str = 'vertical') -> Image.Image:
    """
    Create a gradient background.
    
    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        color1: Starting RGB color
        color2: Ending RGB color
        direction: 'vertical' or 'horizontal'
        
    Returns:
        PIL Image object with gradient
    """
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    if direction == 'vertical':
        for y in range(height):
            # Calculate interpolation factor
            t = y / height
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    else:  # horizontal
        for x in range(width):
            t = x / width
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    return img


def draw_circle(draw: ImageDraw.Draw, center: Tuple[int, int], radius: int,
                fill: Optional[Tuple[int, int, int]] = None,
                outline: Optional[Tuple[int, int, int]] = None,
                width: int = 1) -> None:
    """
    Draw a circle.
    
    Args:
        draw: ImageDraw object
        center: (x, y) center coordinates
        radius: Circle radius
        fill: Fill color (RGB tuple or None)
        outline: Outline color (RGB tuple or None)
        width: Outline width
    """
    x, y = center
    draw.ellipse(
        [x - radius, y - radius, x + radius, y + radius],
        fill=fill,
        outline=outline,
        width=width
    )


def draw_star(draw: ImageDraw.Draw, center: Tuple[int, int], size: int,
              fill: Optional[Tuple[int, int, int]] = None,
              outline: Optional[Tuple[int, int, int]] = None,
              width: int = 1,
              points: int = 5) -> None:
    """
    Draw a star polygon.
    
    Args:
        draw: ImageDraw object
        center: (x, y) center coordinates
        size: Outer radius of star
        fill: Fill color
        outline: Outline color
        width: Outline width
        points: Number of points (default 5)
    """
    import math
    
    cx, cy = center
    vertices = []
    
    # Generate star points
    for i in range(points * 2):
        angle = math.pi / 2 + i * math.pi / points
        r = size if i % 2 == 0 else size / 2
        
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        vertices.append((x, y))
    
    draw.polygon(vertices, fill=fill, outline=outline, width=width)


def draw_text(draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
              fill: Tuple[int, int, int] = (255, 255, 255),
              font_size: int = 16,
              bold: bool = False) -> None:
    """
    Draw text on a frame.
    
    Args:
        draw: ImageDraw object
        text: Text to draw
        position: (x, y) position
        fill: Text color
        font_size: Font size in points
        bold: Whether to use bold font
    """
    try:
        from PIL import ImageFont
        font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_name}", font_size)
    except:
        from PIL import ImageFont
        font = ImageFont.load_default()
    
    draw.text(position, text, fill=fill, font=font)


def draw_text_centered(draw: ImageDraw.Draw, text: str, y: int,
                       fill: Tuple[int, int, int] = (255, 255, 255),
                       font_size: int = 16,
                       bold: bool = False) -> None:
    """
    Draw centered text horizontally.
    
    Args:
        draw: ImageDraw object
        text: Text to draw
        y: Y position
        fill: Text color
        font_size: Font size
        bold: Whether to use bold font
    """
    try:
        from PIL import ImageFont
        font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_name}", font_size)
    except:
        from PIL import ImageFont
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    width = draw.im.size[0]
    x = (width - text_width) // 2
    draw.text((x, y), text, fill=fill, font=font)


def draw_rect(draw: ImageDraw.Draw, coords: Tuple[int, int, int, int],
              fill: Optional[Tuple[int, int, int]] = None,
              outline: Optional[Tuple[int, int, int]] = None,
              width: int = 1,
              radius: int = 0) -> None:
    """
    Draw a rectangle, optionally with rounded corners.
    
    Args:
        draw: ImageDraw object
        coords: (x1, y1, x2, y2) coordinates
        fill: Fill color
        outline: Outline color
        width: Outline width
        radius: Corner radius (0 for square corners)
    """
    if radius > 0:
        draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rectangle(coords, fill=fill, outline=outline, width=width)


def draw_line(draw: ImageDraw.Draw, start: Tuple[int, int], end: Tuple[int, int],
              fill: Tuple[int, int, int], width: int = 1) -> None:
    """
    Draw a line.
    
    Args:
        draw: ImageDraw object
        start: (x1, y1) start coordinates
        end: (x2, y2) end coordinates
        fill: Line color
        width: Line width
    """
    draw.line([start, end], fill=fill, width=width)


def draw_polygon(draw: ImageDraw.Draw, points: list,
                 fill: Optional[Tuple[int, int, int]] = None,
                 outline: Optional[Tuple[int, int, int]] = None,
                 width: int = 1) -> None:
    """
    Draw a polygon.
    
    Args:
        draw: ImageDraw object
        points: List of (x, y) coordinates
        fill: Fill color
        outline: Outline color
        width: Outline width
    """
    draw.polygon(points, fill=fill, outline=outline, width=width)
