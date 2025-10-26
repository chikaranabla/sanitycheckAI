"""
Train the Random Forest contamination detection model
Run this script before starting the server for the first time
"""

import os
from backend.contamination_model import ContaminationDetector

def main():
    """Train model on artificial data"""
    print("="*70)
    print("SanityCheck AI - Model Training")
    print("="*70)
    print()
    
    # Check if data directories exist
    if not os.path.exists("1_Clean_Samples"):
        print("❌ ERROR: Directory '1_Clean_Samples' not found!")
        print("   Please ensure the clean samples directory exists.")
        return
    
    if not os.path.exists("2_Contaminated_Samples"):
        print("❌ ERROR: Directory '2_Contaminated_Samples' not found!")
        print("   Please ensure the contaminated samples directory exists.")
        return
    
    # Create detector
    detector = ContaminationDetector()
    
    # Train model
    try:
        results = detector.train(
            clean_dir="1_Clean_Samples",
            contaminated_dir="2_Contaminated_Samples"
        )
        
        print("\n" + "="*70)
        print("✅ MODEL TRAINING SUCCESSFUL!")
        print("="*70)
        print(f"\nTraining Accuracy:  {results['train_accuracy']:.4f} ({results['train_accuracy']*100:.2f}%)")
        print(f"Testing Accuracy:   {results['test_accuracy']:.4f} ({results['test_accuracy']*100:.2f}%)")
        print(f"Total Samples:      {results['n_samples']}")
        print(f"Number of Features: {results['n_features']}")
        print("\nThe model is now ready to use!")
        print("You can start the server with: python -m backend.main")
        print()
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ MODEL TRAINING FAILED!")
        print("="*70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

