import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def load_data(csv_file: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    df['is_covert'] = df['is_covert'].astype(bool)
    df['is_detected'] = df['is_detected'].astype(bool)
    return df

def compute_confidence_interval(data, confidence=0.95):
    n = len(data)
    if n == 0:
        return (np.nan, np.nan)
    mean = np.mean(data)
    stderr = stats.sem(data)
    h = stderr * stats.t.ppf((1 + confidence) / 2., n - 1)
    return mean, h

def evaluate_detection(df: pd.DataFrame):
    # Use one row per message ID (grouping chunks)
    grouped = df.groupby('msg_id').agg({
        'msg_len': 'first',
        'is_covert': 'any',
        'is_detected': 'any'
    })

    y_true = grouped['is_covert']
    y_pred = grouped['is_detected']

    TP = ((y_true == True) & (y_pred == True)).sum()
    TN = ((y_true == False) & (y_pred == False)).sum()
    FP = ((y_true == False) & (y_pred == True)).sum()
    FN = ((y_true == True) & (y_pred == False)).sum()

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (TP + TN) / len(grouped)

    print("=== Detection Results ===")
    print(f"True Positives (TP): {TP}")
    print(f"True Negatives (TN): {TN}")
    print(f"False Positives (FP): {FP}")
    print(f"False Negatives (FN): {FN}")
    print()
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1_score:.3f}")
    print(f"Accuracy:  {accuracy:.3f}")
    print()

def benchmark_by_length(df: pd.DataFrame):
    print("=== Detection Accuracy by Message Length ===")
    grouped = df.groupby('msg_id').agg({
        'msg_len': 'first',
        'is_covert': 'any',
        'is_detected': 'any'
    })

    lengths = []
    accuracies = []
    errors = []

    for length in sorted(grouped['msg_len'].unique()):
        subset = grouped[grouped['msg_len'] == length]
        correct = (subset['is_covert'] == subset['is_detected']).astype(int)
        mean, h = compute_confidence_interval(correct)
        print(f"Length {length:>3}: Accuracy = {mean:.3f} ± {h:.3f} (95% CI), N = {len(subset)}")

        lengths.append(length)
        accuracies.append(mean)
        errors.append(h)

    # Plot
    plt.figure(figsize=(8, 5))
    plt.errorbar(lengths, accuracies, yerr=errors, fmt='o-', capsize=5, linewidth=2, label='Accuracy ± 95% CI')
    plt.title("Detection Accuracy vs Message Length")
    plt.xlabel("Message Length")
    plt.ylabel("Detection Accuracy")
    plt.ylim(0, 1.05)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("detection_accuracy_vs_length.png")
    plt.show()

def benchmark_by_type(df: pd.DataFrame):
    print("\n=== Detection Breakdown by Message Type ===")
    grouped = df.groupby('msg_id').agg({
        'is_covert': 'any',
        'is_detected': 'any'
    })

    for label, name in [(True, "Covert"), (False, "Visible")]:
        subset = grouped[grouped['is_covert'] == label]
        correct = (subset['is_covert'] == subset['is_detected']).astype(int)
        mean, h = compute_confidence_interval(correct)
        print(f"{name:<7}: Accuracy = {mean:.3f} ± {h:.3f} (95% CI), N = {len(subset)}")

def main():
    df = load_data("results.csv")
    evaluate_detection(df)
    benchmark_by_length(df)
    benchmark_by_type(df)

if __name__ == "__main__":
    main()
