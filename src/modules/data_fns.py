'''
Helper functions for datasets. Contains functions for loading the datasets, and extracting min/max new tokens. 
'''

# utils 
from tqdm import tqdm

# data wrangling 
import pandas as pd 
import ndjson

def load_file(filepath):
    '''
    Load ndjson file from path and convert to pandas dataframe 

    Args
        filepath: full path to file 
    
    Returns
        df: pandas dataframe 
    '''

    # load data
    print("[INFO:] Loading data ...")
    with open(filepath) as f:
        data = ndjson.load(f)
    
    # make into dataframe
    df = pd.DataFrame(data)
    
    return df 

def extract_min_max_tokens(datafilename):
    if "stories" in datafilename:
        min_tokens = 365
        max_new_tokens = 998
    
    if "mrpc" in datafilename:
        min_tokens = 19
        max_new_tokens = 28
    
    if "dailymail_cnn" in datafilename:
        min_tokens = 44
        max_new_tokens = 70
    
    if "dailydialog" in datafilename: 
        min_tokens = 6
        max_new_tokens = 16

    return min_tokens, max_new_tokens