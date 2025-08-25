# Customer Churn Prediction Pipeline

Machine learning pipeline designed to predict customer churn using historical account and usage data, retrieved from [Telco Customer Churn Dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn"). This project performs data cleaning, exploratory data analysis, feature engineering, logistic regression and random forest. 



## 🔧 Key Topics and Tools

* **Data cleaning and preprocessing**: use of `pandas` and `numpy`to handle missing values and prepare data for modeling.
* **Exploratory Data Analysis (EDA)**: use of `seaborn` and `matplotlib` to understand feature distributions and their relationship.
* **Feature Engineering**: creation of new features, encoding of categorical variables, and scaling of numerical values to improve model performance.
* **Modeling**: training and evaluation of Logistic Regression and Random Forest using `scikit-learn`.
* **Model Evaluation**: assessment of model accuracy, precision, recall, and AUC to compare performance and ensure robustness

Necessary libraries, please run `requirements.txt`.


## 📍Workflow
1. **Load & Clean Data**: start ETL process of the dataset.
2. **EDA**: visualize churn distribution across key customer features + identify important trends and correlations.
3. **Feature Engineering**: encode categorical variables using one-hot encoding.
4. **Model Training & Selection**: train and compare Logistic Regression and Random Forest.
5. **Model Evaluation**: evaluate using confusion matrix, ROC curve, and classification metrics.



