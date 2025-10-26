"""
Generate 10 Realistic 96-Well Plate Datasets
Each plate has mostly good growth with random outliers
Includes ground truth annotations for validation
"""

import numpy as np
import pandas as pd
import random
import os

np.random.seed(42)


def generate_good_growth(time, noise=0.01):
    """Generate normal, healthy growth curve"""
    K = np.random.uniform(0.9, 1.1)
    r = np.random.uniform(0.55, 0.65)
    N0 = np.random.uniform(0.06, 0.08)
    t0 = np.random.uniform(1.2, 1.8)
    
    growth = K / (1 + ((K - N0) / N0) * np.exp(-r * (time - t0)))
    growth += np.random.normal(0, noise, len(time))
    growth = np.maximum(growth, 0.05)
    
    return growth


def generate_no_growth(time, noise=0.005):
    """Generate no growth - flat line"""
    base_od = np.random.uniform(0.05, 0.08)
    flat_line = np.ones(len(time)) * base_od
    flat_line += np.random.normal(0, noise, len(time))
    flat_line = np.maximum(flat_line, 0.04)
    
    return flat_line


def generate_bubbles(time):
    """Generate curve with sudden spikes (bubbles)"""
    # Start with normal growth
    K = np.random.uniform(0.9, 1.1)
    r = np.random.uniform(0.55, 0.65)
    N0 = np.random.uniform(0.06, 0.08)
    t0 = np.random.uniform(1.2, 1.8)
    
    growth = K / (1 + ((K - N0) / N0) * np.exp(-r * (time - t0)))
    
    # Add sudden spike(s)
    spike_time = np.random.randint(40, 80)
    spike_duration = np.random.randint(2, 6)
    spike_magnitude = np.random.uniform(0.2, 0.4)
    
    growth[spike_time:spike_time+spike_duration] += spike_magnitude
    
    # Optional second spike
    if np.random.random() > 0.6:
        spike_time2 = np.random.randint(spike_time+10, 90)
        growth[spike_time2:spike_time2+3] += np.random.uniform(0.15, 0.25)
    
    growth += np.random.normal(0, 0.01, len(time))
    growth = np.maximum(growth, 0.05)
    
    return growth


def generate_contamination(time):
    """Generate contamination - abnormally high growth"""
    K = np.random.uniform(1.5, 2.0)  # Very high
    r = np.random.uniform(0.7, 0.95)
    N0 = np.random.uniform(0.08, 0.11)
    t0 = np.random.uniform(0.5, 1.0)
    
    growth = K / (1 + ((K - N0) / N0) * np.exp(-r * (time - t0)))
    growth += np.random.normal(0, 0.015, len(time))
    growth = np.maximum(growth, 0.05)
    
    return growth


def generate_declining(time):
    """Generate declining - death phase after growth"""
    K = np.random.uniform(1.0, 1.2)
    r = np.random.uniform(0.6, 0.7)
    N0 = np.random.uniform(0.07, 0.08)
    t0 = np.random.uniform(1.0, 1.5)
    
    growth = K / (1 + ((K - N0) / N0) * np.exp(-r * (time - t0)))
    
    # Add decline after certain point
    decline_start_idx = np.random.randint(65, 75)
    decline_rate = np.random.uniform(0.006, 0.012)
    
    for idx in range(decline_start_idx, len(time)):
        growth[idx] = growth[decline_start_idx] - decline_rate * (idx - decline_start_idx)
    
    growth += np.random.normal(0, 0.01, len(time))
    growth = np.maximum(growth, 0.05)
    
    return growth


def generate_noisy(time):
    """Generate high noise - measurement problems"""
    K = np.random.uniform(0.9, 1.1)
    r = np.random.uniform(0.55, 0.65)
    N0 = np.random.uniform(0.06, 0.08)
    t0 = np.random.uniform(1.2, 1.8)
    
    growth = K / (1 + ((K - N0) / N0) * np.exp(-r * (time - t0)))
    growth += np.random.normal(0, 0.06, len(time))  # High noise
    growth = np.maximum(growth, 0.04)
    
    return growth


