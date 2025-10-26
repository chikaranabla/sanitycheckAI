"""
Data Loader for Artificial Well Images
"""

import glob
import os
from pathlib import Path
from PIL import Image
import numpy as np
from typing import List, Tuple, Dict


class WellImageLoader:
    """Load and manage artificial well images for simulation"""
    
    def __init__(self, clean_dir: str = "1_Clean_Samples", 
                 contaminated_dir: str = "2_Contaminated_Samples",
                 target_size: Tuple[int, int] = (128, 128)):
        """
        Initialize image loader
        
        Args:
            clean_dir: Directory containing clean well images
            contaminated_dir: Directory containing contaminated well images
            target_size: Target image size (width, height)
        """
        self.clean_dir = Path(clean_dir)
        self.contaminated_dir = Path(contaminated_dir)
        self.target_size = target_size
        
        # Load image paths
        self.clean_images = self._load_image_paths(self.clean_dir)
        self.contaminated_images = self._load_image_paths(self.contaminated_dir)
        
        print(f"Loaded {len(self.clean_images)} clean images")
        print(f"Loaded {len(self.contaminated_images)} contaminated images")
        
        if len(self.clean_images) == 0 or len(self.contaminated_images) == 0:
            print(f"WARNING: No images found!")
            print(f"  Clean dir: {self.clean_dir.absolute()}")
            print(f"  Contaminated dir: {self.contaminated_dir.absolute()}")
    
    def _load_image_paths(self, directory: Path) -> List[str]:
        """Load all image paths from directory"""
        if not directory.exists():
            print(f"WARNING: Directory {directory} does not exist")
            return []
        
        # Support multiple image formats
        patterns = ['*.tif', '*.tiff', '*.png', '*.jpg', '*.jpeg']
        paths = []
        for pattern in patterns:
            paths.extend(glob.glob(str(directory / pattern)))
        
        return sorted(paths)
    
    def load_image(self, path: str, resize: bool = True) -> np.ndarray:
        """
        Load and preprocess image
        
        Args:
            path: Path to image file
            resize: Whether to resize to target size
            
        Returns:
            Preprocessed image as numpy array (grayscale, 0-1 range)
        """
        img = Image.open(path)
        
        # Convert to grayscale if needed
        if img.mode != 'L':
            img = img.convert('L')
        
        # Resize if requested
        if resize:
            img = img.resize(self.target_size)
        
        # Convert to numpy array and normalize
        img_array = np.array(img).astype(np.float32) / 255.0
        
        return img_array
    
    def get_random_clean_image(self) -> Tuple[str, np.ndarray]:
        """
        Get random clean image
        
        Returns:
            Tuple of (image_path, image_array)
        """
        if len(self.clean_images) == 0:
            raise ValueError("No clean images available")
        
        path = np.random.choice(self.clean_images)
        img = self.load_image(path)
        return path, img
    
    def get_random_contaminated_image(self, contamination_level: str = None) -> Tuple[str, np.ndarray]:
        """
        Get random contaminated image
        
        Args:
            contamination_level: 'light', 'medium', 'heavy', or None (random)
            
        Returns:
            Tuple of (image_path, image_array)
        """
        if len(self.contaminated_images) == 0:
            raise ValueError("No contaminated images available")
        
        # Filter by contamination level if specified
        if contamination_level:
            filtered_images = [
                p for p in self.contaminated_images 
                if contamination_level.lower() in os.path.basename(p).lower()
            ]
            if filtered_images:
                path = np.random.choice(filtered_images)
            else:
                path = np.random.choice(self.contaminated_images)
        else:
            path = np.random.choice(self.contaminated_images)
        
        img = self.load_image(path)
        return path, img
    
    def get_dataset_info(self) -> Dict:
        """Get information about loaded dataset"""
        # Count contamination levels
        light_count = sum(1 for p in self.contaminated_images if 'light' in os.path.basename(p).lower())
        medium_count = sum(1 for p in self.contaminated_images if 'medium' in os.path.basename(p).lower())
        heavy_count = sum(1 for p in self.contaminated_images if 'heavy' in os.path.basename(p).lower())
        
        return {
            'total_images': len(self.clean_images) + len(self.contaminated_images),
            'clean_images': len(self.clean_images),
            'contaminated_images': len(self.contaminated_images),
            'contamination_breakdown': {
                'light': light_count,
                'medium': medium_count,
                'heavy': heavy_count
            },
            'target_size': self.target_size
        }

