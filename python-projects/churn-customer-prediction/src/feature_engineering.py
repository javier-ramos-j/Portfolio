import pandas as pd
import numpy as np

def run_feature_engineering(df):
    # Ternure-based features.
    df['tenure_years'] = (df['tenure'] / 12).round(2)

    # Binary feature for long-term customers (tenure >= 2 years).
    df['long_term_customer'] = (df['tenure_years'] >= 2).astype(int)

    # Count of services subscribed.
    services = ['PhoneService','MultipleLines', 'OnlineSecurity','OnlineBackup','DeviceProtection',
                'TechSupport','StreamingTV','StreamingMovies']

    df['total_service_count'] = df[services].sum(axis=1)

    # Ratio of MonthlyCharges to TotalCharges.
    df['charges_ratio'] = (df['MonthlyCharges']/df['TotalCharges']).round(2)

    df['average_monthly_charges'] = (df['TotalCharges'] / df['tenure']).round(2)
    df['average_monthly_charges'] = df['average_monthly_charges'].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Encoding categorical variables.
    df = pd.get_dummies(df, columns=['Contract', 'PaymentMethod', 'InternetService'], drop_first=True)
    df['gender'] = df['gender'].map({'Male': 1, 'Female': 0})

    # Saving the engineered dataset.
    df.to_csv('../data/processed/engineered_churn_data.csv', index=False)
    return df