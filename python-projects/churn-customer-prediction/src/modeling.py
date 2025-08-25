import pandas as pd
import joblib  
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

def run_modeling(df):
    # Define features and target variable
    x = df.drop(columns=["Churn","customerID","tenure_group"]) # features
    y = df["Churn"] # target variable

    x_train, x_test, y_train, y_test = train_test_split(
        x,y, test_size=0.2, random_state=42, stratify=y
        )

    # Train Logistic Regression model
    log_reg = LogisticRegression(max_iter=1000, random_state=42) 
    log_reg.fit(x_train, y_train)

    # Train Random Forest model
    rf_clf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_clf.fit(x_train, y_train)

    def evaluate_model(model, x_test, y_test):
        y_pred = model.predict(x_test)
        y_proba = model.predict_proba(x_test)[:, 1] # Probability estimates for the positive class, [:,1] means we take the second column (positive class)

        print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred):.4f}")
        print(f"Recall:    {recall_score(y_test, y_pred):.4f}")
        print(f"F1-score:  {f1_score(y_test, y_pred):.4f}")
        print(f"ROC AUC:   {roc_auc_score(y_test, y_proba):.4f}")

    # Evaluate Logistic Regression model
    print("Logistic Regression Model Evaluation:")
    evaluate_model(log_reg, x_test, y_test)
    # Evaluate Random Forest model
    print("\nRandom Forest Model Evaluation:")
    evaluate_model(rf_clf, x_test, y_test)

    joblib.dump(log_reg, "../models/logistic_regression_model.pkl")
    joblib.dump(rf_clf, "../models/random_forest_model.pkl")
    print("Models exported successfully.")
    return log_reg, rf_clf
