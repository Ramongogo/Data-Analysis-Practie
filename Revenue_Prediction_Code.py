#Importing data and required packages
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor,AdaBoostRegressor, StackingRegressor
from sklearn.svm import SVR
from sklearn.linear_model import LinearRegression, Ridge,Lasso
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split,GridSearchCV,cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from catboost import CatBoostRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
import optuna
import scipy.stats as stats

data = pd.read_csv("C:/Users/USER/Downloads/data/Restaurant_revenue (1).csv", encoding = 'utf8')
df = pd.DataFrame(data)
pd.set_option('display.max_columns',None)
print(df.head())
#Checking missing value
print(df.isnull().sum())

#Removing outliers
dummies = pd.get_dummies(df['Cuisine_Type'] , drop_first=False).astype(int)
df = pd.concat([df, dummies], axis=1)
df = df.drop(['Cuisine_Type'], axis=1)
for i in range(len(df.columns)):
    Q1 = np.percentile(df.iloc[:,i], 25, method = 'midpoint')
    Q3 = np.percentile(df.iloc[:,i], 75, method = 'midpoint')
    IQR = Q3 - Q1
    lower = Q1 - 1.5*IQR
    upper = Q3 + 1.5*IQR
    outliers = (df.iloc[:,i] > upper) | (df.iloc[:,i] < lower)
df = df[~outliers]

#Observing correlation between each columns 
matrix = df.corr()
sns.heatmap(matrix, annot = True, cmap = 'coolwarm')
plt.show()
print(df['Menu_Price'].mean(),df['Menu_Price'].max(),df['Marketing_Spend'].mean(),df['Marketing_Spend'].max(),df['Number_of_Customers'].mean(),df['Number_of_Customers'].max())
contingency_table = pd.crosstab(df['American'], df['Monthly_Revenue'])
chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
print(f"Chi2: {chi2}")
print(f"P-value: {p}")
print(f"Degrees of Freedom: {dof}")
print(f"Expected Frequencies: \n{expected}")


#Model Training
x = df[['Number_of_Customers','Menu_Price','Marketing_Spend']]
#x = df.drop(['Monthly_Revenue'], axis = 1)
y = df['Monthly_Revenue']
scaler = StandardScaler()
x = scaler.fit_transform(x)
x_train, x_test, y_train, y_test = train_test_split(x,y, test_size=0.2, random_state=88)

#Define evaluation function
def evaluation(real, predicted):
    mae = mean_absolute_error(real,predicted)
    mse = mean_squared_error(real,predicted)
    r2 = r2_score(real,predicted)
    return mae, mse, r2

