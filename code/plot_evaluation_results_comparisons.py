""" Takes a model name and plots the evaluation results for all its 
variations. Namely, it plots the micro and macro mAP@15."""

import os
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from lib.plotting import plot_micro_map_at_15_comparisons, plot_macro_map_at_15_comparisons
from lib.directories import FIGURES_DIR, EVAL_DIR

if __name__=="__main__":

    parser=ArgumentParser(description=__doc__, 
                        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('model', 
                        type=str, 
                        help='Name of the model.')
    parser.add_argument("--save-dir",
                        type=str,
                        default="",
                        help="Directory to save the figures.")
    parser.add_argument("--dataset",
                        type=str,
                        default="FSD50K.eval_audio",
                        help="Dataset used for evaluating.")
    args=parser.parse_args()

    # Create the save directory if it does not exist
    if args.save_dir == "":
        args.save_dir = os.path.join(FIGURES_DIR, args.model)

    # Plot the figures
    plot_micro_map_at_15_comparisons(args.model,
                                    EVAL_DIR,
                                    dataset_name=args.dataset,
                                    save_fig=True,
                                    save_dir=args.save_dir)
    plot_macro_map_at_15_comparisons(args.model, 
                                    EVAL_DIR, 
                                    dataset_name=args.dataset, 
                                    save_fig=True, 
                                    save_dir=args.save_dir)
    print("Done!")
