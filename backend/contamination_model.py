"""
Contamination Detection Model - Random Forest Classifier
Training and prediction functions
"""

import os
import glob
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from typing import Tuple, Dict
from PIL import Image

from backend.feature_extraction import extract_features


class ContaminationDetector:
    """Random Forest-based contamination detector"""
    
    def __init__(self, model_path: str = "backend/models/rf_model.pkl",
                 scaler_path: str = "backend/models/scaler.pkl"):
        """
        Initialize detector
        
        Args:
            model_path: Path to save/load trained model
            scaler_path: Path to save/load feature scaler
        """
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.model = None
        self.scaler = None
        
        # Create models directory if it doesn't exist
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    def train(self, clean_dir: str = "1_Clean_Samples",
              contaminated_dir: str = "2_Contaminated_Samples",
              target_size: Tuple[int, int] = (128, 128),
              test_size: float = 0.2,
              random_state: int = 42) -> Dict:
        """
        Train Random Forest model on artificial data
        
        Args:
            clean_dir: Directory with clean images
            contaminated_dir: Directory with contaminated images
            target_size: Target image size
            test_size: Fraction of data for testing
            random_state: Random seed
            
        Returns:
            Training results dictionary
        """
        print("="*70)
        print("TRAINING CONTAMINATION DETECTOR")
        print("="*70)
        
        # Load data
        print("\nLoading images...")
        X_clean, y_clean = self._load_images_from_dir(clean_dir, label=0, target_size=target_size)
        X_contam, y_contam = self._load_images_from_dir(contaminated_dir, label=1, target_size=target_size)
        
        # Combine data
        X = np.vstack([X_clean, X_contam])
        y = np.concatenate([y_clean, y_contam])
        
        print(f"\nDataset:")
        print(f"  Clean samples:        {len(y_clean)}")
        print(f"  Contaminated samples: {len(y_contam)}")
        print(f"  Total samples:        {len(y)}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"\nSplit:")
        print(f"  Training:   {len(y_train)} samples")
        print(f"  Testing:    {len(y_test)} samples")
        
        # Train scaler
        print("\nStandardizing features...")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        print("\nTraining Random Forest...")
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=4,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=random_state,
            class_weight='balanced',
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        print("\nEvaluating model...")
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        print(f"\nAccuracy:")
        print(f"  Training:   {train_acc:.4f} ({train_acc*100:.2f}%)")
        print(f"  Testing:    {test_acc:.4f} ({test_acc*100:.2f}%)")
        
        print("\nClassification Report (Test Set):")
        print(classification_report(y_test, test_pred, 
                                    target_names=['Clean', 'Contaminated'],
                                    digits=4))
        
        # Save model and scaler
        print("\nSaving model and scaler...")
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print(f"  Model saved to: {self.model_path}")
        print(f"  Scaler saved to: {self.scaler_path}")
        
        print("\n" + "="*70)
        print("TRAINING COMPLETE!")
        print("="*70)
        
        return {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'n_samples': len(y),
            'n_features': X.shape[1]
        }
    
    def _load_images_from_dir(self, directory: str, label: int,
                              target_size: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
        """Load images from directory and extract features"""
        # Find all image files
        patterns = ['*.tif', '*.tiff', '*.png', '*.jpg', '*.jpeg']
        image_paths = []
        for pattern in patterns:
            image_paths.extend(glob.glob(os.path.join(directory, pattern)))
        
        if len(image_paths) == 0:
            raise ValueError(f"No images found in {directory}")
        
        # Extract features from all images
        features = []
        for path in image_paths:
            img = Image.open(path)
            if img.mode != 'L':
                img = img.convert('L')
            img = img.resize(target_size)
            
            feat = extract_features(img)
            features.append(feat)
        
        X = np.array(features)
        y = np.full(len(features), label, dtype=np.int32)
        
        return X, y
    
    def load_model(self) -> bool:
        """
        Load trained model and scaler from disk
        
        Returns:
            True if successful, False otherwise
        """
        if not self.model_path.exists() or not self.scaler_path.exists():
            print(f"Model or scaler not found:")
            print(f"  Model: {self.model_path}")
            print(f"  Scaler: {self.scaler_path}")
            return False
        
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            print(f"Model loaded successfully from {self.model_path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def predict(self, image: np.ndarray) -> Dict:
        """
        Predict if image shows contamination
        
        Args:
            image: Input image (numpy array or PIL Image)
            
        Returns:
            Dictionary with prediction results
        """
        if self.model is None or self.scaler is None:
            # Try to load model
            if not self.load_model():
                raise ValueError("Model not trained or loaded")
        
        # Extract features
        features = extract_features(image).reshape(1, -1)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Label: 0 = clean, 1 = contaminated
        label = "clean" if prediction == 0 else "contaminated"
        confidence = float(probabilities[prediction])
        
        return {
            'label': label,
            'confidence': confidence,
            'probabilities': {
                'clean': float(probabilities[0]),
                'contaminated': float(probabilities[1])
            }
        }

