"""
Core GIF Builder Module

Provides GIFBuilder class for creating and optimizing animated GIFs for Slack.
"""

from PIL import Image
import imageio
import numpy as np
from typing import List, Optional
import os


class GIFBuilder:
    """
    Builder class for creating animated GIFs optimized for Slack.
    
    Attributes:
        width: Width of the GIF in pixels
        height: Height of the GIF in pixels
        fps: Frames per second
        frames: List of PIL Image frames
    """
    
    def __init__(self, width: int = 128, height: int = 128, fps: int = 10):
        """
        Initialize GIF builder.
        
        Args:
            width: Width in pixels (default 128 for emoji, 480 for messages)
            height: Height in pixels (default 128 for emoji, 480 for messages)
            fps: Frames per second (10-30 recommended)
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.frames: List[Image.Image] = []
    
    def add_frame(self, frame: Image.Image) -> None:
        """
        Add a single frame to the animation.
        
        Args:
            frame: PIL Image object for the frame
        """
        # Ensure frame is correct size
        if frame.size != (self.width, self.height):
            frame = frame.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if frame.mode != 'RGB':
            frame = frame.convert('RGB')
        
        self.frames.append(frame)
    
    def add_frames(self, frames: List[Image.Image]) -> None:
        """
        Add multiple frames to the animation.
        
        Args:
            frames: List of PIL Image objects
        """
        for frame in frames:
            self.add_frame(frame)
    
    def save(self, output_path: str, num_colors: int = 64, 
             optimize_for_emoji: bool = False, remove_duplicates: bool = True) -> str:
        """
        Save the animated GIF to a file.
        
        Args:
            output_path: Path to save the GIF
            num_colors: Number of colors in palette (48-128, fewer = smaller file)
            optimize_for_emoji: Apply emoji-specific optimizations
            remove_duplicates: Remove duplicate consecutive frames
            
        Returns:
            Path to the saved file
        """
        if not self.frames:
            raise ValueError("No frames added to GIF")
        
        # Remove duplicate frames if requested
        if remove_duplicates:
            self.frames = self._remove_duplicate_frames()
        
        # Calculate duration in milliseconds
        duration = int(1000 / self.fps)
        
        # Apply emoji optimizations if requested
        if optimize_for_emoji:
            num_colors = min(num_colors, 48)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Save using imageio with optimization
        imageio.mimsave(
            output_path,
            self.frames,
            duration=duration,
            palette=self._generate_palette(num_colors),
            loop=0  # Infinite loop
        )
        
        return output_path
    
    def _remove_duplicate_frames(self) -> List[Image.Image]:
        """Remove consecutive duplicate frames."""
        if len(self.frames) <= 1:
            return self.frames
        
        unique_frames = [self.frames[0]]
        for i in range(1, len(self.frames)):
            # Compare frames using numpy
            curr_arr = np.array(self.frames[i])
            prev_arr = np.array(unique_frames[-1])
            
            if not np.array_equal(curr_arr, prev_arr):
                unique_frames.append(self.frames[i])
        
        return unique_frames
    
    def _generate_palette(self, num_colors: int) -> Optional[List]:
        """
        Generate color palette for optimization.
        
        Args:
            num_colors: Number of colors in palette
            
        Returns:
            Palette or None for automatic generation
        """
        # Return None to let imageio generate optimal palette
        return None
    
    def get_info(self) -> dict:
        """
        Get information about the GIF.
        
        Returns:
            Dictionary with GIF information
        """
        return {
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'total_frames': len(self.frames),
            'duration_seconds': len(self.frames) / self.fps
        }


def validate_gif_for_slack(gif_path: str, is_emoji: bool = False) -> tuple:
    """
    Validate if a GIF meets Slack's requirements.
    
    Args:
        gif_path: Path to the GIF file
        is_emoji: Whether this is an emoji GIF (stricter requirements)
        
    Returns:
        Tuple of (passes_validation: bool, info: dict)
    """
    info = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check file exists
    if not os.path.exists(gif_path):
        return False, {'valid': False, 'errors': ['File not found']}
    
    # Check file size
    file_size = os.path.getsize(gif_path)
    file_size_kb = file_size / 1024
    
    if file_size_kb > 1024:  # 1MB limit
        info['errors'].append(f'File size {file_size_kb:.1f}KB exceeds 1MB limit')
        info['valid'] = False
    elif file_size_kb > 500:
        info['warnings'].append(f'File size {file_size_kb:.1f}KB is large')
    
    # Open and check dimensions
    with Image.open(gif_path) as img:
        width, height = img.size
        
        if is_emoji:
            if width != 128 or height != 128:
                info['errors'].append(f'Emoji GIF must be 128x128, got {width}x{height}')
                info['valid'] = False
        else:
            if width > 480 or height > 480:
                info['errors'].append(f'GIF dimensions {width}x{height} exceed 480x480 limit')
                info['valid'] = False
        
        # Check frame count and duration
        n_frames = img.n_frames
        duration = n_frames / 10  # Estimate at 10 fps
        
        if duration > 30:
            info['errors'].append(f'Duration {duration:.1f}s exceeds 30s limit')
            info['valid'] = False
        
        info['width'] = width
        info['height'] = height
        info['frames'] = n_frames
        info['duration'] = duration
        info['file_size_kb'] = file_size_kb
    
    return info['valid'], info


def is_slack_ready(gif_path: str) -> bool:
    """
    Quick check if GIF is ready for Slack.
    
    Args:
        gif_path: Path to the GIF file
        
    Returns:
        True if GIF meets Slack requirements
    """
    valid, _ = validate_gif_for_slack(gif_path)
    return valid
