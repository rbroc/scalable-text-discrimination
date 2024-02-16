'''
Script for preprocessing and combining generations with human data.
'''

import pathlib 
import re
import pandas as pd

def get_paths(ai_dir: pathlib.Path, human_dir: pathlib.Path, models: list, dataset: str, temp:float=1, prompt_number:int=None):
    '''
    Get all paths pertaining to a particular dataset (e.g., mrpc)
    '''
    ai_paths = []

    # get ai paths based on args 
    for model_name in models:
        model_path = ai_dir / model_name

        if prompt_number:
            file_identifier = f"{dataset}_prompt_{prompt_number}"
            paths = [file for file in model_path.iterdir() if file.name.startswith(file_identifier)]
            ai_paths.extend(paths)

        elif temp: 
            file_identifier = f"{temp}.ndjson"
            paths = [file for file in model_path.iterdir() if file.name.endswith(file_identifier)]
            ai_paths.extend(paths)

        elif prompt_number and temp: 
            file_identifier = f"{dataset}_prompt_{prompt_number}_temp{temp}.ndjson"
            paths = [file for file in model_path.iterdir() if file.name.startswith(file_identifier)]
            ai_paths.extend(paths)

        else:
            ai_paths.extend([file for file in model_path.iterdir()])

    # get human paths 
    human_path =  human_dir / dataset / "data.ndjson"

    if len(ai_paths) == 0: 
        print(f"[WARNING:] Length of ai paths is zero. Ensure that you have valid arguments.")

    return ai_paths, human_path

def load_dataset(ai_paths, human_path):
    '''
    Load data from paths extracted from get_paths function
    '''

    ai_dfs = [pd.read_json(p, lines=True) for p in ai_paths]
    human_df = pd.read_json(human_path, lines=True)

    return ai_dfs, human_df

def combine_data(ai_dfs, human_df, subset=None):
    '''
    Return a dataframe for a particular dataset with all AI generations and human data in one.

    Args: 
        ai_dfs: list of dataframes
        human_df: dataframe corresponding to the dfs in ai_dfs 
        subset: whether datasets should be subsetted (subsets ai datasets to n first rows, and subsequently matches the human completions on completion id). For prompt selection, this was set to 99.

    Returns: 
        combined_df: combined dataframe
    '''
    # prepare data for concatenating (similar formatting)
    for idx, df in enumerate(ai_dfs): 
        # subset to only 100 vals (since some have 150 and some have 100)
        if subset:
            new_df = df.loc[:subset].copy()
        else: 
            new_df = df.copy()
        
        # standardise prompt and completions cols 
        prompt_colname = [col for col in new_df.columns if col.startswith("prompt_")][0] # get column name that starts with prompt_ (e.g., prompt_1, prompt_2, ...)
        new_df["prompt_number"] = prompt_colname.split("_")[1] # extract numbers 1 to 6
        new_df.rename(columns={prompt_colname: "prompt"}, inplace=True)

        mdl_colname = [col for col in new_df.columns if col.endswith("_completions")][0] 
        new_df["model"] = re.sub(r"_completions$", "", mdl_colname)  # remove "_completions" from e.g., "beluga_completions"
        new_df.rename(columns={mdl_colname: "completions"}, inplace=True)
        
        # add source col 
        new_df = new_df.merge(human_df[["id", "source"]], on="id", how="left")

        # replace OG df with new df 
        ai_dfs[idx] = new_df
   
    human_df = human_df.query('id in @ai_dfs[1]["id"]').copy()
    human_df["model"] = "human"
    #human_df.drop(["source"], inplace=True, axis=1)
    human_df.rename(columns={"human_completions": "completions"}, inplace=True)

    # add human dfs
    all_dfs = [human_df, *ai_dfs]

    # append human to ai_dfs, concatenate all data
    combined_df = pd.concat(all_dfs, ignore_index=True, axis=0)

    return combined_df

def preprocess_datasets(ai_dir: pathlib.Path, human_dir: pathlib.Path, models: list, datasets: list, subset=None, temp: str = None):
    '''
    Loads and prepares as many datasets as needed
    
    Args:
        ai_dir: path to directory with AI datasets
        human_dir: path to directory with human datasets
        models: list of models to include
        datasets: list of datasets to include
        subset: whether datasets should be subsetted (subsets ai datasets to n first rows, and subsequently matches the human completions
        temp: temperature in file name (e.g., temp1, temp2, temp3 or temp1.4)
        prompt_n: prompt number (e.g., 21)

    Returns:
        all_dfs_combined: combined dataframe with all datasets
    '''

    all_dfs = []

    for dataset in datasets: 
        ai_paths, human_path = get_paths(ai_dir, human_dir, models, dataset, temp=temp)
        ai_dfs, human_df = load_dataset(ai_paths, human_path)
        dataset_df = combine_data(ai_dfs, human_df, subset=subset)
        
        # add dataset col 
        dataset_df["dataset"] = dataset

        all_dfs.append(dataset_df)
        
    if len(datasets) > 1:  
        final_df = pd.concat(all_dfs, ignore_index=True, axis=0)
    
    else:
        final_df = all_dfs[0]

    return final_df

def main(): 
    path = pathlib.Path(__file__)
    ai_dir = path.parents[2] / "datasets" / "ai_datasets" / "vLLM" / "FULL_DATA"
    human_dir = path.parents[2] / "datasets" / "human_datasets"
    
    models = ["beluga7b", "llama2_chat13b", "mistral7b"]
    datasets = ["dailymail_cnn", "stories", "mrpc", "dailydialog"]

    ai_paths, human_paths = get_paths(ai_dir, human_dir, models, dataset="stories", temp=1.5, prompt_number=22)

    for p in ai_paths: 
        print(p)

    #all_dfs = preprocess_datasets(ai_dir, human_dir, models, datasets, subset=99)
    
    #print(all_dfs)


if __name__ == "__main__":
    main()

