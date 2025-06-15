import pandas as pd
import numpy as np
from scipy import stats

def mean_confidence_interval(data, confidence=0.95):
    a = np.array(data)
    n = len(a)
    if n == 0:
        return 0, 0, 0
    m = np.mean(a)
    se = stats.sem(a)
    h = se * stats.t.ppf((1 + confidence) / 2., n-1) if n > 1 else 0
    return m, m-h, m+h

def summarize_results(normal_csv, mitigation_csv):
    # Load normal results
    df_norm = pd.read_csv(normal_csv)
    num_covert_messages = df_norm['is_covert'].sum()

    # Load mitigation results
    df_mit = pd.read_csv(mitigation_csv)
    num_passed_messages = df_mit['is_covert'].sum()

    total_mit = len(df_mit)
    covert_mit = df_mit['is_covert'].sum()
    noncovert_mit = total_mit - covert_mit

    covert_array = df_mit['is_covert'].astype(int)
    mean_cov, ci_low_cov, ci_high_cov = mean_confidence_interval(covert_array)
    print(f"Total messages: {total_mit}")
    print(f"Covert messages: {covert_mit}")
    print(f"Non-covert messages: {noncovert_mit}")
    print(f"Covert message rate (mean): {mean_cov:.3f}")
    print(f"Covert message rate 95% CI: [{ci_low_cov:.3f}, {ci_high_cov:.3f}]")
    print()

    # Channel capacity proxy: how many covert messages got through
    print("Channel Capacity Proxy:")
    print(f"Covert messages passed: {num_passed_messages}/{num_covert_messages} ({df_mit["is_covert"].sum()/df_norm["is_covert"].sum():.2%})")


if __name__ == "__main__":
    summarize_results("results.csv", "mitigation_results.csv")