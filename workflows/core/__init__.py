"""
Core Workflow Utilities

Shared utilities for workflow animations and visualizations.
"""

from .gif_builder import GIFBuilder, validate_gif_for_slack, is_slack_ready
from .frame_composer import (
    create_blank_frame,
    create_gradient_background,
    draw_circle,
    draw_star,
    draw_text,
    draw_text_centered,
    draw_rect,
    draw_line,
    draw_polygon
)
from .easing import interpolate, get_easing_function, EASING_FUNCTIONS

__all__ = [
    'GIFBuilder',
    'validate_gif_for_slack',
    'is_slack_ready',
    'create_blank_frame',
    'create_gradient_background',
    'draw_circle',
    'draw_star',
    'draw_text',
    'draw_text_centered',
    'draw_rect',
    'draw_line',
    'draw_polygon',
    'interpolate',
    'get_easing_function',
    'EASING_FUNCTIONS'
]
