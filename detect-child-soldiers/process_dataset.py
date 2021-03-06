# -----------------------------
#   USAGE
# -----------------------------
# python process_dataset.py --dataset VictorGevers_Dataset --output output

# -----------------------------
#   IMPORTS
# -----------------------------
# Import the necessary packages
from pyimagesearch.helpers import detect_and_predict_age
from pyimagesearch.helpers import detect_camo
from pyimagesearch import config
from tensorflow.keras.models import load_model
from imutils import paths
import progressbar
import argparse
import cv2
import os


# Construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dataset", required=True, help="path to input directory of images to process")
ap.add_argument("-o", "--output", required=True, help="path to output directory where CSV files will be stored")
args = vars(ap.parse_args())

# Initialize a dictionary that will store the output file pointers for the age and the camo predictions, respectively
FILES = {}

# Loop over the two types of output predictions
for k in ("ages", "camo"):
    # Construct the output file path for the CSV file, open a path to the file pointer,
    # and then store it in the files dictionary
    p = os.path.sep.join([args["output"], "{}.csv".format(k)])
    f = open(p, "w")
    FILES[k] = f

# Load the serialized face detector model, the age detector model and the camo detector model from the disk
print("[INFO] Loading the trained models from disk...")
faceNet = cv2.dnn.readNet(config.FACE_PROTOTXT, config.FACE_WEIGHTS)
ageNet = cv2.dnn.readNet(config.AGE_PROTOTXT, config.AGE_WEIGHTS)
camoNet = load_model(config.CAMO_MODEL)

# Grab the paths to all the images in the dataset
imagePaths = sorted(list(paths.list_images(args["dataset"])))
print("[INFO] Processing {} images".format(len(imagePaths)))

# Initialize the progress bar
widgets = ["Processing Images: ", progressbar.Percentage(), " ", progressbar.Bar(), " ", progressbar.ETA()]
pbar = progressbar.ProgressBar(maxval=len(imagePaths), widgets=widgets).start()

# Loop over the image paths
for (i, imagePath) in enumerate(imagePaths):
    # Load the image from disk
    image = cv2.imread(imagePath)
    # If the image is 'None', then it could not be properly read from disk (so we should just skip it)
    if image is None:
        continue
    # Detect all faces in the input image and then predict their perceived age based on the face ROI
    ageResults = detect_and_predict_age(image, faceNet, ageNet)
    # Use the camo detection model to detect if camouflage exists in the image or not
    camoResults = detect_camo(image, camoNet)
    # Loop over the age detection results
    for r in ageResults:
        # The output row for the ages CSV consists of:
        # (1) the image file path;
        # (2) bounding box coordinates of the face;
        # (3) the predicted age;
        # (4) the corresponding probability of the age prediction
        row = [imagePath, *r["loc"], r["age"][0], r["age"][1]]
        row = ",".join([str(x) for x in row])
        # Write the row to the age prediction CSV file
        FILES["ages"].write("{}\n".format(row))
        FILES["ages"].flush()
    # Check to see if the camouflage predictor was triggered
    if camoResults[0] == "camouflage_clothes":
        # The output row for the camo CSV consists of:
        # (1) the image file path;
        # (2) the probability of the camo prediction;
        row = [imagePath, camoResults[1]]
        row = ",".join([str(x) for x in row])
        # Write the row to the camo prediction CSV file
        FILES["camo"].write("{}\n".format(row))
        FILES["camo"].flush()
    # Update the progress bar
    pbar.update(i)

# Stop the progress bar
pbar.finish()
print("[INFO] Cleaning up...")

# Loop over the open file pointers and close them
for f in FILES.values():
    f.close()

