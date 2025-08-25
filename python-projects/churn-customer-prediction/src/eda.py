import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages 

def run_eda(df):
    #Class distribution of target variable
    print("Class distribution of target variable 'Churn':", df['Churn'].value_counts(),"\n")
    print("Percentage of churned customers:", df['Churn'].value_counts(normalize=True).map(lambda x: f"{x:.2%}"),"\n")

    #Summary statistics
    print("Summary statistics of numerical columns:\n", df.describe())
    print("Summary statistics of categorical columns:\n", df.describe(include=['object']))

    #Visualize class imbalance
    sns.countplot(x='Churn', data=df)
    plt.title('Churn Distribution')
    plt.show()
    plt.close()

    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    print("Categorical columns:", categorical_cols,"\n")

    """
    As it is a categorical variable, we will display the distribution of churn by categorical columns.
    For numeric columns, it is more common to use boxplots or violin plotsto visualize the distribution 
    of churn across different numeric values.
    """

    # Churn by category
    with PdfPages("../reports/report_categorical.pdf") as pdf:
        for col in categorical_cols:
            if col != 'customerID':
                plt.figure(figsize=(10,5))
                sns.countplot(x=col, hue='Churn', data=df)
                plt.title(f'Churn by {col}')
                plt.xticks(rotation=45) 
                plt.tight_layout()
                pdf.savefig(plt.gcf())  # Save each plot to a PDF file
                plt.show()
                plt.close()

    """
    Churn by category explanation.
    For each categorical column, we create a count plot that shows the distribution of churned and non-churned customers.
    The x-axis represents the categories of the column, while the y-axis shows the count of customers in each category.
    The hue parameter is set to 'Churn', which allows us to see how churn varies across different categories.
    This helps us identify which categories have a higher proportion of churned customers, providing insights into customer 
    behavior and potential factors contributing to churn.

    plt.xticks(rotation=45) is used to rotate the x-axis labels for better readability, especially if the category names are long.
    plt.tight_layout() ensures that the plot elements fit well within the figure area, preventing overlap.
    """

    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()

    # Churn by numerical values
    with PdfPages("../reports/report_numerical.pdf") as pdf:
        for col in numerical_cols:
            if col != 'Churn':
                plt.figure(figsize=(10,5))
                sns.boxplot(x='Churn', y=col, data=df)
                plt.title(f'{col} by Churn')
                plt.tight_layout()
                pdf.savefig(plt.gcf())
                plt.show()
                plt.close()

    # KDE plots for numerical columns
    with PdfPages("../reports/report_numerical_kde.pdf") as pdf:
        for col in numerical_cols:
            if col != 'Churn':
                plt.figure(figsize=(10,5))
                sns.kdeplot(hue='Churn', x=col, data=df, common_norm=False)
                plt.title(f'Distribution of {col} by Churn')
                plt.tight_layout()
                pdf.savefig(plt.gcf())
                plt.show()
                plt.close()

    # Correlation heatmap
    numeric_df = df.select_dtypes(include=['number'])
    corr = numeric_df.corr()
    with PdfPages("../reports/report_heatmap.pdf") as pdf:
        plt.figure(figsize=(12,10))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', square=True)
        plt.title('Correlation Heatmap')
        pdf.savefig(plt.gcf())
        plt.show()
        plt.close()