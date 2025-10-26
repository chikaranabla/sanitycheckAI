"""
Example: Testing Your Outlier Detection on Plate Datasets
Shows how to load data, run detection, and calculate accuracy metrics
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")


def load_plate_data(plate_num, data_dir='/mnt/user-data/outputs/plate_datasets'):
    """Load a single plate's data and annotations"""
    data_file = f'{data_dir}/plate_{plate_num:02d}_data.csv'
    annotation_file = f'{data_dir}/plate_{plate_num:02d}_annotations.csv'
    
    data = pd.read_csv(data_file)
    annotations = pd.read_csv(annotation_file)
    
    return data, annotations


def calculate_growth_parameters(time, od_values):
    """Calculate key growth parameters"""
    max_od = np.max(od_values)
    growth_rate = np.max(np.diff(od_values) / np.diff(time)) if len(time) > 1 else 0
    auc = np.trapezoid(od_values, time)
    noise = np.std(np.diff(od_values))
    
    return {
        'max_od': max_od,
        'growth_rate': growth_rate,
        'auc': auc,
        'noise_level': noise
    }


def simple_outlier_detection(plate_data, threshold=2.5):
    """
    Simple Z-score based outlier detection
    Replace this with YOUR detection algorithm!
    """
    time = plate_data['time_seconds'].values / 3600  # Convert to hours
    wells = [col for col in plate_data.columns if col != 'time_seconds']
    
    # Calculate parameters for all wells
    parameters = []
    for well in wells:
        params = calculate_growth_parameters(time, plate_data[well].values)
        params['well_id'] = well
        parameters.append(params)
    
    params_df = pd.DataFrame(parameters).set_index('well_id')
    
    # Z-score detection
    outliers = []
    for feature in ['max_od', 'growth_rate', 'auc', 'noise_level']:
        z_scores = np.abs(stats.zscore(params_df[feature]))
        outliers.extend(params_df[z_scores > threshold].index.tolist())
    
    return list(set(outliers))  # Remove duplicates


def evaluate_detection(detected_outliers, annotations):
    """
    Calculate accuracy metrics comparing detected vs ground truth
    """
    # Get ground truth
    true_outliers = set(annotations[annotations['is_outlier']]['well_id'])
    normal_wells = set(annotations[~annotations['is_outlier']]['well_id'])
    detected_set = set(detected_outliers)
    
    # Calculate confusion matrix
    true_positives = len(true_outliers & detected_set)
    false_positives = len(normal_wells & detected_set)
    false_negatives = len(true_outliers - detected_set)
    true_negatives = len(normal_wells - detected_set)
    
    # Calculate metrics
    total = len(annotations)
    accuracy = (true_positives + true_negatives) / total
    
    sensitivity = true_positives / len(true_outliers) if true_outliers else 0
    specificity = true_negatives / len(normal_wells) if normal_wells else 0
    precision = true_positives / len(detected_set) if detected_set else 0
    
    # F1 score
    f1 = 2 * (precision * sensitivity) / (precision + sensitivity) if (precision + sensitivity) > 0 else 0
    
    return {
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'true_negatives': true_negatives,
        'accuracy': accuracy,
        'sensitivity': sensitivity,
        'specificity': specificity,
        'precision': precision,
        'f1_score': f1
    }


def evaluate_by_category(detected_outliers, annotations):
    """Evaluate detection performance by category"""
    results = []
    
    for category in annotations['category'].unique():
        category_wells = annotations[annotations['category'] == category]['well_id'].values
        n_total = len(category_wells)
        n_detected = sum([w in detected_outliers for w in category_wells])
        
        results.append({
            'category': category,
            'total': n_total,
            'detected': n_detected,
            'detection_rate': n_detected / n_total if n_total > 0 else 0
        })
    
    return pd.DataFrame(results)


