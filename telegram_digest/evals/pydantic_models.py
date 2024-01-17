import matplotlib.pyplot as plt
import logging
import pandas as pd
import shap
from abc import ABC, abstractmethod
from pydantic import BaseModel, validator
import xgboost as xgb
from sklearn.model_selection import train_test_split
from plotly.subplots import make_subplots

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split
from pygam import LinearGAM, s
import plotly.graph_objs as go
from typing import ClassVar, Any


class Explainer(BaseModel, ABC):
    df: pd.DataFrame
    independent_vars: list[str]
    dependent_var: str
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)
    model: Any = None  # cls.train_model will set this
    metrics: dict = None  # cls.train_model may set this
    explainer: Any = None  # cls.explain_and_plot may set this

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types


    @validator("dependent_var")
    def dependent_var_must_be_in_df(cls, v, values):
        if "df" in values and v not in values["df"].columns:
            raise ValueError(f"dependent_var '{v}' not found in DataFrame columns")
        return v

    @abstractmethod
    def train_model(self) -> 'Explainer':
        """Method to train a model; must be implemented by subclasses."""
        pass

    def explain_and_plot(self, filepath=None) -> 'Explainer':
        """Use the trained model to create explainations and plots"""
        pass


class LinearGAMExplainer(Explainer):
    def train_model(self) -> 'LinearGAMExplainer':
        """
        Fit a Generalized Additive Model to the DataFrame with a spline for each independent variable.
        """
        self.logger.info("Fitting LinearGAM model")
        independent_vars = self.independent_vars

        # Preparing the data
        X = self.df[independent_vars].values
        y = self.df[self.dependent_var].values

        # Building the model with a spline for each independent variable
        # Use '+' to concatenate terms into a TermList
        terms = s(0)
        for i in range(1, len(independent_vars)):
            terms += s(i)
        gam = LinearGAM(terms).fit(X, y)
        gam.feature_names_ = independent_vars

        # save to instance
        self.model = gam

        return self

    def explain_and_plot(self, filepath=None) -> 'LinearGAMExplainer':
        """
        Create a grid of partial dependence plots for each independent variable in the model.
        """
        gam = self.model
        independent_vars = self.independent_vars

        # Print the summary
        print(gam.summary())

        # Plots
        num_vars = len(independent_vars)
        cols = 3  # Adjust the number of columns as per preference
        rows = (num_vars + cols - 1) // cols  # Calculate required number of rows

        fig = make_subplots(
            rows=rows,
            cols=cols,
            # showlegend=False,
            subplot_titles=[f"{i}-{var}" for i, var in enumerate(independent_vars)],
        )

        for i, var in enumerate(independent_vars, start=1):
            XX = gam.generate_X_grid(term=i - 1)
            pdep, confi = gam.partial_dependence(term=i - 1, X=XX, width=0.95)

            row = (i - 1) // cols + 1
            col = (i - 1) % cols + 1

            # Create a plot for each variable
            trace = go.Scatter(x=XX[:, i - 1], y=pdep, mode="lines", name=f"{i}-{var}")
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

        fig.update_layout(
            height=400 * rows, title_text="LinearGAM: Partial Dependence Plots"
        )

        if filepath:
            fig.write_html(filepath)
        fig.show()

        return self


class XGBoostExplainer(Explainer):
    def train_model(self) -> 'XGBoostExplainer':
        """
        Trains an XGBoost model, evaluates it using standard metrics and checks for overfitting.
        """
        self.logger.info("Fitting XGBoost model")
        X = self.df[self.independent_vars]
        y = self.df[self.dependent_var]

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Define the model
        model = xgb.XGBRegressor(
            n_estimators=100,  # Number of trees
            max_depth=4,  # Maximum depth of trees to prevent over-complex models
            learning_rate=0.1,  # Learning rate
            reg_alpha=0.1,  # L1 regularization
            reg_lambda=0.1,  # L2 regularization
            subsample=0.8,  # Subsample ratio of the training instances
            colsample_bytree=0.8,  # Subsample ratio of columns
        )

        # Train the model
        model.fit(
            X_train,
            y_train,
            early_stopping_rounds=10,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        # Predictions on test and training sets
        predictions_test = model.predict(X_test)
        predictions_train = model.predict(X_train)

        # Evaluation metrics for test and training sets
        metrics_test = {
            "R2 Score": r2_score(y_test, predictions_test),
            "MSE": mean_squared_error(y_test, predictions_test),
            "MAE": mean_absolute_error(y_test, predictions_test),
        }

        metrics_train = {
            "R2 Score": r2_score(y_train, predictions_train),
            "MSE": mean_squared_error(y_train, predictions_train),
            "MAE": mean_absolute_error(y_train, predictions_train),
        }

        # Check for overfitting
        # You can adjust the thresholds as per your requirement
        if metrics_train["R2 Score"] - metrics_test["R2 Score"] > 0.1:
            logging.warning(
                "Warning: Possible overfitting detected. R2 Score on training set significantly higher than on test set."
            )

        # Check for overfitting using ratios
        for metric_name in ["MAE", "MSE"]:
            if metrics_test[metric_name] > 1.5 * metrics_train[metric_name]:
                logging.warning(
                    f"Warning: Possible overfitting detected for {metric_name}. {metrics_test[metric_name]=} , {metrics_train[metric_name]=}"
                )

        # save to instance
        self.model = model
        self.metrics = dict(
            metrics_test=metrics_test,
            metrics_train=metrics_train,
        )

        return self

    def explain_and_plot(self, filepath=None) -> 'XGBoostExplainer':
        """
        Performs SHAP analysis on the given XGBoost model and feature data.
        """
        feature_names = self.independent_vars
        X = self.df[feature_names]

        # SHAP values and plot
        explainer = shap.Explainer(self.model)
        shap_values = explainer(X)
        shap.summary_plot(shap_values, X, feature_names=feature_names)
        # Save the plot if a filepath is provided
        if filepath:
            plt.savefig(filepath)

        # Show the plot graphically
        plt.show()

        self.explainer = explainer
    
        return self
