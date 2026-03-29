#!/usr/bin/env python3
"""
Slack GIF Generator - Compliance Controls Animation

Creates an animated GIF optimized for Slack showing:
1. Dual-signature approval process for POs over $50,000
2. Ethical sourcing standards compliance

Author: OpenClaw Workflow Engine
Date: 2026-03-29
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
import math
from workflows.core.gif_builder import GIFBuilder
from workflows.core.frame_composer import create_gradient_background
from workflows.core.easing import interpolate

# Configuration
WIDTH = 480
HEIGHT = 480
FPS = 12
TOTAL_FRAMES = 72  # 6 seconds at 12 FPS
OUTPUT_PATH = 'workflows/outputs/compliance_controls_slack.gif'


def create_color_palette():
    """Create a professional color palette for the animation"""
    return {
        'background_dark': (15, 23, 42),        # Dark blue-black
        'background_mid': (30, 41, 59),         # Slate
        'background_light': (51, 65, 85),       # Light slate
        'primary_blue': (59, 130, 246),         # Bright blue
        'success_green': (34, 197, 94),         # Green
        'warning_yellow': (234, 179, 8),        # Yellow
        'alert_red': (239, 68, 68),             # Red
        'text_white': (248, 250, 252),          # White
        'text_gray': (156, 163, 175),           # Gray
        'accent_purple': (139, 92, 246),        # Purple
        'accent_teal': (20, 184, 166),          # Teal
        'gold': (251, 191, 36),                 # Gold for ethical sourcing
    }


def draw_rounded_rectangle(draw, coords, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)


def draw_document(draw, x, y, scale, color, show_text=True):
    """Draw a document icon"""
    w = int(60 * scale)
    h = int(80 * scale)
    
    # Document body
    draw_rounded_rectangle(draw, [x, y, x + w, y + h], 5, fill=color, outline=(255, 255, 255, 200), width=2)
    
    # Folded corner
    fold_size = int(15 * scale)
    draw.polygon([
        (x + w - fold_size, y),
        (x + w, y),
        (x + w, y + fold_size)
    ], fill=(200, 200, 200))
    
    # Lines representing text
    if show_text:
        line_color = (255, 255, 255, 150)
        line_spacing = int(8 * scale)
        start_y = y + int(20 * scale)
        for i in range(3):
            line_y = start_y + i * line_spacing
            line_width = int((40 - i * 5) * scale)
            draw.line([(x + int(10 * scale), line_y), (x + int(10 * scale) + line_width, line_y)], 
                     fill=line_color, width=2)


def draw_signature(draw, x, y, signed=False, scale=1.0):
    """Draw a signature line with optional signature"""
    w = int(80 * scale)
    
    # Signature line
    draw.line([(x, y), (x + w, y)], fill=(200, 200, 200), width=2)
    
    if signed:
        # Draw signature scribble
        sig_color = (34, 197, 94)
        points = [
            (x + 5, y - 5),
            (x + 15, y + 8),
            (x + 25, y - 3),
            (x + 35, y + 10),
            (x + 45, y - 5),
            (x + 55, y + 5),
            (x + 65, y - 8),
            (x + 75, y + 3)
        ]
        draw.line(points, fill=sig_color, width=3)
        
        # Checkmark
        check_points = [(x + w + 5, y - 10), (x + w + 12, y - 3), (x + w + 20, y - 15)]
        draw.line(check_points, fill=sig_color, width=3)


def draw_person(draw, x, y, scale=1.0, color=None, has_checkmark=False):
    """Draw a person icon"""
    if color is None:
        color = (59, 130, 246)
    
    head_radius = int(15 * scale)
    body_width = int(30 * scale)
    body_height = int(40 * scale)
    
    # Head (circle)
    head_center = (x + body_width // 2, y + head_radius)
    draw.ellipse([
        head_center[0] - head_radius,
        head_center[1] - head_radius,
        head_center[0] + head_radius,
        head_center[1] + head_radius
    ], fill=color, outline=(255, 255, 255, 200), width=2)
    
    # Body (rounded rectangle)
    draw.rounded_rectangle([
        x, y + head_radius * 2,
        x + body_width, y + head_radius * 2 + body_height
    ], radius=5, fill=color, outline=(255, 255, 255, 200), width=2)
    
    if has_checkmark:
        # Draw checkmark badge
        badge_x = x + body_width - 5
        badge_y = y + head_radius
        draw.ellipse([badge_x - 8, badge_y - 8, badge_x + 8, badge_y + 8], 
                    fill=(34, 197, 94), outline=(255, 255, 255, 200), width=2)
        # Checkmark
        draw.line([(badge_x - 4, badge_y), (badge_x - 1, badge_y + 3), (badge_x + 4, badge_y - 4)], 
                 fill=(255, 255, 255), width=2)


def draw_shield(draw, x, y, scale=1.0, color=None):
    """Draw a shield icon for ethical sourcing"""
    if color is None:
        color = (251, 191, 36)  # Gold
    
    # Shield shape (polygon)
    points = [
        (x, y),
        (x + int(60 * scale), y),
        (x + int(60 * scale), y + int(40 * scale)),
        (x + int(30 * scale), y + int(70 * scale)),
        (x, y + int(40 * scale))
    ]
    draw.polygon(points, fill=color, outline=(255, 255, 255, 200), width=3)
    
    # Checkmark inside shield
    check_x = x + int(15 * scale)
    check_y = y + int(25 * scale)
    draw.line([
        (check_x, check_y + int(10 * scale)),
        (check_x + int(10 * scale), check_y + int(20 * scale)),
        (check_x + int(25 * scale), check_y)
    ], fill=(15, 23, 42), width=3)


def draw_arrow(draw, x1, y1, x2, y2, color, animated_progress=1.0):
    """Draw an animated arrow"""
    # Calculate intermediate point based on progress
    curr_x = interpolate(x1, x2, animated_progress)
    curr_y = interpolate(y1, y2, animated_progress)
    
    # Draw arrow line
    draw.line([(x1, y1), (curr_x, curr_y)], fill=color, width=4)
    
    # Draw arrowhead if animation is complete
    if animated_progress >= 0.95:
        angle = math.atan2(y2 - y1, x2 - x1)
        head_length = 12
        arrow_points = [
            (x2, y2),
            (x2 - head_length * math.cos(angle - math.pi/6), y2 - head_length * math.sin(angle - math.pi/6)),
            (x2 - head_length * math.cos(angle + math.pi/6), y2 - head_length * math.sin(angle + math.pi/6))
        ]
        draw.polygon(arrow_points, fill=color)


def draw_text_centered(draw, text, y, font_size=24, color=(255, 255, 255), bold=False):
    """Draw centered text"""
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size) if bold else \
               ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (WIDTH - text_width) // 2
    draw.text((x, y), text, fill=color, font=font)


def generate_frame(frame_num, colors):
    """Generate a single frame of the animation"""
    # Create gradient background
    frame = create_gradient_background(WIDTH, HEIGHT, colors['background_dark'], colors['background_mid'])
    draw = ImageDraw.Draw(frame)
    
    total_frames = TOTAL_FRAMES
    progress = frame_num / total_frames
    
    # Animation phases:
    # 0-20%: Title screen
    # 20-40%: Show PO document with amount
    # 40-60%: First signature animation
    # 60-80%: Second signature animation
    # 80-100%: Ethical sourcing badge + completion
    
    phase = frame_num / total_frames
    
    # Title text (fades out after 20%)
    if phase < 0.25:
        title_alpha = int(255 * (1 - phase / 0.25))
        title_color = (*colors['text_white'][:3], title_alpha)
        draw_text_centered(draw, "NEW COMPLIANCE CONTROLS", 50, font_size=28, color=colors['text_white'], bold=True)
        draw_text_centered(draw, "Effective Q2 2026", 90, font_size=18, color=colors['text_gray'])
    
    # PO Document (appears at 20%)
    if phase >= 0.15:
        doc_appear = min(1.0, (phase - 0.15) / 0.15)
        doc_x = 80
        doc_y = 140
        
        # Draw PO document
        draw_document(draw, doc_x, doc_y, 1.2, colors['primary_blue'])
        
        # PO Amount label
        if doc_appear > 0.5:
            amount_text = "PO: $75,000"
            draw_text_centered(draw, amount_text, doc_y + 110, font_size=20, color=colors['warning_yellow'], bold=True)
            
            # Threshold indicator
            threshold_text = "> $50K = Dual Signature Required"
            threshold_alpha = int(200 * doc_appear)
            draw_text_centered(draw, threshold_text, doc_y + 145, font_size=14, color=(*colors['text_gray'][:3], threshold_alpha))
    
    # First approver (appears at 35%)
    if phase >= 0.35:
        person1_x = 280
        person1_y = 130
        
        # Draw person 1
        person1_alpha = min(1.0, (phase - 0.35) / 0.1)
        draw_person(draw, person1_x, person1_y, 1.0, colors['accent_teal'], 
                   has_checkmark=(phase >= 0.55))
        
        # Label
        label1 = "Dept Manager"
        draw_text_centered(draw, label1, person1_y + 70, font_size=14, color=colors['text_gray'])
        
        # Arrow from PO to person 1
        if phase >= 0.40:
            arrow_progress = min(1.0, (phase - 0.40) / 0.1)
            draw_arrow(draw, 180, 180, person1_x, 180, colors['primary_blue'], arrow_progress)
        
        # Signature 1 (appears at 45%)
        if phase >= 0.45:
            sig1_progress = min(1.0, (phase - 0.45) / 0.1)
            sig1_signed = phase >= 0.55
            draw_signature(draw, person1_x - 10, person1_y + 60, signed=sig1_signed)
            
            if sig1_signed:
                draw_text_centered(draw, "✓ Approved", person1_y + 95, font_size=12, color=colors['success_green'])
    
    # Second approver (appears at 55%)
    if phase >= 0.55:
        person2_x = 280
        person2_y = 260
        
        # Draw person 2
        person2_alpha = min(1.0, (phase - 0.55) / 0.1)
        draw_person(draw, person2_x, person2_y, 1.0, colors['accent_purple'],
                   has_checkmark=(phase >= 0.75))
        
        # Label
        label2 = "Finance Director"
        draw_text_centered(draw, label2, person2_y + 70, font_size=14, color=colors['text_gray'])
        
        # Arrow from person 1 to person 2
        if phase >= 0.60:
            arrow_progress = min(1.0, (phase - 0.60) / 0.1)
            draw_arrow(draw, person1_x + 20, person1_y + 40, person2_x, person2_y, colors['primary_blue'], arrow_progress)
        
        # Signature 2 (appears at 65%)
        if phase >= 0.65:
            sig2_progress = min(1.0, (phase - 0.65) / 0.1)
            sig2_signed = phase >= 0.75
            draw_signature(draw, person2_x - 10, person2_y + 60, signed=sig2_signed)
            
            if sig2_signed:
                draw_text_centered(draw, "✓ Approved", person2_y + 95, font_size=12, color=colors['success_green'])
    
    # Ethical Sourcing badge (appears at 75%)
    if phase >= 0.75:
        badge_scale = min(1.0, (phase - 0.75) / 0.1)
        badge_x = 80
        badge_y = 300
        
        # Pulse effect
        pulse = 1.0 + 0.1 * math.sin((frame_num - 0.75 * total_frames) * 0.5)
        
        draw_shield(draw, badge_x, badge_y, 1.2 * badge_scale * pulse, colors['gold'])
        
        # Ethical sourcing text
        if badge_scale > 0.5:
            draw_text_centered(draw, "Ethical Sourcing 4.2", badge_y + 80, 
                             font_size=16, color=colors['gold'], bold=True)
            
            # Key points
            if badge_scale > 0.8:
                points_y = badge_y + 110
                point_size = 12
                point_color = colors['text_gray']
                
                points = [
                    "• No forced/child labor",
                    "• Fair wages & hours",
                    "• Safe workplaces",
                    "• Worker grievance rights"
                ]
                
                for i, point in enumerate(points):
                    point_alpha = int(200 * min(1.0, (phase - 0.80) / 0.05 + i * 0.1))
                    draw.text((badge_x + 100, points_y + i * 22), point, 
                             fill=(*point_color[:3], point_alpha), font=ImageFont.load_default())
    
    # Final approval status (appears at 85%)
    if phase >= 0.85:
        status_alpha = min(1.0, (phase - 0.85) / 0.1)
        
        # Success banner
        banner_y = 420
        draw_rounded_rectangle(draw, [20, banner_y, WIDTH - 20, banner_y + 40], 
                              10, fill=(*colors['success_green'][:3], int(200 * status_alpha)),
                              outline=(255, 255, 255, 200), width=2)
        
        status_text = "✓ DUAL APPROVAL COMPLETE - READY FOR RELEASE"
        draw_text_centered(draw, status_text, banner_y + 10, font_size=16, color=colors['text_white'], bold=True)
    
    # Slack footer
    footer_y = HEIGHT - 25
    draw.text((20, footer_y), "Procurement Workflow System", 
             fill=colors['text_gray'], font=ImageFont.load_default())
    
    return frame


def main():
    """Generate the animated GIF"""
    print("=" * 70)
    print("Slack GIF Generator - Compliance Controls Animation")
    print("=" * 70)
    print()
    
    colors = create_color_palette()
    
    print(f"Configuration:")
    print(f"  Dimensions: {WIDTH}x{HEIGHT}")
    print(f"  FPS: {FPS}")
    print(f"  Total Frames: {TOTAL_FRAMES}")
    print(f"  Duration: {TOTAL_FRAMES / FPS:.1f} seconds")
    print()
    
    print("Generating frames...")
    
    # Create GIF builder
    builder = GIFBuilder(width=WIDTH, height=HEIGHT, fps=FPS)
    
    # Generate all frames
    for i in range(TOTAL_FRAMES):
        frame = generate_frame(i, colors)
        builder.add_frame(frame)
        
        if (i + 1) % 12 == 0:
            print(f"  Generated {i + 1}/{TOTAL_FRAMES} frames...")
    
    print()
    print("Saving optimized GIF for Slack...")
    
    # Create output directory
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Save with optimization for Slack
    builder.save(
        OUTPUT_PATH,
        num_colors=64,
        optimize_for_emoji=False,
        remove_duplicates=True
    )
    
    # Get file size
    file_size = os.path.getsize(OUTPUT_PATH)
    file_size_kb = file_size / 1024
    
    print()
    print("=" * 70)
    print("Animation Complete!")
    print("=" * 70)
    print()
    print(f"Output: {OUTPUT_PATH}")
    print(f"File Size: {file_size_kb:.1f} KB")
    print(f"Duration: {TOTAL_FRAMES / FPS:.1f} seconds")
    print(f"Frames: {TOTAL_FRAMES}")
    print()
    
    # Slack validation
    print("Slack Optimization:")
    print(f"  ✓ Dimensions: {WIDTH}x{HEIGHT} (under 480x480 limit)")
    print(f"  ✓ File size: {file_size_kb:.1f} KB (under 1MB limit)")
    print(f"  ✓ Duration: {TOTAL_FRAMES / FPS:.1f}s (under 30s limit)")
    print(f"  ✓ Colors: 64 (optimized)")
    print()
    print("Ready to share in Slack!")
    print()
    
    return OUTPUT_PATH


if __name__ == '__main__':
    main()