def test_single_plate(plate_num):
    """Test detection on a single plate"""
    print(f"\n{'='*70}")
    print(f"TESTING PLATE {plate_num}")
    print(f"{'='*70}")
    
    # Load data
    data, annotations = load_plate_data(plate_num)
    print(f"✓ Loaded plate {plate_num}")
    print(f"  Wells: {len(annotations)}")
    print(f"  Normal: {sum(~annotations['is_outlier'])}")
    print(f"  Outliers: {sum(annotations['is_outlier'])}")
    
    # Run detection
    detected = simple_outlier_detection(data)
    print(f"\n✓ Detection complete")
    print(f"  Detected {len(detected)} outliers")
    
    # Evaluate
    metrics = evaluate_detection(detected, annotations)
    
    print(f"\n{'='*70}")
    print(f"PERFORMANCE METRICS")
    print(f"{'='*70}")
    print(f"Accuracy:    {metrics['accuracy']*100:5.1f}%")
    print(f"Sensitivity: {metrics['sensitivity']*100:5.1f}%  (True Positive Rate)")
    print(f"Specificity: {metrics['specificity']*100:5.1f}%  (True Negative Rate)")
    print(f"Precision:   {metrics['precision']*100:5.1f}%  (Positive Predictive Value)")
    print(f"F1 Score:    {metrics['f1_score']:.3f}")
    
    print(f"\nConfusion Matrix:")
    print(f"  True Positives:  {metrics['true_positives']:3d}")
    print(f"  False Positives: {metrics['false_positives']:3d}")
    print(f"  False Negatives: {metrics['false_negatives']:3d}")
    print(f"  True Negatives:  {metrics['true_negatives']:3d}")
    
    # Category breakdown
    category_results = evaluate_by_category(detected, annotations)
    
    print(f"\n{'='*70}")
    print(f"DETECTION BY CATEGORY")
    print(f"{'='*70}")
    for _, row in category_results.iterrows():
        rate = row['detection_rate'] * 100
        status = "✓" if (row['category'] == 'good_growth' and rate < 20) or \
                       (row['category'] != 'good_growth' and rate > 70) else "⚠"
        print(f"{status} {row['category']:20s}: {row['detected']:2d}/{row['total']:2d} ({rate:5.1f}%)")
    
    return metrics, category_results


def test_all_plates(n_plates=10):
    """Test detection on all plates and aggregate results"""
    print("\n" + "="*70)
    print("TESTING ALL PLATES")
    print("="*70)
    
    all_metrics = []
    
    for plate_num in range(1, n_plates + 1):
        metrics, _ = test_single_plate(plate_num)
        metrics['plate'] = plate_num
        all_metrics.append(metrics)
    
    # Create summary
    metrics_df = pd.DataFrame(all_metrics)
    
    print("\n" + "="*70)
    print("AGGREGATE RESULTS ACROSS ALL PLATES")
    print("="*70)
    
    print(f"\nAverage Performance:")
    print(f"  Accuracy:    {metrics_df['accuracy'].mean()*100:.1f}% (±{metrics_df['accuracy'].std()*100:.1f}%)")
    print(f"  Sensitivity: {metrics_df['sensitivity'].mean()*100:.1f}% (±{metrics_df['sensitivity'].std()*100:.1f}%)")
    print(f"  Specificity: {metrics_df['specificity'].mean()*100:.1f}% (±{metrics_df['specificity'].std()*100:.1f}%)")
    print(f"  Precision:   {metrics_df['precision'].mean()*100:.1f}% (±{metrics_df['precision'].std()*100:.1f}%)")
    print(f"  F1 Score:    {metrics_df['f1_score'].mean():.3f} (±{metrics_df['f1_score'].std():.3f})")
    
    # Total confusion matrix
    total_tp = metrics_df['true_positives'].sum()
    total_fp = metrics_df['false_positives'].sum()
    total_fn = metrics_df['false_negatives'].sum()
    total_tn = metrics_df['true_negatives'].sum()
    
    print(f"\nTotal Across All Plates:")
    print(f"  True Positives:  {total_tp}")
    print(f"  False Positives: {total_fp}")
    print(f"  False Negatives: {total_fn}")
    print(f"  True Negatives:  {total_tn}")
    
    # Save results
    metrics_df.to_csv('/mnt/user-data/outputs/plate_datasets/detection_test_results.csv', index=False)
    print(f"\n✓ Saved: detection_test_results.csv")
    
    return metrics_df


