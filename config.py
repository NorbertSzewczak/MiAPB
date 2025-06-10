from opyenxes.classification.XEventAttributeClassifier import XEventAttributeClassifier
from opyenxes.data_in.XUniversalParser import XUniversalParser
import os
from pathlib import Path

# Ścieżki względne do katalogu projektu
current_dir = Path(__file__).parent
file_path = os.path.join(current_dir, "event_logs", "L1.xes")
output_directory = os.path.join(current_dir, "output")

# Upewnij się, że katalog wyjściowy istnieje
os.makedirs(output_directory, exist_ok=True)

with open(file_path) as log_file:
    # Parse the log
    log = XUniversalParser().parse(log_file)[0]

# Generate the classifier
classifier = XEventAttributeClassifier("concept:name", ["concept:name"])

# Convert log object in array with only the Activity attribute of the event
log_list = list(map(lambda trace: list(map(classifier.get_class_identity, trace)), log))