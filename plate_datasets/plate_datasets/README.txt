# 96-Well Plate Growth Curve Datasets - Ground Truth

## Overview

This folder contains **10 simulated 96-well plate datasets** with realistic distributions
of bacterial growth curves. Each plate has **mostly good growth (70-80%) with random 
outliers (20-30%)** distributed across 6 categories.

Perfect for testing and validating your outlier detection algorithms!

## Files Structure

### Data Files (10 plates)
- `plate_01_data.csv` through `plate_10_data.csv`
  - Each file contains OD600 measurements for 96 wells over time
  - Column format: time_seconds, A1, A2, ..., H12
  - ~100 timepoints per plate (simulating measurements every 30 seconds)

### Annotation Files (10 plates)
- `plate_01_annotations.csv` through `plate_10_annotations.csv`
  - **Ground truth labels** for each well
  - Columns: well_id, category, is_outlier, plate_number

### Summary Files
- `all_plates_annotations.csv` - Combined annotations from all 10 plates
- `plates_summary.csv` - Summary table showing category counts per plate
- `README.txt` - This file

## Categories (6 types)

### ✅ GOOD GROWTH (70-80% of wells)
- Normal, healthy bacterial growth
- Standard logistic curve pattern
- **Should NOT be flagged as outliers**

### 🚫 NO GROWTH (3-8% of wells)
- Flat line at baseline OD
- Causes: Dead culture, no inoculation
- **Easy to detect**: Zero growth rate

### 💧 BUBBLES (2-5% of wells)
- Sudden spikes in readings
- Causes: Air bubbles, debris, condensation
- **Easy to detect**: High noise, sudden jumps

### 🦠 CONTAMINATION (2-5% of wells)
- Abnormally high final OD (1.5-2.0x normal)
- Causes: Cross-contamination
- **Easy to detect**: Very high max OD

### 📉 DECLINING (2-4% of wells)
- Normal growth followed by death phase
- Causes: Nutrient depletion, cell lysis
- **Moderate difficulty**: Requires curve shape analysis

### 📡 NOISY (3-5% of wells)
- High measurement variability
- Causes: Instrument issues, evaporation
- **Easy to detect**: High standard deviation

## How to Use

### Load Data
```python
import pandas as pd

# Load plate data
plate1 = pd.read_csv('plate_01_data.csv')

# Load ground truth annotations
annotations1 = pd.read_csv('plate_01_annotations.csv')

# See what categories are in each well
print(annotations1.head())
```

### Test Your Detection Algorithm
```python
# Your detection function
detected_outliers = your_detection_algorithm(plate1)

# Compare with ground truth
true_outliers = set(annotations1[annotations1['is_outlier']]['well_id'])
detected_set = set(detected_outliers)

# Calculate accuracy
true_positives = len(true_outliers & detected_set)
false_positives = len(detected_set - true_outliers)
false_negatives = len(true_outliers - detected_set)

sensitivity = true_positives / len(true_outliers)
specificity = true_negatives / total_normal_wells

print(f"Sensitivity: {sensitivity:.1%}")
print(f"Specificity: {specificity:.1%}")
```

### Validate Across All Plates
```python
# Load combined annotations
all_annotations = pd.read_csv('all_plates_annotations.csv')

# Test on all 10 plates
for plate_num in range(1, 11):
    plate_data = pd.read_csv(f'plate_{plate_num:02d}_data.csv')
    plate_annotations = all_annotations[all_annotations['plate_number'] == plate_num]
    
    # Run your detection
    detected = your_detection_algorithm(plate_data)
    
    # Calculate metrics
    # ... your evaluation code
```

## Expected Performance Benchmarks

Good detection algorithms should achieve:
- **Sensitivity (True Positive Rate)**: >85%
  - Catch most outliers (especially contamination, bubbles, no growth)
  
- **Specificity (True Negative Rate)**: >90%
  - Don't over-flag normal growth wells
  
- **Precision**: >70%
  - Most flagged wells should be true outliers
  
- **Overall Accuracy**: >85%

### Category-Specific Detection Rates
- Easy categories (bubbles, contamination, no growth): >90%
- Moderate categories (noisy, declining): >70%
- All categories combined: >80%

## Statistics

### Overall Dataset
- Total plates: 10
- Total wells: 960 (96 wells × 10 plates)
- Timepoints per plate: ~100
- Duration per plate: ~2.5 hours (simulated)

### Category Distribution (Approximate)
- Good growth: ~700 wells (73%)
- Outliers: ~260 wells (27%)
  - No growth: ~50 wells (5%)
  - Bubbles: ~35 wells (4%)
  - Contamination: ~35 wells (4%)
  - Declining: ~30 wells (3%)
  - Noisy: ~40 wells (4%)

## Validation Tips

### 1. Start with Easy Categories
Test your algorithm on obvious outliers first:
- Contamination (very high OD)
- No growth (flat line)
- Bubbles (sudden spikes)

### 2. Tune Thresholds
Use multiple plates to find optimal detection thresholds that balance
sensitivity and specificity.

### 3. Category-Specific Methods
Different outliers may need different detection approaches:
- Z-score works well for contamination
- Noise detection for bubbles
- Slope analysis for no growth
- Curve shape for declining

### 4. Cross-Validation
Train on plates 1-7, test on plates 8-10 to avoid overfitting.

## Real-World Simulation Details

These datasets simulate realistic experimental conditions:
- **Realistic distributions**: Most wells are normal (70-80%)
- **Random placement**: Outliers distributed randomly across plate
- **Biological variation**: Normal wells show natural variation
- **Measurement noise**: All curves include realistic noise
- **Edge effects**: Not explicitly modeled (can be added if needed)

## Citation

If using this dataset for your hackathon or research:

"Validated on 10 simulated 96-well plates (960 wells total) with ground truth 
annotations across 6 categories, achieving X% accuracy with Y% sensitivity."

## Questions?

This dataset was created to help validate outlier detection algorithms for
growth curve analysis. The ground truth annotations allow precise calculation
of accuracy metrics.

Good luck with your testing! 🚀

---
Generated: October 2025
Format: 96-well plate (8 rows × 12 columns)
Categories: 6 (good_growth, no_growth, bubbles, contamination, declining, noisy)
Ground Truth: Yes (annotations provided for all wells)
