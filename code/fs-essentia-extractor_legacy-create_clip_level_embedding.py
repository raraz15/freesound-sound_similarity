"""Takes fs-essentia-extractor_legacy embeddings, and to implements
the Gaia feature preprocessing with Python. Namely, select a subset
 of the features, normalizes each of them independently and applies
 dimensionality reduction with PCA."""

import os
import time
import glob
import yaml
import json
from pathlib import Path
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA

from lib.utils import get_fname
from lib.directories import AUDIO_DIR

# Use these statistics for each feature
PCA_DESCRIPTORS = [
    "mean",
    "dmean",
    "dmean2",
    "var",
    "dvar",
    "dvar2"
]

# Features that are multiple band
MBAND_FEATURES = [
    "barkbands",
    "erb_bands",
    "frequency_bands",
    "gfcc",
    "mfcc",
    "scvalleys",
    "spectral_contrast"
]

def load_yaml(path):
    return yaml.safe_load(Path(path).read_text())

def select_subset(output):
    """ Selects a determined subset from a large set of features"""

    # For multiband features, collect PCA_DESCRIPTORS statistics of each band separately
    mband_feats = {}
    for feat in MBAND_FEATURES:
        n_bands = len(output["lowlevel"][feat][PCA_DESCRIPTORS[0]]) # Get the Number of bands
        for i in range(n_bands): # Access each band
            mband_feats[f"{feat}_{i}"] = {}
            for stat in PCA_DESCRIPTORS:
                mband_feats[f"{feat}_{i}"][stat] = output["lowlevel"][feat][stat][i]
        del output["lowlevel"][feat]
    # Insert the collection to the rest of the lowlevel features
    for k,v in mband_feats.items():
        output["lowlevel"][k] = v
    # Select the subset of features
    embed = {}
    for feat,feat_dct in output["lowlevel"].items():
        if type(feat_dct) == dict:
            embed[feat] = []
            for stat in PCA_DESCRIPTORS:
                embed[feat].append(feat_dct[stat])
    return embed

# TODO: whiten PCA??
if __name__=="__main__":

    parser=ArgumentParser(description=__doc__, 
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('embed_dir',
                        type=str,
                        help='Directory containing fs-essentia-extractor_legacy embeddings.')
    parser.add_argument("-N",
                        type=int,
                        default=100, 
                        help="Number of PCA components to keep.")
    parser.add_argument('--plot-scree', 
                        action='store_true', 
                        help="Plot variance contributions of PCA components.")
    parser.add_argument("--output-dir",
                        type=str,
                        default="",
                        help="Path to output directory. If not provided, "
                        "a directory will be created in the same directory "
                        "as the embed_dir.")
    args = parser.parse_args()

    # Read all the embeddins
    embed_paths = glob.glob(os.path.join(args.embed_dir, "*.yaml"))
    print(f"{len(embed_paths)} embeddings found.")

    # Create the initial embeddings from model outputs
    print("Creating the initial embeddings...")
    start_time = time.time()
    fnames,embeddings = [],[]
    for i,embed_path in enumerate(embed_paths):
        if (i+1)%1000==0:
            print(f"Processed {i} embeddings...")
        # Get the fname from the path
        fnames += [get_fname(embed_path).split("-")[0]]
        # Load the features and select the subset
        feat_dict = load_yaml(embed_path)
        embeddings += [select_subset(feat_dict)]
    total_time = time.time()-start_time
    print(f"Total time: {time.strftime('%M:%S', time.gmtime(total_time))}")

    # List of all included features
    SUBSET_KEYS = list(embeddings[0].keys())
    print(f"{len(SUBSET_KEYS)} features selected.")

    # Create and store a Scaler for each feature
    print("Fitting scalers for each feature...")
    start_time = time.time()
    scalers = []
    for feat in SUBSET_KEYS:
        # Create the Data Matrix
        data = np.array([embed[feat] for embed in embeddings])
        scaler = MinMaxScaler()
        scaler.fit(data)
        scalers.append((feat,scaler))
    total_time = time.time()-start_time
    print(f"Total time: {time.strftime('%M:%S', time.gmtime(total_time))}")

    # Normalize each feature independently
    print("Normalizing each feature independently...")
    start_time = time.time()
    for i in range(len(embeddings)):
        for key,scaler in scalers:
            d = np.array(embeddings[i][key]).reshape(1,-1)
            embeddings[i][key] = scaler.transform(d).reshape(-1)
    total_time = time.time()-start_time
    print(f"Total time: {time.strftime('%M:%S', time.gmtime(total_time))}")

    # Concat all normalized features, make sure same order is followed
    print("Concatanating all the features....")
    start_time = time.time()
    for i in range(len(embeddings)):
        embeddings[i] = np.array([embeddings[i][k] for k in SUBSET_KEYS]).reshape(-1)
    embeddings = np.array(embeddings)
    total_time = time.time()-start_time
    print(f"Total time: {time.strftime('%M:%S', time.gmtime(total_time))}")

    # Determine PCA components
    n_components = args.N if args.N!=-1 else embeddings.shape[1]

    # Create the output dir
    if args.output_dir == "":
        output_dir = f"{args.embed_dir}-PCA_{n_components}"
    else:
        output_dir = os.path.join(args.output_dir, os.path.basename(args.embed_dir))
    os.makedirs(output_dir, exist_ok=True)
    print(f"Exporting the embeddings to: {output_dir}")

    # Scree plot
    if args.plot_scree:
        print(f"Plotting the PCA Scree plot next to the embeddings...")
        import matplotlib.pyplot as plt
        model = os.path.basename(args.embed_dir)
        data = os.path.basename(os.path.dirname(args.embed_dir))
        title=f'FSD50K.{data} - {model} Embeddings PCA Scree Plot'
        pca = PCA(n_components=None, copy=True)
        pca.fit(embeddings)
        PC_values = np.arange(pca.n_components_) + 1
        cumsum_variance = 100*np.cumsum(pca.explained_variance_ratio_)
        fig,ax = plt.subplots(figsize=(15,8), constrained_layout=True)
        fig.suptitle(title, fontsize=20)
        ax.plot(PC_values, cumsum_variance, 'ro-', linewidth=2)
        ax.set_xlim([-5,len(PC_values)+5])
        ax.set_yticks(np.arange(0,105,5)) # 5% increase
        ax.set_xlabel('Number of Principal Components Selected', fontsize=15)
        ax.set_ylabel('% Cumulative Variance Explained', fontsize=15)
        ax.grid()
        figure_path = os.path.join(output_dir, f'FSD50K.{data}-{model}-scree_plot.jpeg')
        fig.savefig(figure_path)

    # Apply PCA if specified
    if args.N!=-1:
        print("Applying PCA to each embedding...")
        start_time = time.time()
        pca = PCA(n_components=n_components)
        embeddings = pca.fit_transform(embeddings)
        total_time = time.time()-start_time
        print(f"Total time: {time.strftime('%M:%S', time.gmtime(total_time))}")

    # Export the transformed embeddings
    print("Exporting the embeddings...")
    for fname,embed in zip(fnames,embeddings):
        embed = {"audio_path": os.path.join(AUDIO_DIR,f"{fname}.wav"),
                "embeddings": embed.tolist()}
        output_path = os.path.join(output_dir, f"{fname}.json")
        with open(output_path, "w") as outfile:
            json.dump(embed, outfile, indent=4)

    #############
    print("Done!")