import os
import sys
import json
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report, confusion_matrix

def train_and_evaluate(root_dir):
    print("=" * 60)
    print("PARTS D, E, F: XGBOOST MODEL TRAINING, EVALUATION & VERSIONING")
    print("=" * 60)
    
    t0 = time.time()
    feature_path = os.path.join(root_dir, 'solexs_feature_matrix.parquet')
    cat_path = os.path.join(root_dir, 'solexs_flare_candidate_catalog.csv')
    
    if not os.path.exists(feature_path):
        raise FileNotFoundError(f"Feature matrix missing: {feature_path}. Run feature_engineering.py first!")
        
    print(f"Loading feature matrix from {feature_path}...")
    df = pd.read_parquet(feature_path)
    df['utc_time'] = pd.to_datetime(df['utc_time'], utc=True)
    
    # Filter valid evaluation rows (rows not bridging data gaps > 300s)
    df = df[df['valid_forecast_window']].reset_index(drop=True)
    print(f"Loaded {len(df):,} valid evaluation rows.")
    
    # Define feature column list (exclude metadata & target columns)
    exclude_cols = {
        'TSTART', 'utc_time', 'date_str', 'segment_id', 'source_file',
        'label_flare_imminent', 'valid_forecast_window'
    }
    
    # Exclude reserved HEL1OS placeholders with NaN values during training
    feature_cols = [c for c in df.columns if c not in exclude_cols and not c.startswith('hel1os_')]
    print(f"\nFeature Set ({len(feature_cols)} features):")
    for f_name in feature_cols:
        print(f"  - {f_name}")
        
    # -------------------------------------------------------------
    # Part D: Chronological Train / Test Split
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print("CHRONOLOGICAL TRAIN / TEST SPLIT")
    print("-" * 60)
    
    all_dates = sorted(df['date_str'].unique())
    n_total_days = len(all_dates)
    
    # Chronological 80/20 split on calendar dates
    split_idx = int(n_total_days * 0.80)
    train_dates = all_dates[:split_idx]
    test_dates = all_dates[split_idx:]
    
    train_mask = df['date_str'].isin(train_dates)
    test_mask = df['date_str'].isin(test_dates)
    
    train_df = df[train_mask].reset_index(drop=True)
    test_df = df[test_mask].reset_index(drop=True)
    
    print(f"Total Calendar Days: {n_total_days}")
    print(f"Train Date Range:   {train_dates[0]} to {train_dates[-1]} ({len(train_dates)} days)")
    print(f"Test Date Range:    {test_dates[0]} to {test_dates[-1]} ({len(test_dates)} days - FIXED HOLDOUT SET)")
    
    X_train = train_df[feature_cols]
    y_train = train_df['label_flare_imminent']
    
    X_test = test_df[feature_cols]
    y_test = test_df['label_flare_imminent']
    
    train_pos = (y_train == 1).sum()
    train_neg = (y_train == 0).sum()
    test_pos = (y_test == 1).sum()
    test_neg = (y_test == 0).sum()
    
    print(f"\nTrain Set Rows: {len(train_df):,} | Positives (1): {train_pos:,} ({train_pos/len(train_df)*100:.2f}%) | Negatives (0): {train_neg:,}")
    print(f"Test Set Rows:  {len(test_df):,} | Positives (1): {test_pos:,} ({test_pos/len(test_df)*100:.2f}%) | Negatives (0): {test_neg:,}")
    
    scale_pos_weight = train_neg / max(1, train_pos)
    print(f"Calculated scale_pos_weight for XGBoost: {scale_pos_weight:.2f}")
    
    # Model Training
    print("\nTraining XGBoost Classifier (XGBClassifier)...")
    model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    print("Model training complete!")
    
    # -------------------------------------------------------------
    # Part E: Evaluation on Held-Out Test Set
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PART E: EVALUATION ON HELD-OUT TEST SET ONLY")
    print("=" * 60)
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    test_df['pred_label'] = y_pred
    test_df['pred_prob'] = y_prob
    
    prec = precision_score(y_test, y_pred, pos_label=1)
    rec = recall_score(y_test, y_pred, pos_label=1)
    f1 = f1_score(y_test, y_pred, pos_label=1)
    
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    n_test_days = len(test_dates)
    fp_sec_per_day = fp / float(n_test_days)
    
    # Count contiguous false positive episodes (false alarm alert events)
    is_fp = (y_test == 0) & (y_pred == 1)
    fp_episodes = int((~is_fp).cumsum()[is_fp].nunique())
    fp_episodes_per_day = fp_episodes / float(n_test_days)
    
    print(f"\nConfusion Matrix on Test Set:")
    print(f"  True Negatives (TN):  {tn:,}")
    print(f"  False Positives (FP): {fp:,} (False Alarm Seconds)")
    print(f"  False Negatives (FN): {fn:,} (Missed Alert Seconds)")
    print(f"  True Positives (TP):  {tp:,} (Correct Alert Seconds)")
    
    print(f"\nPositive Class (Flare Imminent within 15m) Performance:")
    print(f"  Precision:                 {prec:.4f} ({prec*100:.2f}%)")
    print(f"  Recall:                    {rec:.4f} ({rec*100:.2f}%)")
    print(f"  F1 Score:                  {f1:.4f}")
    print(f"  False Alarm Rate (sec/day): {fp_sec_per_day:.1f} false positive seconds / day")
    print(f"  False Alarm Rate (ep/day):  {fp_episodes_per_day:.1f} discrete false alarm episodes / day")
    
    # Calculate Lead Time before Peak for correctly predicted flare events in Test Set
    lead_times = []
    if os.path.exists(cat_path):
        cat = pd.read_csv(cat_path)
        cat['start_time'] = pd.to_datetime(cat['start_time'], utc=True)
        cat['peak_time'] = pd.to_datetime(cat['peak_time'], utc=True)
        
        # Test period events
        test_start_utc = test_df['utc_time'].min()
        test_end_utc = test_df['utc_time'].max()
        test_events = cat[(cat['start_time'] >= test_start_utc) & (cat['start_time'] <= test_end_utc)]
        
        # Check alerts (y_pred == 1) prior to each test event peak
        alerts_df = test_df[test_df['pred_label'] == 1]
        
        for idx, event in test_events.iterrows():
            e_peak = event['peak_time']
            window_start = e_peak - pd.Timedelta(minutes=15)
            prior_alerts = alerts_df[(alerts_df['utc_time'] >= window_start) & (alerts_df['utc_time'] <= e_peak)]
            if len(prior_alerts) > 0:
                first_alert = prior_alerts['utc_time'].min()
                lt_min = (e_peak - first_alert).total_seconds() / 60.0
                lead_times.append(lt_min)
                
    mean_lead_time = float(np.mean(lead_times)) if lead_times else 0.0
    print(f"  Mean Actual Lead Time:     {mean_lead_time:.1f} minutes before flare peak")
    
    # Render Feature Importance Plot
    print("\nRendering Feature Importance plot...")
    plt.figure(figsize=(10, 8), dpi=150)
    # Gain importance
    importance_scores = model.feature_importances_
    sorted_idx = np.argsort(importance_scores)[::-1][:15]
    top_features = [feature_cols[i] for i in sorted_idx]
    top_scores = importance_scores[sorted_idx]
    
    plt.barh(top_features[::-1], top_scores[::-1], color='#1f77b4', edgecolor='black', linewidth=0.5)
    plt.xlabel("Importance (Gain / Weight)", fontsize=11, labelpad=8)
    plt.title("XGBoost Flare Forecasting — Top 15 Feature Importances", fontsize=13, fontweight='bold', pad=10)
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    feat_img_path = os.path.join(root_dir, 'solexs_feature_importance.png')
    plt.savefig(feat_img_path)
    plt.close()
    print(f"Saved: {feat_img_path}")
    
    # -------------------------------------------------------------
    # Part F: Model Versioning & Metadata Export
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PART F: MODEL VERSIONING & METADATA EXPORT")
    print("=" * 60)
    
    min_date_str = df['utc_time'].min().strftime('%Y%m%d')
    max_date_str = df['utc_time'].max().strftime('%Y%m%d')
    version_tag = f"v1_{min_date_str}_{max_date_str}"
    
    model_filename = f"solexs_flare_model_{version_tag}.json"
    meta_filename = f"solexs_flare_model_{version_tag}_metadata.json"
    
    model_save_path = os.path.join(root_dir, model_filename)
    meta_save_path = os.path.join(root_dir, meta_filename)
    
    print(f"Saving trained XGBoost model to {model_save_path}...")
    model.save_model(model_save_path)
    
    metadata = {
        'model_version': version_tag,
        'created_at_utc': pd.Timestamp.now('UTC').strftime('%Y-%m-%d %H:%M:%S UTC'),
        'instrument': 'SoLEXS SDD2 (Aditya-L1)',
        'full_date_range': f"{all_dates[0]} to {all_dates[-1]}",
        'training_date_range': f"{train_dates[0]} to {train_dates[-1]}",
        'test_date_range': f"{test_dates[0]} to {test_dates[-1]}",
        'forecast_horizon_minutes': 15,
        'dataset_counts': {
            'train_total_rows': int(len(train_df)),
            'train_positive_examples': int(train_pos),
            'train_negative_examples': int(train_neg),
            'test_total_rows': int(len(test_df)),
            'test_positive_examples': int(test_pos),
            'test_negative_examples': int(test_neg)
        },
        'evaluation_metrics': {
            'precision': float(round(prec, 4)),
            'recall': float(round(rec, 4)),
            'f1_score': float(round(f1, 4)),
            'false_positives_seconds': int(fp),
            'false_alarm_seconds_per_day': float(round(fp_sec_per_day, 1)),
            'false_alarm_episodes_per_day': float(round(fp_episodes_per_day, 1)),
            'mean_lead_time_minutes': float(round(mean_lead_time, 2))
        },
        'features_used': feature_cols
    }
    
    with open(meta_save_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Saved metadata JSON to {meta_save_path}...")
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY REPORT & MODEL BENCHMARK")
    print("=" * 80)
    print(f"Model File Saved:             {model_filename}")
    print(f"Metadata File Saved:          {meta_filename}")
    print(f"Train Date Period:            {train_dates[0]} to {train_dates[-1]} ({len(train_dates)} days)")
    print(f"Test Date Period (Holdout):   {test_dates[0]} to {test_dates[-1]} ({len(test_dates)} days)")
    print(f"Test Precision:               {prec*100:.2f}%")
    print(f"Test Recall:                  {rec*100:.2f}%")
    print(f"Test F1 Score:                {f1:.4f}")
    print(f"False Alarm Rate (episodes):  {fp_episodes_per_day:.1f} discrete false alarm episodes / day")
    print(f"Mean Early Lead Time:         {mean_lead_time:.1f} minutes before flare peak")
    print("=" * 80)
    print("CONFIRMATION: Successfully trained, evaluated, versioned, and exported SoLEXS flare forecasting model!")
    print("=" * 80)

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.abspath(__file__)) if len(sys.argv) < 2 else sys.argv[1]
    train_and_evaluate(root_dir)
