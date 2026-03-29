"""
Easing Functions Module

Provides smooth interpolation functions for animation.
"""

import math
from typing import Callable


def interpolate(start: float, end: float, t: float, 
                easing: str = 'linear') -> float:
    """
    Interpolate between start and end values with easing.
    
    Args:
        start: Starting value
        end: Ending value
        t: Progress from 0.0 to 1.0
        easing: Easing function name
        
    Returns:
        Interpolated value
    """
    # Apply easing function to t
    if easing == 'linear':
        eased_t = t
    elif easing == 'ease_in':
        eased_t = t * t
    elif easing == 'ease_out':
        eased_t = t * (2 - t)
    elif easing == 'ease_in_out':
        if t < 0.5:
            eased_t = 2 * t * t
        else:
            eased_t = -1 + (4 - 2 * t) * t
    elif easing == 'bounce_out':
        eased_t = _bounce_out(t)
    elif easing == 'elastic_out':
        eased_t = _elastic_out(t)
    elif easing == 'back_out':
        eased_t = _back_out(t)
    else:
        eased_t = t
    
    # Interpolate
    return start + (end - start) * eased_t


def _bounce_out(t: float) -> float:
    """Bounce easing - overshoots and bounces back."""
    n1 = 7.5625
    d1 = 2.75
    
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def _elastic_out(t: float) -> float:
    """Elastic easing - oscillates around endpoint."""
    if t == 0:
        return 0
    if t == 1:
        return 1
    
    c4 = (2 * math.pi) / 3
    
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def _back_out(t: float) -> float:
    """Back easing - goes backward before moving forward."""
    c1 = 1.70158
    c3 = c1 + 1
    
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_in_quad(t: float) -> float:
    """Quadratic ease in - accelerates from zero velocity."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease out - decelerates to zero velocity."""
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease in and out - accelerates then decelerates."""
    if t < 0.5:
        return 2 * t * t
    else:
        return -1 + (4 - 2 * t) * t


def ease_in_cubic(t: float) -> float:
    """Cubic ease in."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease out."""
    return 1 - pow(1 - t, 3)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease in and out."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def sine_in(t: float) -> float:
    """Sine ease in."""
    return 1 - math.cos((t * math.pi) / 2)


def sine_out(t: float) -> float:
    """Sine ease out."""
    return math.sin((t * math.pi) / 2)


def sine_in_out(t: float) -> float:
    """Sine ease in and out."""
    return -(math.cos(math.pi * t) - 1) / 2


# Easing function registry
EASING_FUNCTIONS = {
    'linear': lambda t: t,
    'ease_in': ease_in_quad,
    'ease_out': ease_out_quad,
    'ease_in_out': ease_in_out_quad,
    'ease_in_cubic': ease_in_cubic,
    'ease_out_cubic': ease_out_cubic,
    'ease_in_out_cubic': ease_in_out_cubic,
    'bounce_out': _bounce_out,
    'elastic_out': _elastic_out,
    'back_out': _back_out,
    'sine_in': sine_in,
    'sine_out': sine_out,
    'sine_in_out': sine_in_out
}


def get_easing_function(name: str) -> Callable[[float], float]:
    """
    Get easing function by name.
    
    Args:
        name: Name of easing function
        
    Returns:
        Easing function
        
    Raises:
        ValueError: If easing function not found
    """
    if name not in EASING_FUNCTIONS:
        raise ValueError(f"Unknown easing function: {name}")
    return EASING_FUNCTIONS[name]
