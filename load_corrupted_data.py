from PIL import Image
import os
import os.path
import errno
import numpy as np
import sys
import pickle

import torch.utils.data as data
from torchvision.datasets.utils import download_url, check_integrity

import torch
import torch.nn.functional as F
from torch.autograd import Variable as V
import wideresnet as wrn
import torchvision.transforms as transforms

import pandas as pd
from ast import literal_eval


def get_label_to_id(raw_labels):
    label_to_id = {'benigh': 0}
    cnt = 1

    for i in range(len(raw_labels)):

        if raw_labels is None:
            continue

        candidate_label = literal_eval(raw_labels[i])

        for label in candidate_label:
            if label[0] not in id_label:
                label_to_id[label[0]] = cnt 
                cnt += 1

    return label_to_id


def divide_dataset(raw_names, raw_labels):

    label_to_num = {}
    for i in range(len(raw_labels)):
        if raw_name[i].endswith('white'):
            label = 'benigh'
            if label not in label_to_num:
                label_to_num[label] = []
            label_to_num[label].append(i)
        else:
            candidate_label = literal_eval(raw_labels[i])
            label = candidate_label[0][0]

            if label not in label_to_num:
                label_to_num = []
            label_to_num[label].append(i)

    train_list = []
    test_list = []

    for key, value in label_to_num.items():
        num = len(value)
        train_sz = int(0.8 * num)
        train_list += value[0: train_sz]
        test_list += value[train_sz, :]

    return train_list, test_list


class PE_dataset(data.Dataset):

    def __init__(self, root, data_file, label_file, train=True,  seed=1):
        self.root = root
        self.train = train  # training set or test set
        self.gold = gold

        # now load the picked numpy arrays
        
        self.train_data = []
        self.train_labesl = []
        ## read the csv files
        datasets = pd.read_csv(root + '/' + label_file)
        raw_names = datasets.iloc[:, 1].values
        raws_labels = datasets.iloc[:, 3].values
        label_to_id = get_label_to_id(raw_labels)


        feats = pd.read_csv(root + '/' + data_file)
        raw_feats = feats.iloc[:, 2].values

        self.class_num = len(label_to_id)


        ## split training set and testing set
        train_list, test_list = divide_dataset(raw_names, raw_labels)

        if train:

            self.train_data = [], self.train_label = [], self.confusions = []

            for i in range(len(raw_labels)):
                if i not in train_list:
                    continue
                feat = np.array(literal_eval(raw_feats[i]))
                self.train_data.append(feat)

                confusion = np.zeros((self.class_num, self.class_num), dtype=float)
                for i in range(self.class_num): confusion[i][i] = 1.0


                if raw_labels[i] is None:
                    label = label_to_id['benigh']
                else:
                    candidate_label = literal_eval(raw_labels[i])

                    if raw_names[i].endswith('white'):
                        counts = []
                        total = 0
                        for i in range(len(candidate_label)):
                            num = candidate_label[i][1]
                            counts.append(num)
                            total += num 
                        for i in range(len(counts)) counts[i] /= 16
                        counts.append(1 - total * 1.0 / 16)
                        prob = np.array(counts)
                        index = np.random.choice(range(0, len(candidate_label) + 1), prob.ravel())
                        if index == len(candidate_label): 
                           label = label_to_id['benigh'] 
                        else:
                           label = label_to_id[candidate_label[index][0]]

                        id = 0
                        for i in range(len(counts) - 1):
                            fake_id = label_to_id[candidate_label[i][0]]
                            confusion[id][fake_id] = prob[i]

                        confusion[id][id] = prob[-1]

                    else:
                        counts = []
                        total = 0
                        for i in range(len(candidate_label)):
                            num = candidate_label[i][1]
                            counts.append(num)
                            total += num

                        for i in range(len(counts)) counts[i] /= num

                        prob = np.array(counts)
                        index = np.random.choice(range(0, len(candidate_label)), prob.ravel())
                        label = label_to_id[candidate_label[index][0]]
                        id = label_to_id[candidate_label[0][0]]

                        for i in range(len(counts)):
                            fake_id = label_to_id[candidate_label[i][0]]
                            confusion[id][fake_id] = prob[i]
                self.train_label.append(label)
                self.confusions.append(confusion)
            return self.train_data, self.train_label, self.confusions
        else:

            self.test_data = [], self.test_label = []

            for i in range(len(raw_labels)):
                if i not in test_list:
                    continue
                feat = np.array(literal_eval(raw_feats[i]))
                if raw_names[i].endswith('white'):
                    label = label_to_id['benigh']
                else:
                    label = label_to_id[raw_labels[0][0]]
                self.test_data.append(feat)
                self.test_label.append(label)

            return self.test_data, self.test_label


    def __getitem__(self, index):
        if self.train:
            feature, target, confusion = self.train_data[index], self.train_label[index], self.confusions[index] 
        else:
            feature, target = self.test_data[index], self.test_label[index]
        return img, target

    def __len__(self):
        if self.train:
            return len(train_list)
        else:
            return len(test_list)