#Define training and tuning model function
param_grid = {  'Linear Regression':{},'Lasso':{'alpha':[0.01,0.1,1,10,100]},'Ridge':{'alpha':[0.01,0.1,1,10,100]},
                'Decision Tree':{'max_depth':[10,20,30],
                                'min_samples_split': [2, 5, 10],
                                'min_samples_leaf': [1, 2, 4]},
                'Random Forest Regressor':{'n_estimators':[50,100,200,300],
                                'max_depth':[10,20,30]},
                                'min_samples_split': [2, 5, 10],
                                'min_samples_leaf': [1, 2, 4],
                'XGBRegressor':{'n_estimators':[50,100,200,300],
                                'learning_rate':[0.01,0.1,0.2,0.3],
                                'max_depth': [10,20,30],
                                'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
                                'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0]},
                "CatBoosting Regressor":{'iteratons':[50,100,200,300],
                                'learning_rate':[0.01,0.1,0.2,0.3],
                                'depth': [10,20,30],
                                'l2_leaf_reg': [1, 3, 5, 7, 9],
                                'border_count': [32, 64, 128, 256]},
                'AdaBoostRegressor':{'n_estimators':[50,100,200,300],
                                'learning_rate': [0.01, 0.05, 0.1, 0.2, 0.3],
                                'loss': ['linear', 'square', 'exponential']}
              }
models = {'Linear Regression':LinearRegression(),"Lasso":Lasso(),"Ridge":Ridge(),"Decision Tree":DecisionTreeRegressor(),
              "Random Forest Regressor":RandomForestRegressor(),"XGBRegressor":XGBRegressor(),"CatBoosting Regressor":CatBoostRegressor(verbose=False),
              "AdaBoostRegressor":AdaBoostRegressor()}

results_before = []
results_after = []
#Before tuning results
for model_name, model in models.items():
    model.fit(x_train,y_train)
    y_train_pred = model.predict(x_train)
    y_test_pred = model.predict(x_test)
    model_train_mae, model_train_mse, model_train_r2 = evaluation(y_train, y_train_pred)
    model_test_mae, model_test_mse, model_test_r2 = evaluation(y_test, y_test_pred)
    cv_scores = cross_val_score(model, x_train, y_train, cv=10, scoring='r2', n_jobs=-1)
    results_before.append({'Model':model_name,'Train MAE':model_train_mae,
                            'Train MSE':model_train_mse,'Train R2':model_train_r2,
                            'Test MAE':model_test_mae,'Test MSE':model_test_mse,
                            "Test R2":model_test_r2,'cv_scores':cv_scores.mean()})

#After tuning results
    param_grid = param_grid.get(model_name,{})
    if param_grid:
        grid_search = GridSearchCV(estimator = model, param_grid = param_grid,cv = 5, scoring = 'r2', n_jobs=-1)
        grid_search.fit(x_train,y_train)
        best_model = grid_search.best_estimator_
    else:
        best_model = model
        best_model.fit(x_train,y_train)
        y_train_pred_tuned = best_model.predict(x_train)
        y_test_pred_tuned = best_model.predict(x_test)
        train_mae_tuned, train_mse_tuned, train_r2_tuned = evaluation(y_train, y_train_pred_tuned)
        test_mae_tuned, test_mse_tuned, test_r2_tuned = evaluation(y_test, y_test_pred_tuned)
        cv_scores_tuned = cross_val_score(best_model, x_train, y_train, cv=10, scoring='r2', n_jobs=-1)
        results_after.append({'Model':model_name,'Test MAE':test_mae_tuned,'Test MSE':test_mse_tuned,
                            'Test R2':test_r2_tuned,'cv_scores':cv_scores_tuned.mean()})
Comparison_before= pd.DataFrame(results_before).sort_values(by = ['Test R2'],ascending=False) 
Comparison_after = pd.DataFrame(results_after).sort_values(by = ['Test R2'],ascending=False)

#Optuna tuning for the best model
def objective(trial):
    model = Lasso(alpha = trial.suggest_loguniform('alpha', 0.001, 100))
    score = cross_val_score(model, x_train, y_train, cv=10, scoring='r2')
    return np.mean(score)
study = optuna.create_study(direction = 'maximize')
study.optimize(objective, n_trials = 100)
best_params = study.best_trial.params
best_lasso = Lasso(**best_params)
best_lasso.fit(x_train, y_train)
y_pred_lasso = best_lasso.predict(x_test)
y_pred_train_lasso = best_lasso.predict(x_train)
lasso_test_mae, lasso_test_mse, lasso_test_r2 = evaluation(y_test, y_pred_lasso)
lasso_train_mae, lasso_train_mse, lasso_train_r2 = evaluation(y_train, y_pred_train_lasso)
cv_scores_lasso = cross_val_score(best_lasso, x_train, y_train, cv=10, scoring='r2', n_jobs=-1)
lasso_data = ['Best_Lasso',lasso_test_mae,lasso_test_mse,lasso_test_r2,cv_scores_lasso.mean()]
Comparison_after.loc[8] = lasso_data
Comparison_after = Comparison_after.sort_values(by = ['Test R2'],ascending=False)

#Model Stacking
stacking = {"Lasso":Lasso(),"Random Forest Regressor":RandomForestRegressor(),"AdaBoostRegressor":AdaBoostRegressor()}
base_learners = [(name, model) for name, model in stacking.items()]
meta_learner = LinearRegression()
stacking_regressor = StackingRegressor(estimators=base_learners, final_estimator=meta_learner)
cv_scores = cross_val_score(stacking_regressor, x_train, y_train, cv=10, scoring='r2')
stacking_regressor.fit(x_train, y_train)
st_y_train_pred = stacking_regressor.predict(x_train)
st_y_test_pred = stacking_regressor.predict(x_test)
st_test_mae, st_test_mse, st_test_r2 = evaluation(y_test, st_y_test_pred)
st_train_mae, st_train_mse, st_train_r2 = evaluation(y_train, st_y_train_pred)
cv_scores_st = cross_val_score(stacking_regressor, x_train, y_train, cv=10, scoring='r2', n_jobs=-1)
st_data = ['Stacking Regressor', st_test_mae, st_test_mse, st_test_r2, cv_scores_st.mean()]
Comparison_after.loc[9] = st_data
Comparison_after = Comparison_after.sort_values(by = ['Test R2'],ascending=False)

#Results comparison
print('Before tuning')
print(Comparison_before)
print('After tuning')
print(Comparison_after)
print('-'*40)
print(f'Lasso optuna result : Intercept = {best_lasso.intercept_}, Coef : {best_lasso.coef_}')