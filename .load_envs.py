import os

def load_env_variables(filename):
  """
  Reads variables from `filename` and loads them as environment variables
  Expects the file to be formatted as {key}={value}
  """
  with open(filename, 'r') as file:
      for line in file:
          if line.strip() and not line.startswith('#'):
              key, value = line.strip().split('=', 1)
              os.environ[key] = value

load_env_variables('conf.env')