import pandas as pd
import numpy as np

def run_preprocess_data():
    # Load raw data, as a single column, then split into multiple columns. Specify no header in raw data.
    df_raw = pd.read_csv('../data/raw/churn_data.csv', header=None)
    df = df_raw[0].str.split(",", expand=True)

    # Specify the header names as the first row of the dataframe
    df.columns = df.iloc[0]

    # Drop the first row as it is now the header
    df = df.drop(df.index[0]).reset_index(drop=True)

    print("DataFrame shape:", df.shape)
    print("DataFrame columns:", df.columns.tolist())


    # Convert appropriate columns to numeric types
    binary_columns = ['Partner', 'Dependents', 'PhoneService', 'PaperlessBilling',
                    'Churn', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                    'TechSupport', 'StreamingTV', 'StreamingMovies', 'MultipleLines']

    df[binary_columns] = df[binary_columns].replace({'Yes': 1, 'No': 0, 'No internet service': 0, 'No phone service': 0})

    # Convert to appropiate data types
    df['SeniorCitizen'] = df['SeniorCitizen'].astype(int)
    df['tenure'] = pd.to_numeric(df['tenure'], errors='coerce')
    df['MonthlyCharges'] = pd.to_numeric(df['MonthlyCharges'], errors='coerce')
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    # Drop rows with NA or inf values
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    # Now, convert categorical columns to string type
    df = df.astype({
        'customerID': 'string',
        'gender': 'string',
        'InternetService': 'string',
        'Contract': 'string',
        'PaymentMethod': 'string',
    })

    # For latter use, we will add a tenure_group column to categorize tenure into groups for better analysis
    df['tenure_group'] = pd.cut(df['tenure'], bins=[0, 12, 24, 48, 60, np.inf], labels=['0-12', '13-24', '25-48', '49-60', '60+'])

    # Display columns and their data types
    print(df.info())

    # Save the cleaned dataframe to a new CSV file
    df.to_csv('../data/processed/cleaned_churn_data.csv', index=False) 
    return df