def generate_well_name(row, col):
    """Generate well name like A1, B2, etc."""
    rows = 'ABCDEFGH'
    return f"{rows[row]}{col+1}"


def create_plate_layout():
    """Create list of all 96 well positions"""
    rows = 'ABCDEFGH'
    wells = []
    for row in rows:
        for col in range(1, 13):
            wells.append(f"{row}{col}")
    return wells


def generate_plate_dataset(plate_num, time, output_dir):
    """
    Generate one 96-well plate with realistic distribution of categories
    
    Realistic distribution:
    - 70-80% good growth (67-77 wells)
    - 5-8% no growth (5-8 wells)
    - 3-5% bubbles (3-5 wells)
    - 3-5% contamination (3-5 wells)
    - 2-4% declining (2-4 wells)
    - 3-5% noisy (3-5 wells)
    """
    
    # Define number of each type (totaling 96)
    # Make it realistic with mostly good growth
    n_good = random.randint(67, 77)
    
    remaining = 96 - n_good
    
    # Distribute outliers
    n_no_growth = random.randint(3, min(8, remaining))
    remaining -= n_no_growth
    
    n_bubbles = random.randint(2, min(5, remaining))
    remaining -= n_bubbles
    
    n_contamination = random.randint(2, min(5, remaining))
    remaining -= n_contamination
    
    n_declining = random.randint(2, min(4, remaining))
    remaining -= n_declining
    
    n_noisy = remaining  # Whatever's left
    
    print(f"\nPlate {plate_num} distribution:")
    print(f"  Good growth: {n_good} wells ({n_good/96*100:.1f}%)")
    print(f"  No growth: {n_no_growth} wells ({n_no_growth/96*100:.1f}%)")
    print(f"  Bubbles: {n_bubbles} wells ({n_bubbles/96*100:.1f}%)")
    print(f"  Contamination: {n_contamination} wells ({n_contamination/96*100:.1f}%)")
    print(f"  Declining: {n_declining} wells ({n_declining/96*100:.1f}%)")
    print(f"  Noisy: {n_noisy} wells ({n_noisy/96*100:.1f}%)")
    
    # Create category assignments for all wells
    categories = (
        ['good_growth'] * n_good +
        ['no_growth'] * n_no_growth +
        ['bubbles'] * n_bubbles +
        ['contamination'] * n_contamination +
        ['declining'] * n_declining +
        ['noisy'] * n_noisy
    )
    
    # Shuffle to randomize positions
    random.shuffle(categories)
    
    # Get well names
    wells = create_plate_layout()
    
    # Generate data for each well
    data = {'time_seconds': time * 3600}  # Convert hours to seconds like real data
    annotations = []
    
    for well_name, category in zip(wells, categories):
        # Generate curve based on category
        if category == 'good_growth':
            curve = generate_good_growth(time)
        elif category == 'no_growth':
            curve = generate_no_growth(time)
        elif category == 'bubbles':
            curve = generate_bubbles(time)
        elif category == 'contamination':
            curve = generate_contamination(time)
        elif category == 'declining':
            curve = generate_declining(time)
        elif category == 'noisy':
            curve = generate_noisy(time)
        
        data[well_name] = curve
        
        # Record annotation
        annotations.append({
            'well_id': well_name,
            'category': category,
            'is_outlier': category != 'good_growth',
            'plate_number': plate_num
        })
    
    # Create DataFrames
    df = pd.DataFrame(data)
    annotations_df = pd.DataFrame(annotations)
    
    # Save files
    data_filename = f'plate_{plate_num:02d}_data.csv'
    annotation_filename = f'plate_{plate_num:02d}_annotations.csv'
    
    df.to_csv(os.path.join(output_dir, data_filename), index=False)
    annotations_df.to_csv(os.path.join(output_dir, annotation_filename), index=False)
    
    print(f"  ✓ Saved: {data_filename}")
    print(f"  ✓ Saved: {annotation_filename}")
    
    return df, annotations_df


