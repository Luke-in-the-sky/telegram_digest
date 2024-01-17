import pandas as pd
import re
import pickle
from pygam import LinearGAM, s  # pip install pygam
import plotly.graph_objs as go
from plotly.subplots import make_subplots


def extract_dicts_from_log(file_path):
    pattern = r"INFO \|root\| Output from Run: ({.*})"
    dicts = []

    with open(file_path, "r") as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                # Convert string representation of dict to actual dict
                dict_str = match.group(1)
                dict_obj = eval(
                    dict_str
                )  # Using eval() here since the string format matches Python dict syntax
                dicts.append(dict_obj)

    return dicts


def fit_gam(df, independent_vars, dependent_var):
    """
    Fit a Generalized Additive Model to the DataFrame with a spline for each independent variable.

    Parameters:
    df (DataFrame): The DataFrame containing the data.
    independent_vars (list): List of column names for independent variables.
    dependent_var (str): Column name for the dependent (metric) variable.

    Returns:
    GAM: Fitted GAM model.
    """
    # Preparing the data
    X = df[independent_vars].values
    y = df[dependent_var].values

    # Building the model with a spline for each independent variable
    # Use '+' to concatenate terms into a TermList
    terms = s(0)
    for i in range(1, len(independent_vars)):
        terms += s(i)
    gam = LinearGAM(terms).fit(X, y)
    gam.feature_names_ = independent_vars

    return gam


def plot_partial_dependence(gam, df, independent_vars, filepath=None):
    """
    Create a grid of partial dependence plots for each independent variable in the model.

    Parameters:
    gam (GAM): Fitted GAM model.
    df (DataFrame): The DataFrame used to fit the model.
    independent_vars (list): List of independent variable names.
    """
    num_vars = len(independent_vars)
    cols = 2  # Adjust the number of columns as per preference
    rows = (num_vars + cols - 1) // cols  # Calculate required number of rows

    fig = make_subplots(rows=rows, cols=cols, subplot_titles=independent_vars)

    for i, var in enumerate(independent_vars, start=1):
        XX = gam.generate_X_grid(term=i - 1)
        pdep, confi = gam.partial_dependence(term=i - 1, X=XX, width=0.95)

        row = (i - 1) // cols + 1
        col = (i - 1) % cols + 1

        # Create a plot for each variable
        trace = go.Scatter(
            x=XX[:, i - 1], y=pdep, mode="lines", name=f"Partial Dependence for {var}"
        )
        fig.add_trace(trace, row=row, col=col)

        # Add confidence interval
        fig.add_trace(
            go.Scatter(
                x=XX[:, i - 1],
                y=confi[:, 0],
                mode="lines",
                showlegend=False,
                line=dict(color="red", dash="dash"),
            ),
            row=row,
            col=col,
        )
        fig.add_trace(
            go.Scatter(
                x=XX[:, i - 1],
                y=confi[:, 1],
                mode="lines",
                showlegend=False,
                line=dict(color="red", dash="dash"),
            ),
            row=row,
            col=col,
        )

    fig.update_layout(height=400 * rows, title_text="Partial Dependence Plots")

    if filepath:
        fig.write_html(filepath)
        print(f"Plot saved to {filepath}")
    else:
        fig.show()


def main():
    log_file_path = "logfile.log"
    output_file_path = "df_sweep.pkl"

    # Extract dictionaries from log file
    extracted_dicts = extract_dicts_from_log(log_file_path)

    # Convert to DataFrame
    df = pd.DataFrame(extracted_dicts)
    df.query("silhouette_coefficient > -1", inplace=True)

    # Save DataFrame to pickle file
    with open(output_file_path, "wb") as file:
        pickle.dump(df, file)

    print(f"DataFrame saved to {output_file_path}")

    # Example usage of fit_gam
    independent_vars = [
        "hdbscan_alpha",
        "hdbscan_cluster_selection_epsilon",
        "hdbscan_min_cluster_size",
        "hdbscan_min_samples",
        "umap_min_dist",
        "umap_n_components",
        "umap_n_neighbors",
        "render_msg_upstream",
        "include_sender_name",
        "join_messages_n",
        "join_messages_overlap",
        "num_of_samples",
    ]
    gam_model = fit_gam(df, independent_vars, dependent_var="silhouette_coefficient")

    # You can now use gam_model for predictions, plotting, etc.
    print(gam_model.summary())

    # Plotting Partial Dependence
    plot_partial_dependence(gam_model, df, independent_vars)


if __name__ == "__main__":
    main()
