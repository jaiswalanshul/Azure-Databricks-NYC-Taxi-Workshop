# Databricks notebook source
# Shared settings
user_name = None # Should only contain alpha-numeric and underscores

model_dataset_name = 'model_dataset_{0}'.format(user_name)
pyspark_experiment_name = 'pyspark_taxi_duration_{0}'.format(user_name)
automl_experiment_name = 'automl_taxi_duration_{0}'.format(user_name)

if not user_name:
  raise AttributeError("You must enter a unique user name for this workshop. " 
                       "This will avoid issues when we're all interacting with the same cluster.")

# COMMAND ----------

# Azure Machine Learning Services Settings

# COMMAND ----------

AZURE_ML_CONF = {'subscription_id': None, # Delete 'None' and enter your subscription_id here. See animation below for details
                 'resource_group': None,  # Delete 'None' and enter your resource_group name here - 
                                          # if you don't have an AML Workspace, you can enter the desired resource group name here.
                 'workspace_name': None}  # Delete 'None' and enter your workspace_name name here - 
                                          # if you don't have an AML Workspace, you can enter the desired workspace name here.

# COMMAND ----------

### Finding your Azure Subscription ID

# To find your Azure Subscription ID, you can navigate to [https://portal.azure.com](https://portal.azure.com), then follow the link below to see an animation on where to find it.

# https://github.com/Microsoft/Azure-Databricks-NYC-Taxi-Workshop/raw/master/images/8-machine-learning/3-find-azure-subscription.gif

# COMMAND ----------

# Shared Functions

# COMMAND ----------

import matplotlib.pyplot as plt

def generate_crosstab(ct, 
                     title="Location ID Populated versus Date",
                     axis_titles={'x': 'Location ID Populated', 'y': 'Date before or after July 1st, 2016'},
                     axis_labels={'x': ['No', 'Yes'], 'y': ['Before', 'After']},
                     cmap=plt.cm.Greens):
  import itertools

  fig, ax = plt.subplots()

  dt = ct.values.T[1:, :].astype('float').T

  plt.imshow(dt, interpolation='nearest', cmap=cmap)
  # plt.tight_layout()
  plt.title(title)


  plt.yticks(range(len(axis_labels['y'])), axis_labels['y'])
  plt.ylabel(axis_titles['y'])

  plt.xticks(range(len(axis_labels['x'])), axis_labels['x'])
  plt.xlabel(axis_titles['x'])
  
  thresh = dt.max() / 2.
  for i, j in itertools.product(range(dt.shape[0]), range(dt.shape[1])):
      plt.text(j, i, "{:,}".format(int(dt[i, j])),
               horizontalalignment="center",
               color="white" if dt[i, j] > thresh else "black")
             
  return fig

# COMMAND ----------

def plot_residuals(scored_data, target="duration_minutes", prediction='prediction', sample_percent=0.5):
  """
  CAUTION: This will collect the data back to the driver - 
  therefore, it's recommended to sample from the dataframe before doing that - that's what the sample percent argument is for.
  
  Plot the residual values and return a matplotlib chart.
  """
  from pyspark.sql.functions import col
  import matplotlib.pyplot as plt
  
  df = scored_data.select([col(target), col(prediction)]).withColumn("error", col(prediction) - col(target)).sample(fraction=sample_percent, withReplacement=False).toPandas()
  
  fig, ax = plt.subplots()
  
  plt.scatter(df.duration_minutes, df.error, alpha=0.5)
  plt.title("Residual Plot")
  plt.xlabel('Actual Values')
  plt.ylabel("Residual")
  plt.close(fig) # Prevent further changes to the plot (also frees up system resources)
  
  return fig

# COMMAND ----------

def get_train_test_valid_data(table_name='global_temp.{0}'.format(model_dataset_name), randomSeed=35092, splits=[.005, .001, .001, .993]):
  tripData = spark.read.table(table_name)

  
  # Selecting a much smaller sample of data
  # Doing an 80%, 10%, 10% split - because we have 
  df_splits = tripData.randomSplit(splits, seed=randomSeed)
  
  # return the first 3 dataframes
  return df_splits[:3]