def create_combined_annotation_summary(output_dir, n_plates):
    """Create a combined summary of all annotations"""
    all_annotations = []
    
    for plate_num in range(1, n_plates + 1):
        annotation_file = os.path.join(output_dir, f'plate_{plate_num:02d}_annotations.csv')
        df = pd.read_csv(annotation_file)
        all_annotations.append(df)
    
    combined = pd.concat(all_annotations, ignore_index=True)
    combined.to_csv(os.path.join(output_dir, 'all_plates_annotations.csv'), index=False)
    
    # Create summary statistics
    summary = combined.groupby(['plate_number', 'category']).size().reset_index(name='count')
    summary_pivot = summary.pivot(index='plate_number', columns='category', values='count').fillna(0).astype(int)
    summary_pivot.to_csv(os.path.join(output_dir, 'plates_summary.csv'))
    
    print("\n" + "="*70)
    print("COMBINED SUMMARY")
    print("="*70)
    print(summary_pivot.to_string())
    
    return combined, summary_pivot


def create_readme(output_dir):
    """Create README for the dataset"""
    readme_content = """# 96-Well Plate Growth Curve Datasets - Ground Truth

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
"""
    
    with open(os.path.join(output_dir, 'README.txt'), 'w') as f:
        f.write(readme_content)
    
    print("\n✓ Created README.txt")


def main():
    """Generate all plate datasets"""
    print("\n" + "="*70)
    print("GENERATING 10 REALISTIC 96-WELL PLATE DATASETS")
    print("="*70)
    
    # Create output directory
    output_dir = '/mnt/user-data/outputs/plate_datasets'
    os.makedirs(output_dir, exist_ok=True)
    
    # Time points (simulating ~2.5 hours with measurements every 30 seconds)
    time = np.linspace(0, 2.5, 100)  # 0-2.5 hours
    
    # Generate 10 plates
    n_plates = 10
    
    for plate_num in range(1, n_plates + 1):
        generate_plate_dataset(plate_num, time, output_dir)
    
    # Create combined summary
    print("\n" + "="*70)
    print("CREATING COMBINED SUMMARIES")
    print("="*70)
    combined, summary = create_combined_annotation_summary(output_dir, n_plates)
    print("✓ Created all_plates_annotations.csv")
    print("✓ Created plates_summary.csv")
    
    # Create README
    create_readme(output_dir)
    
    # Print overall statistics
    print("\n" + "="*70)
    print("DATASET GENERATION COMPLETE")
    print("="*70)
    print(f"\nTotal plates generated: {n_plates}")
    print(f"Total wells: {n_plates * 96}")
    print(f"Output directory: {output_dir}")
    
    # Category totals
    print("\nOverall category distribution:")
    category_totals = combined.groupby('category').size().sort_values(ascending=False)
    for category, count in category_totals.items():
        percentage = count / (n_plates * 96) * 100
        print(f"  {category:20s}: {count:3d} wells ({percentage:5.1f}%)")
    
    print("\n" + "="*70)
    print("FILES CREATED:")
    print("="*70)
    print("Data files:")
    for i in range(1, n_plates + 1):
        print(f"  • plate_{i:02d}_data.csv")
    print("\nAnnotation files:")
    for i in range(1, n_plates + 1):
        print(f"  • plate_{i:02d}_annotations.csv")
    print("\nSummary files:")
    print("  • all_plates_annotations.csv")
    print("  • plates_summary.csv")
    print("  • README.txt")
    
    print("\n" + "="*70)
    print("✅ SUCCESS! All datasets ready for testing!")
    print("="*70)
    print("\nTo use:")
    print("  1. Load data: pd.read_csv('plate_01_data.csv')")
    print("  2. Load truth: pd.read_csv('plate_01_annotations.csv')")
    print("  3. Test your algorithm")
    print("  4. Compare with ground truth")
    print("  5. Calculate accuracy metrics!")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
