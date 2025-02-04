from pathlib import Path
import pandas as pd
import argparse

def compute_mean_errors(errors_df, is_significant):
    """Computes mean number of errors over radiologists.
    
    Args:
        errors_df: DataFrame containing radiologist annotations
        is_significant: Whether to look at clinically significant or insignificant errors
    
    Returns:
        DataFrame with mean error counts per study and candidate type
    """
    errors_df = errors_df.query("clinically_significant == @is_significant")
    mean_errors = errors_df.groupby(['study_number', 'candidate_type', 'error_category']).mean()
    mean_errors = mean_errors.drop(columns=['rater_index', 'clinically_significant'])
    mean_errors = mean_errors.reset_index()
    
    mean_errors = mean_errors.groupby(['study_number', 'candidate_type']).sum()
    mean_errors = mean_errors.drop(columns=['error_category'])
    return mean_errors.reset_index()

def preprocess(input_path, output_path):
    """Preprocess the radiologist error annotation dataset.
    
    Args:
        input_path: Path to the dataset directory containing CSV files
        output_path: Path where the processed CSV will be saved
    
    Returns:
        DataFrame containing the processed data
    """
    input_path = Path(input_path)
    
    # Read input files
    study_reports_df = pd.read_csv(input_path / "50_samples_gt_and_candidates.csv")
    errors_df = pd.read_csv(input_path / "6_valid_raters_per_rater_error_categories.csv")
    
    # Calculate mean errors
    sig_mean_errors = compute_mean_errors(errors_df, is_significant=True)
    insig_mean_errors = compute_mean_errors(errors_df, is_significant=False)
    
    # Merge significant and insignificant errors
    total_mean_errors = pd.merge(
        sig_mean_errors.rename(columns={'num_errors': 'mean_sig_errors'}),
        insig_mean_errors.rename(columns={'num_errors': 'mean_insig_errors'}),
        on=['study_number', 'candidate_type']
    )
    total_mean_errors['mean_total_errors'] = (
        total_mean_errors['mean_sig_errors'] + total_mean_errors['mean_insig_errors']
    )
    
    # Create final dataset
    dataset = []
    for _, row in total_mean_errors.iterrows():
        dataset.append({
            "study_id": study_reports_df.iloc[row['study_number']]['study_id'],
            "study_number": row['study_number'],
            "candidate_type": row['candidate_type'],
            "gt_report": study_reports_df.iloc[row['study_number']]['gt_report'],
            "pred_report": study_reports_df.iloc[row['study_number']][row['candidate_type']],
            "mean_sig_errors": row['mean_sig_errors'],
            "mean_insig_errors": row['mean_insig_errors'],
            "mean_total_errors": row['mean_total_errors']
        })
    
    # Convert to DataFrame and save
    output_df = pd.DataFrame(dataset)
    if output_path:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(output_path / "rexval_preprocessed.csv", index=False)
        print(f"Preprocessed data saved to \"{output_path / 'rexval_preprocessed.csv'}\".")
    
    return output_df

def main():
    parser = argparse.ArgumentParser(
        description='Preprocess radiologist error annotation dataset. The result csv will be saved in the output_path with the name "rexval_preprocessed.csv".'
    )
    parser.add_argument(
        '-i', '--input_path',
        required=True,
        help='Path to the dataset directory containing CSV files'
    )
    parser.add_argument(
        '-o', '--output_path',
        required=True,
        help='Path where the processed CSV will be saved'
    )
    
    args = parser.parse_args()
    preprocess(args.input_path, args.output_path)

if __name__ == '__main__':
    main()