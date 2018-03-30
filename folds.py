import imageio
from glob import glob
import os
import numpy as np
from sklearn.utils import shuffle
import matplotlib.pyplot as plt
import time
import numpy as np

from constants import *

def remove_extension(file):
    return os.path.splitext(file)[0]


def get_filename(file):
    return os.path.basename(remove_extension(file))


def group_uids(files):
    uids = dict()

    # intialize empty sets
    for language in LANGUAGES:
        uids[language] = dict()
        for gender in GENDERS:
            uids[language][gender] = set()

    # extract uids and append to language/gender sets
    for file in files:
        info = get_filename(file).split('_')

        language = info[0]
        gender = info[1]
        uid = info[2].split('.')[0]

        uids[language][gender].add(uid)

    # convert sets to lists
    for language in LANGUAGES:
        for gender in GENDERS:
            uids[language][gender] = sorted(list(uids[language][gender]))

    return uids

def has_uids(uids):
    for language in LANGUAGES:
        for gender in GENDERS:
            if len(uids[language][gender]) == 0:
                return False

    return True


def generate_fold(uids, input_dir, input_ext, output_dir, group, fold_index, shape):

    # pull uid for each a language, gender pair
    fold_uids = []
    for language in LANGUAGES:
        for gender in GENDERS:
            fold_uids.append(uids[language][gender].pop())

    # find files for given uids
    fold_files = []
    for fold_uid in fold_uids:
        filename = '*{uid}*{extension}'.format(uid=fold_uid, extension=input_ext)
        fold_files.extend(glob(os.path.join(input_dir, filename)))

    fold_files = sorted(fold_files)
    fold_files = shuffle(fold_files, random_state=SEED)

    metadata = []

    # create a file array
    filename = "{group}_data.fold{index}.npy".format(group=group, index=fold_index)
    features = np.memmap(
        os.path.join(output_dir, filename),
        dtype=DATA_TYPE, mode='w+',
        shape=(len(fold_files),) + shape
    )

    # append data to a file array
    # append metadata to an array
    for index, fold_file in enumerate(fold_files):
        print(fold_file)

        filename = get_filename(fold_file)
        language = filename.split('_')[0]
        gender = filename.split('_')[1]

        data = np.load(fold_file)[DATA_KEY]
        assert data.shape == shape
        assert data.dtype == DATA_TYPE

        features[index] = data
        metadata.append((language, gender, filename))

    assert len(metadata) == len(fold_files)

    # store metadata in a file
    filename = "{group}_metadata.fold{index}.npy".format(group=group, index=fold_index)
    np.save(
        os.path.join(output_dir, filename),
        metadata
    )

    # flush changes to a disk
    features.flush()
    del features

def generate_folds(input_dir, input_ext, output_dir, group, shape):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files = glob(os.path.join(input_dir, '*' + input_ext))

    uids = group_uids(files)

    fold_index = 1
    while has_uids(uids):
        print("Fold {0}".format(fold_index))

        generate_fold(
            uids, input_dir, input_ext,
            output_dir, group, fold_index, shape
        )

        fold_index += 1

if __name__ == "__main__":
    start = time.time()

    generate_folds(
        './build/test', '.fb.npz',
        output_dir='fb', group='test',
        shape=(FB_HEIGHT, WIDTH, COLOR_DEPTH)
    )
    generate_folds(
        './build/train', '.fb.npz',
        output_dir='fb', group='train',
        shape=(FB_HEIGHT, WIDTH, COLOR_DEPTH)
    )

    end = time.time()
    print("It took [s]: ", end - start)