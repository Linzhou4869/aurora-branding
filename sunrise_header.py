#!/usr/bin/env python3
"""
Generate serene sunrise over calm tropical ocean
High-resolution header image for internal resort report
"""

from PIL import Image, ImageDraw, ImageFilter
import math

def create_sunrise_header(width=1920, height=600):
    """Create a serene tropical sunrise scene."""
    
    # Create image with gradient sky
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Color palette - serene tropical sunrise
    colors = {
        'sky_top': (15, 25, 45),        # Deep twilight blue
        'sky_mid': (85, 115, 145),      # Soft dawn blue
        'horizon_glow': (255, 180, 120), # Warm orange glow
        'sun_core': (255, 220, 180),    # Bright sun center
        'sun_outer': (255, 160, 100),   # Sun halo
        'ocean_deep': (20, 50, 80),     # Deep ocean
        'ocean_mid': (45, 90, 130),     # Mid ocean
        'ocean_shimmer': (255, 200, 150) # Sun reflection
    }
    
    # Draw sky gradient (top to horizon)
    horizon_y = height // 2
    for y in range(horizon_y):
        ratio = y / horizon_y
        r = int(colors['sky_top'][0] + (colors['horizon_glow'][0] - colors['sky_top'][0]) * ratio)
        g = int(colors['sky_top'][1] + (colors['horizon_glow'][1] - colors['sky_top'][1]) * ratio)
        b = int(colors['sky_top'][2] + (colors['horizon_glow'][2] - colors['sky_top'][2]) * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Draw sun (partially above horizon)
    sun_x = width // 2
    sun_y = horizon_y - 20
    sun_radius = 60
    
    # Sun glow (outer)
    for r in range(sun_radius + 40, sun_radius, -3):
        alpha = int(80 * (1 - (r - sun_radius) / 40))
        sun_color = (*colors['sun_outer'], alpha)
        draw.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=colors['sun_outer'])
    
    # Sun core
    draw.ellipse([sun_x - sun_radius, sun_y - sun_radius, 
                  sun_x + sun_radius, sun_y + sun_radius], 
                 fill=colors['sun_core'])
    
    # Draw ocean with gradient and gentle waves
    for y in range(horizon_y, height):
        ocean_ratio = (y - horizon_y) / (height - horizon_y)
        r = int(colors['horizon_glow'][0] * 0.3 + colors['ocean_deep'][0] * ocean_ratio)
        g = int(colors['horizon_glow'][1] * 0.3 + colors['ocean_deep'][1] * ocean_ratio)
        b = int(colors['horizon_glow'][2] * 0.3 + colors['ocean_deep'][2] * ocean_ratio)
        
        # Add subtle wave variation
        wave_offset = math.sin(y * 0.05) * 3
        r = max(0, min(255, r + int(wave_offset)))
        
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Add sun reflection on water (shimmer path)
    for i in range(80):
        reflect_y = horizon_y + i * 3
        reflect_width = max(20, 150 - i * 1.5)
        alpha = int(60 * (1 - i / 80))
        shimmer_x = sun_x - int(reflect_width / 2)
        
        # Gentle wave distortion
        wave_x = int(math.sin(i * 0.1) * 20)
        
        for j in range(5):
            shimmer_y = reflect_y + j * 2
            if shimmer_y < height:
                draw.rectangle([
                    (shimmer_x + wave_x - j * 3, shimmer_y),
                    (shimmer_x + reflect_width + wave_x + j * 3, shimmer_y + 1)
                ], fill=(255, 220, 180))
    
    # Add subtle clouds (wispy, minimal)
    cloud_positions = [
        (width * 0.2, horizon_y - 100, 80, 25),
        (width * 0.75, horizon_y - 80, 100, 30),
        (width * 0.5, horizon_y - 150, 120, 35),
    ]
    
    for cx, cy, cw, ch in cloud_positions:
        # Soft white clouds with transparency effect
        for offset in range(5):
            cloud_color = (255 - offset * 10, 255 - offset * 10, 255 - offset * 10)
            draw.ellipse([
                (cx - cw//2 + offset * 3, cy - ch//2 + offset * 2),
                (cx + cw//2 + offset * 3, cy + ch//2 + offset * 2)
            ], fill=cloud_color)
    
    # Apply subtle blur for dreamy atmosphere
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Sharpen slightly to maintain definition
    img = img.filter(ImageFilter.SHARPEN)
    
    return img

if __name__ == "__main__":
    print("Generating serene tropical sunrise header image...")
    
    # Create high-resolution image
    img = create_sunrise_header(width=1920, height=600)
    
    # Save to workspace
    output_path = 'sunrise_ocean_header.png'
    img.save(output_path, 'PNG', quality=95, dpi=(300, 300))
    
    print(f"✓ Header image saved: {output_path}")
    print(f"  Resolution: 1920x600 pixels (300 DPI)")
    print(f"  Format: PNG (high-quality)")
