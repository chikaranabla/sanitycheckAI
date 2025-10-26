"""
Feature Extraction Module for Bacterial Culture Contamination Detection
Based on v2_hack_sanitycheckai.py approach
"""

import numpy as np
import cv2
from scipy import stats
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from typing import Union
from PIL import Image


def extract_features(image: Union[np.ndarray, Image.Image]) -> np.ndarray:
    """
    Extract comprehensive features from bacterial culture well image
    
    Features extracted:
    - Intensity statistics (7 features)
    - Texture features via GLCM (12 features)
    - Local Binary Pattern (3 features)
    - Edge features (2 features)
    - Gradient features (2 features)
    - FFT frequency domain (2 features)
    
    Total: 28 features
    
    Args:
        image: Input image (PIL Image or numpy array)
        
    Returns:
        Feature vector (numpy array of shape (28,))
    """
    # Convert to numpy array if PIL Image
    if isinstance(image, Image.Image):
        img = np.array(image)
    else:
        img = image.copy()
    
    # Ensure grayscale
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Normalize to 0-1 range
    if img.dtype == np.uint8:
        img_normalized = img.astype(np.float32) / 255.0
    else:
        img_normalized = img.astype(np.float32)
        if img_normalized.max() > 1.0:
            img_normalized = img_normalized / img_normalized.max()
    
    # Convert back to uint8 for feature extraction
    img_uint8 = (img_normalized * 255).astype(np.uint8)
    
    features = []
    
    # ===== 1. INTENSITY STATISTICS (7 features) =====
    features.extend([
        np.mean(img_uint8),           # Mean intensity
        np.std(img_uint8),            # Standard deviation
        np.min(img_uint8),            # Minimum intensity
        np.max(img_uint8),            # Maximum intensity
        np.median(img_uint8),         # Median intensity
        stats.skew(img_uint8.flatten()),  # Skewness
        stats.kurtosis(img_uint8.flatten())  # Kurtosis
    ])
    
    # ===== 2. TEXTURE FEATURES (GLCM) (12 features) =====
    # Gray Level Co-occurrence Matrix
    glcm = graycomatrix(
        img_uint8,
        distances=[1, 2],
        angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
        levels=256,
        symmetric=True,
        normed=True
    )
    
    # Calculate texture properties
    for prop in ['contrast', 'dissimilarity', 'homogeneity', 'energy', 'correlation', 'ASM']:
        prop_values = graycoprops(glcm, prop).flatten()
        features.extend([
            np.mean(prop_values),  # Mean of property
            np.std(prop_values)    # Std of property
        ])
    
    # ===== 3. LOCAL BINARY PATTERN (LBP) (3 features) =====
    # Captures local texture patterns
    radius = 3
    n_points = 8 * radius
    lbp = local_binary_pattern(img_uint8, n_points, radius, method='uniform')
    
    # LBP histogram statistics
    n_bins = int(lbp.max() + 1)
    lbp_hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=True)
    features.extend([
        np.mean(lbp_hist),  # Mean of LBP histogram
        np.std(lbp_hist),   # Std of LBP histogram
        np.max(lbp_hist)    # Max of LBP histogram
    ])
    
    # ===== 4. EDGE FEATURES (2 features) =====
    edges = cv2.Canny(img_uint8, 50, 150)
    features.extend([
        np.sum(edges > 0) / edges.size,  # Edge density
        np.std(edges)                     # Edge variation
    ])
    
    # ===== 5. GRADIENT FEATURES (2 features) =====
    gradient_x = cv2.Sobel(img_uint8, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(img_uint8, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
    
    features.extend([
        np.mean(gradient_magnitude),  # Mean gradient magnitude
        np.std(gradient_magnitude)    # Std gradient magnitude
    ])
    
    # ===== 6. FREQUENCY DOMAIN FEATURES (FFT) (2 features) =====
    fft = np.fft.fft2(img_uint8)
    fft_shift = np.fft.fftshift(fft)
    magnitude_spectrum = np.abs(fft_shift)
    
    features.extend([
        np.mean(magnitude_spectrum),  # Mean FFT magnitude
        np.std(magnitude_spectrum)    # Std FFT magnitude
    ])
    
    return np.array(features, dtype=np.float32)


def get_feature_names() -> list:
    """
    Get feature names for interpretation
    
    Returns:
        List of feature names
    """
    feature_names = (
        # Intensity statistics (7)
        ['Mean', 'Std', 'Min', 'Max', 'Median', 'Skew', 'Kurtosis'] +
        
        # GLCM texture features (12)
        [f'GLCM_{prop}_{stat}' 
         for prop in ['contrast', 'dissimilarity', 'homogeneity', 'energy', 'correlation', 'ASM']
         for stat in ['mean', 'std']] +
        
        # LBP features (3)
        ['LBP_mean', 'LBP_std', 'LBP_max'] +
        
        # Edge features (2)
        ['EdgeDensity', 'EdgeVariation'] +
        
        # Gradient features (2)
        ['GradientMean', 'GradientStd'] +
        
        # FFT features (2)
        ['FFT_mean', 'FFT_std']
    )
    
    return feature_names

