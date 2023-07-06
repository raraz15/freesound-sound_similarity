#!/bin/bash

SCRIPT_DIR="$(pwd)/scripts/pipelines/"
DATA_DIR="$(pwd)/data"
export PATH="$SCRIPT_DIR:$PATH"

#############################################################################

MODEL_NAME="audioset-vggish-3"
DATASET_NAME="FSD50K.eval_audio"
EMBED_DIR="$DATA_DIR/embeddings/$DATASET_NAME"

#############################################################################

for file in "$EMBED_DIR/"*; do # for each embedding dir
    f=$(basename -- "$file")   # get the basename=embed_name
    if [[ $f == "$MODEL_NAME-"* ]]; then # if the embed contains model-
        echo "======================================================================="
        echo $f
        SUFFIX="${f/$MODEL_NAME-/""}" # Strip model name to get the suffix
        yamnet-search_evaluate.sh $SUFFIX
    fi
done

# Compare the results of the experiments
python code/plot_evaluation_results_comparisons.py =audioset-vgggish-3

#############################################################################