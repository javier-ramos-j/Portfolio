from data_preprocessing import run_preprocess_data
from eda import run_eda
from feature_engineering import run_feature_engineering
from modeling import run_modeling
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting the churn customer prediction pipeline...")


logging.info("Running data preprocessing...")
df = run_preprocess_data()

logging.info("Running EDA...")
run_eda(df)

logging.info("Running feature engineering...")
df = run_feature_engineering(df)

logging.info("Running modeling...")
log_reg, rf_clf = run_modeling(df)

logging.info("Models trained and saved successfully.")
logging.info("Churn customer prediction pipeline completed successfully.")
