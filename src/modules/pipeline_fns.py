'''
Functions for running the text generation pipelines 
'''

# utils 
from tqdm import tqdm

# data wrangling 
import pandas as pd 
import ndjson

# models  
from transformers import pipeline, AutoTokenizer

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

def create_prompt(df, datafile:str="dailymail_cnn", prompt_number:int=1): 
    prompts = {
        # daily mail (summarization)
        "dailymail_cnn_1": "summarize the main points of this article: ", 
        "dailymail_cnn_2": "create a summary of the news article: ", 
        "dailymail_cnn_3": "write a short summarised text of the news article: ",

        # stories (text generate)
        "stories_1": "continue the story: ",
        "stories_2": "write a small text based on this story: ",
        "stories_3": "complete the text: ",
        "stories_4": "complete the story: ",

        # mrpc (paraphrase)
        "mrpc_1": "paraphrase this text: ",
        "mrpc_2": "summarize this text: ", 
        "mrpc_3": "summarize this: ",
        "mrpc_4": "create a summary of this: ",

        # dailydialog 
        "dailydialog_1": "respond to the final sentence: ",
        "dailydialog_2": "continue this dialog: "    }

    # create prompt col 
    df[f"prompt_{prompt_number}"] = prompts[f"{datafile}_{prompt_number}"] + df["source"].copy()
    
    return df 

def completions_generator(df, prompt_col:str, model, model_name:str, min_len:int , max_tokens: int, outfilepath=None):
    '''
    Create completions based on source text in dataframe (df). Save to outfilepath if specified.

    Args
        df: dataframe with "source" text col
        prompt_col: name of column to generate completions from 
        model: initalised pipeline
        model_name: name of model (used for naming the column with generated text)
        min_len: minimum length of the completion (output)
        max_tokens: maximum new tokens to be added 
        outfilepath: path where the file should be saved (defaults to none, not saving anything)

    Returns
        completions_df: dataframe with model completions and ID 
    '''

    # empty list for completions
    completions = []

    # generate the text
    for prompt in tqdm(df[prompt_col], desc="Generating"):
        completion = model(prompt, min_length=min_len, max_new_tokens=max_tokens)

        # extraxt ONLY the text from the completion (it is wrapped as a list of dicts otherwise)
        completion_txt = list(completion[0].values())[0]

        # append to lst 
        completions.append(completion_txt)
    
    # add ID column from completions_df   
    completions_df = df[["id", prompt_col]].copy()

    # add completions 
    completions_df[f"{model_name}_completions"] = completions

    # save it to json ONLY if outfilepath is specified 
    if outfilepath is not None:
        completions_json = completions_df.to_json(orient="records", lines=True)

        with open(outfilepath, "w") as file:
            file.write(completions_json)

    return completions_df

