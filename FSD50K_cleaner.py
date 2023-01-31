import os
import json
from itertools import combinations

import editdistance as ed

DATASET_DIR = "/data/FSD50K"
EXPORT_DIR = "/home/roguz/freesound-perceptual_similarity/clean_tags"

# TODO: ask where the json is
# TODO: ask which letter to fix
# TODO: make a copy of the input json
# TODO: fix bpm
if __name__=="__main__":

    with open(f"{DATASET_DIR}/FSD50K.metadata/eval_clips_info_FSD50K.json" ,"r") as infile:
        metadata_dict = json.load(infile)
    print(f"There are {len(metadata_dict)} clip metadata.")

    # Retrieve unique tags
    tags = [tag for metadata in metadata_dict.values() for tag in metadata["tags"]]
    tags = sorted(list(set(tags)))
    print(f"{len(tags)} unique tags found.")

    # Some cleaning and formatting
    tags = tags[275:] # remove numbers for now
    print(f"{len(tags)} tags left after removing number tags.")
    tags = [tag for tag in tags if len(tag)>3] # Skip short tags
    print(f"{len(tags)} tags left after removing short tags.")

    # TODO:
    tags_subset = tags[489:1132][:100] # tags starting with "b"
    comb = [(tag0,tag1) for tag0,tag1 in combinations(tags_subset, 2)] # All 2 combinations

    # Find 1 character typos
    groups,remove_indices = [],[]
    for i,(tag0,tag1) in enumerate(comb):
        computed = False
        for j,group in enumerate(groups): # Skip already compared tags
            if tag0 in group and tag1 in group:
                computed = True
                break
        if computed:
            continue
        dist = ed.eval(tag0, tag1) # Calculate levehnsthein distance
        if dist==1:
            if input(f"|{tag0}|{tag1}| Merge? [y/N]: ")=="y":
                tag0_in,tag1_in = False,False
                for j,group in enumerate(groups): # Search each group for both tags
                    if tag0 in group:
                        tag0_in = True
                    if tag1 in group:
                        tag1_in = True
                    if tag0_in or tag1_in:
                        break # A tag is found exit search
                if (not tag0_in) and (not tag1_in): # Neither tag exist in a group, create
                    groups.append(f"{tag0}|{tag1}")
                elif tag0_in and (not tag1_in): # Add tag1 to the group
                    groups[j] += f"|{tag1}"
                elif (not tag0_in) and tag1_in: # Add tag0 to the group
                    groups[j] += f"|{tag0}"

    # TODO: name convention
    # Export the groups
    with open(os.path.join(EXPORT_DIR, "groups.txt"),"w") as outfile:
        for group in groups:
            outfile.write(group+"\n")

    print("\nSelect the representative/correct spelling...")
    # Ask for which name to keep
    replacement_dict = {}
    for group in groups:
        names = group.split("|")
        print("\nWhich word?")
        for i,name in enumerate(names):
            print(f"{i}: {name}")
        j = input("Number: ")
        for i,name in enumerate(names):
            replacement_dict[name] = names[int(j)]

    # Unify the grouped tags
    for clip_id,metadata in metadata_dict.items():
        clean_tags = []
        for tag in metadata["tags"]:
            if tag in replacement_dict:
                tag = replacement_dict[tag]
            clean_tags.append(tag)
        metadata_dict[clip_id]["tags"] = clean_tags

    with open(os.path.join(EXPORT_DIR, "changed.json"),"w") as outfile:
        json.dump(metadata_dict,outfile,indent=4)

    #############
    print("Done!")