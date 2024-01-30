'''
Script to investigate generated data
'''
import pathlib
import sys
sys.path.append(str(pathlib.Path(__file__).parents[3]))
from src.utils.process_generations import preprocess_datasets
from src.utils.pca import get_descriptive_metrics, run_PCA, save_PCA_results, get_loadings, plot_loadings
from src.utils.distance import compute_distances, jitterplots, interactive_jitterplot

def main(): 
    path = pathlib.Path(__file__)
    ai_dir = path.parents[3] / "datasets" / "ai_datasets" / "vLLM" / "FULL_DATA"
    human_dir = path.parents[3] / "datasets" / "human_datasets"

    results_path = path.parents[3] / "results" / "descriptives"
    pca_path = results_path / "PCA"
    distance_path = results_path / "distance"

    for p in [pca_path, distance_path]:
        p.mkdir(parents=True, exist_ok=True)
    
    models = ["beluga7b", "llama2_chat13b", "mistral7b"]
    datasets = ["dailymail_cnn", "stories", "mrpc", "dailydialog"]

    print("[INFO:] Preprocessing datasets ...")
    df = preprocess_datasets(ai_dir, human_dir, models, datasets)

    # run pca
    print("[INFO:] Extracting Metrics ...")
    df = df.drop("doc_length", axis=1)

    metrics_df = get_descriptive_metrics(df, "completions", "id")

    print("[INFO:] Running PCA ...")
    pca, pca_df = run_PCA(metrics_df, feature_names=["doc_length", "n_tokens", "n_characters", "n_sentences"], n_components=4)

    print("[INFO:] Saving PCA results ...")
    save_PCA_results(pca, pca_path)
    pca_df.to_csv(pca_path/"PCA_DATA")

    print("[INFO:] Plotting PCA")
    loadings_matrix = get_loadings(pca, feature_names=["doc_length", "n_tokens", "n_characters", "n_sentences"],  n_components=4)

    for component in range(1, 5):
        plot_loadings(loadings_matrix, component, pca_path)

    # run distance
    print("[INFO]: Computing distances")
    distances = compute_distances(pca_df, models=models, save_path=distance_path, include_baseline_completions=True)

if __name__ == "__main__":
    main()

