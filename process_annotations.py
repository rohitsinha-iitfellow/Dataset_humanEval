import os
import json

root_dir = r"D:\Perception_dataset\Dataset_humanEval"

for folder in os.listdir(root_dir):
    folder_path = os.path.join(root_dir, folder)
    if os.path.isdir(folder_path):
        json_path = os.path.join(folder_path, "annotation.json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Get the first 20 keys
            keys = list(data.keys())[:20]
            
            # Create new data with only the first 20 entries
            new_data = {k: data[k] for k in keys}
            
            # Write the updated JSON back to the file
            with open(json_path, 'w') as f:
                json.dump(new_data, f, indent=4)
            
            # Remove image files not in the kept keys
            for file in os.listdir(folder_path):
                if file.endswith('.png') and file not in keys:
                    os.remove(os.path.join(folder_path, file))