def visualize_results(metrics_df):
    """Create visualizations of test results"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Accuracy by plate
    ax = axes[0, 0]
    ax.bar(metrics_df['plate'], metrics_df['accuracy'] * 100, 
           color='#3498db', edgecolor='black', linewidth=1.5)
    ax.axhline(85, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Target (85%)')
    ax.set_xlabel('Plate Number', fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontweight='bold')
    ax.set_title('Accuracy by Plate', fontweight='bold')
    ax.set_ylim([0, 105])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Sensitivity vs Specificity
    ax = axes[0, 1]
    ax.scatter(metrics_df['specificity'] * 100, metrics_df['sensitivity'] * 100,
              s=150, alpha=0.7, color='#e74c3c', edgecolor='black', linewidth=2)
    for i, row in metrics_df.iterrows():
        ax.annotate(f"P{int(row['plate'])}", 
                   (row['specificity']*100, row['sensitivity']*100),
                   fontsize=9, ha='center', va='center', color='white', fontweight='bold')
    ax.set_xlabel('Specificity (%)', fontweight='bold')
    ax.set_ylabel('Sensitivity (%)', fontweight='bold')
    ax.set_title('Sensitivity vs Specificity', fontweight='bold')
    ax.set_xlim([0, 105])
    ax.set_ylim([0, 105])
    ax.grid(True, alpha=0.3)
    ax.plot([0, 100], [0, 100], 'k--', alpha=0.3)
    
    # Plot 3: F1 Score distribution
    ax = axes[1, 0]
    ax.bar(metrics_df['plate'], metrics_df['f1_score'],
           color='#2ecc71', edgecolor='black', linewidth=1.5)
    ax.set_xlabel('Plate Number', fontweight='bold')
    ax.set_ylabel('F1 Score', fontweight='bold')
    ax.set_title('F1 Score by Plate', fontweight='bold')
    ax.set_ylim([0, 1.1])
    ax.axhline(metrics_df['f1_score'].mean(), color='red', 
              linestyle='--', linewidth=2, alpha=0.7, label='Mean')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Confusion matrix totals
    ax = axes[1, 1]
    totals = [
        metrics_df['true_positives'].sum(),
        metrics_df['false_positives'].sum(),
        metrics_df['false_negatives'].sum(),
        metrics_df['true_negatives'].sum()
    ]
    labels = ['True\nPositives', 'False\nPositives', 'False\nNegatives', 'True\nNegatives']
    colors = ['#2ecc71', '#e74c3c', '#e67e22', '#3498db']
    
    bars = ax.bar(labels, totals, color=colors, edgecolor='black', linewidth=2)
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Total Confusion Matrix (All Plates)', fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{int(height)}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/mnt/user-data/outputs/plate_datasets/detection_test_visualizations.png',
                dpi=300, bbox_inches='tight')
    print("✓ Saved: detection_test_visualizations.png")
    
    return fig


def main():
    """Main testing workflow"""
    print("\n" + "="*70)
    print("PLATE DATASET TESTING EXAMPLE")
    print("="*70)
    print("\nThis script demonstrates how to:")
    print("  1. Load plate data and annotations")
    print("  2. Run your detection algorithm")
    print("  3. Compare with ground truth")
    print("  4. Calculate accuracy metrics")
    print("  5. Evaluate across all plates")
    
    # Test on plate 1 as example
    print("\n" + "="*70)
    print("EXAMPLE: Testing on Plate 1")
    print("="*70)
    test_single_plate(1)
    
    # Test all plates
    metrics_df = test_all_plates(10)
    
    # Visualize
    print("\n" + "="*70)
    print("CREATING VISUALIZATIONS")
    print("="*70)
    visualize_results(metrics_df)
    
    print("\n" + "="*70)
    print("TESTING COMPLETE!")
    print("="*70)
    print("\nYour detection algorithm has been tested on 960 wells (10 plates)")
    print("with ground truth annotations. Review the metrics to improve!")
    print("\nNext steps:")
    print("  1. Analyze which categories are hardest to detect")
    print("  2. Tune detection thresholds")
    print("  3. Try different detection methods")
    print("  4. Combine multiple approaches")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
