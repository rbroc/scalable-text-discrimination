import pathlib 
import re
import pandas as pd

import spacy
import textdescriptives as td

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def load_data(ai_dir, human_datapath, models:list, dataset:str): 
    '''
    Loads data and combines dataframes from human and ai generated data.

    Args
        ai_dir (pathlib.Path): Path to ai generated data
        human_datapath (pathlib.Path): Path to human generated data
        models (list): List of models to include in the data
        dataset (str): Name of dataset (dailymail_cnn, mrpc, stories, dailydialog)
    '''

    # paths, access subfolder and its file in ai_dir
    ai_paths = []

    for p in ai_dir.iterdir():
        if p.name in models: # access models folder 
            for f in p.iterdir(): 
                if dataset in f.name: # take only the dataset that is specified from mdl folder
                    ai_paths.append(f)

    ai_paths = sorted(ai_paths)

    # data
    human_df = pd.read_json(human_datapath, lines=True)
    ai_dfs = [pd.read_json(p, lines=True) for p in ai_paths]

    # prepare data for concatenating (similar formatting)
    for idx, df in enumerate(ai_dfs): 
        # subset to only 100 vals (since some have 150 and some have 100)
        new_df = df.loc[:99].copy()
        
        # standardise prompt and completions cols 
        prompt_colname = [col for col in new_df.columns if col.startswith("prompt_")][0] # get column name that starts with prompt_ (e.g., prompt_1, prompt_2, ...)
        new_df["prompt_number"] = prompt_colname.split("_")[1] # extract numbers 1 to 6
        new_df.rename(columns={prompt_colname: "prompt"}, inplace=True)

        mdl_colname = [col for col in new_df.columns if col.endswith("_completions")][0] 
        new_df["model"] = re.sub(r"_completions$", "", mdl_colname)  # remove "_completions" from e.g., "beluga_completions"
        new_df.rename(columns={mdl_colname: "completions"}, inplace=True)

        # replace OG df with new df 
        ai_dfs[idx] = new_df
    
    human_df = human_df.query('id in @ai_dfs[1]["id"]').copy()
    human_df["model"] = "human"
    human_df.drop(["source"], inplace=True, axis=1)
    human_df.rename(columns={"human_completions": "completions"}, inplace=True)

    # add human dfs
    all_dfs = [human_df, *ai_dfs]

    # append human to ai_dfs, concatenate all data
    combined_data = pd.concat(all_dfs, ignore_index=True)

    return combined_data

def get_descriptive_metrics(df:pd.DataFrame, text_column:str, id_column:str):
    '''
    Extract low level descriptive features doc_length, n_tokens, n_characters and n_sentences 
    '''
    textcol = df[text_column]
    idcol = df[id_column]

    metrics = td.extract_metrics(text=textcol, spacy_model="en_core_web_lg", metrics=["descriptive_stats", "quality"])
    metrics["id"] = idcol
    subset_metrics = metrics[["id", "doc_length", "n_tokens", "n_characters", "n_sentences"]]
    
    metrics_df = df.merge(subset_metrics, on="id", how="inner")
    
    return metrics_df 

def run_PCA(metrics_df:pd.DataFrame, feature_names:list):
    # normalise 
    std_scaler = StandardScaler()
    scaled_df = std_scaler.fit_transform(metrics_df[feature_names])

    pca = PCA()
    result = pca.fit_transform(scaled_df)

    return pca.components_, result


def main(): 
    spacy.util.fix_random_seed(129)
    
    # load data 
    path = pathlib.Path(__file__)
    models = ["beluga", "llama2_chat"]
    dataset = "dailymail_cnn"

    ai_dir = path.parents[1] / "datasets_ai"
    human_data = path.parents[1] / "datasets" / dataset / "data.ndjson"

    df = load_data(ai_dir, human_data, models, dataset)

    # get metrics, perform PCA 
    metrics_df = get_descriptive_metrics(df, "completions", "id")

    components, results = run_PCA(metrics_df, feature_names=["doc_length", "n_tokens", "n_characters", "n_sentences"])

    print(components)
    print(results)

if __name__ == "__main__":
    main()