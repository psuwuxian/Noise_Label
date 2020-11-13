import os
import os.path
import numpy as np
import sys
import pickle

import torch.utils.data as data
import math
import pandas as pd
from ast import literal_eval
import csv

import random

'''
def get_label_to_id(raw_labels):
    label_to_id = {'benigh': 0}
    cnt = 1
    for i in range(len(raw_labels)):
        if not isinstance(raw_labels[i], str):
            continue
        candidate_label = literal_eval(raw_labels[i])
        for label in candidate_label:
            if label[0] not in label_to_id:
                label_to_id[label[0]] = cnt 
                cnt += 1

    return label_to_id

def get_num(raw_labels, flags):
    mapping = {}
    for i in range(len(raw_labels)):
        if not isinstance(raw_labels[i], str):
            if 'benigh' not in mapping:
                mapping['benigh'] = 1
            else:
                mapping['benigh'] += 1
        else:
            if flags[i] == 2:
                mapping['benigh'] += 1
            else:
                candidate_label = literal_eval(raw_labels[i])
                label = candidate_label[0][0]
                if label not in mapping:
                    mapping[label] = 1
                else:
                    mapping[label] += 1
    # sort the label
    sorted(mapping.items(), key=lambda x: x[1], reverse=True)

    mapping_class = {}
    for k, v in mapping.items():
        if v <= 30: continue
        else:
            mapping_class[k] = v
    return mapping_class

def calculate_ratio(mapping_class, raw_labels, flags):
    cnt = 0
    noise_black = 0
    noise_white = 0
    noise_white_total = 0
    total_ratio = 0

    for i in range(len(raw_labels)):
        if not isinstance(raw_labels[i], str):
            continue
        candidate_label = literal_eval(raw_labels[i])
        if flags[i] == 1:
            true_label = candidate_label[0][0]
        else:
            true_label = 'benigh'
            noise_white_total += 1
        if true_label not in mapping_class:
            continue
        total = len(candidate_label)
        #ret = []
        for label in candidate_label:
            if label[0] not in mapping_class:
                total -= 1
            #ret.append(label[0])
        if total > 1:
            cnt += 1
            num = 0
            for label in candidate_label:
                if label[0] in mapping_class:
                    num += label[1]
            ratio = (num - candidate_label[0][1]) * 1.0 / num
            total_ratio += ratio
            noise_black += 1

        elif total == 1:
            if flags[i] == 2:
               noise_white += 1
               cnt += 1
    sum = 0
    for k, v in mapping_class.items():
        sum += v

    print('noise data is ', ratio * 1.0 / noise_black)

    print('noisy ratio is ', cnt * 1.0 / sum)
    print('end ....')

def divide_dataset(benigh_list,  raw_labels, flags, mapping_class):

    label_to_num = {}
    for i in range(len(raw_labels)):
        if not isinstance(raw_labels[i], str):
            real_label = 'benigh'
        else:
            if flags[i] == 2:
                real_label = 'benigh'
            else:
                candidate_label = literal_eval(raw_labels[i])
                real_label = candidate_label[0][0]
        if real_label not in mapping_class:
            continue
        if real_label == 'benigh' and i not in benigh_list:
            continue

        if real_label not in label_to_num:
            label_to_num[real_label] = []
        label_to_num[real_label].append(i)

    train_list = []
    test_list = []

    for key, value in label_to_num.items():
        num = len(value)
        train_sz = int(0.8 * num)
        train_list += value[0: train_sz]
        test_list += value[train_sz: ]

    return train_list, test_list
'''


def go_class(raw_labels, flags):
    class_to_num = {}
    class_to_list = {}
    num = len(raw_labels)

    for i in range(num):
        if not isinstance(raw_labels[i], str):
            if 'benigh' not in class_to_num:
                class_to_num['benigh'] = 1
                class_to_list['benigh'] = []
            else:
                class_to_num['benigh'] += 1
            class_to_list['benigh'].append(i)


        else:
            if flags[i] == 2:
                class_to_num['benigh'] += 1
                class_to_list['benigh'].append(i)
            else:
                labels = literal_eval(raw_labels[i])
                true_label = labels[0][0]
                if true_label not in class_to_num:
                    class_to_num[true_label] = 1
                    class_to_list[true_label] = []
                else:
                    class_to_num[true_label] += 1
                class_to_list[true_label].append(i)

    filter_class = {}
    filter_list = {}
    for k, v in class_to_num.items():
        if v <= 30:
            continue
        else:
            filter_class[k] = v
            filter_list[k] = class_to_list[k]

    return filter_class, filter_list


def go_multi_labels(raw_labels, filter_class, flags):
    num = len(raw_labels)
    multi_label = []

    for i in range(num):
        if not isinstance(raw_labels[i], str):
            continue
        else:
            labels = literal_eval(raw_labels[i])
            if flags[i] == 2:
                true_label = 'benigh'
            else:
                true_label = labels[0][0]

            if true_label not in filter_class:
                continue

            total = len(labels)
            for label in labels:
                if label[0] not in filter_class:
                    total -= 1

            if total > 1:
                multi_label.append(i)
            elif total == 1:
                if flags[i] == 2:
                    multi_label.append(i)
    return multi_label


def go_train_test_set(multi_label, filter_list):
    # construct datasets
    num = len(multi_label)
    train_list = []
    test_list = []

    assert num == 6724
    remaining = 2 * num

    is_train = True

    for k, v_list in filter_list.items():
        if k == 'benigh': continue
        for i in v_list:
            if i in multi_label: continue
            if random.random() < 0.57:
                train_list.append(i)
            else:
                pass
            is_train = not is_train

    remaining -= len(train_list)

    for i in filter_list['benigh']:
        if i in multi_label: continue
        if remaining >= 0:
            train_list.append(i)
            remaining -= 1

    # construct test_list
    for k, v_list in filter_list.items():
        if k == 'benigh': continue
        for i in v_list:
            if i in train_list or i in multi_label:
                continue
            else:
                if random.random() < 0.5:
                   test_list.append(i)

    for i in filter_list['benigh']:
        if i in multi_label or i in train_list:
            continue
        else:
            if len(test_list) < 5100:
               test_list.append(i)

    return train_list + multi_label, test_list


def write_into_csv(raw_name, raw_labels, flags, filter_class, train_list, test_list, av_class, raw_feats):
    fileHeader = ["name", "label", "train/test"]

    csvFile = open('feats', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    num = len(raw_labels)
    for i in range(num):
        data = []
        if i in train_list or i in test_list:
            data.append(raw_name[i])
            data.append(raw_feats[i])
            if i in train_list: data.append(1)
            else: data.append(0)
        writer.writerow(data)
    csvFile.close()

    ## write into true_label
    csvFile = open('true_label', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    num = len(raw_labels)
    t = 0

    for i in range(num):
        data = []
        if i in train_list or i in test_list:
            t += 1
            data.append(raw_name[i])
            if not isinstance(raw_labels[i], str):
                label = 'benigh'
            else:
                if flags[i] == 2:
                    label = 'benigh'
                else:
                    labels = literal_eval(raw_labels[i])
                    label = labels[0][0]
            data.append(label)

            if i in train_list:
                data.append(1)
            else:
                data.append(0)
            writer.writerow(data)
    csvFile.close()

    csvFile = open('noise_label', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    num = len(raw_labels)

    for i in range(num):
        data = []
        if i in train_list:
            data.append(raw_name[i])
            if not isinstance(raw_labels[i], str):
                noise_label = [('benigh', -1)]
            else:
                noise_label = []
                if flags[i] == 1:
                    labels = literal_eval(raw_labels[i])
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label.append(label)
                else:
                    labels = raw_labels[i]
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label.append(label)
                    noise_label.append(('benigh', av_class[i]))
            data.append(noise_label)
            if i in train_list:
                data.append(1)
            else:
                data.append(0)
            writer.writerow(data)
    csvFile.close()


class PE_dataset(data.Dataset):

    def __init__(self, root, data_file, label_file, train=True,  seed=1):
        self.root = root
        self.train = train  # training set or test set
        # now load the picked numpy arrays
        
        self.train_data = []
        self.train_labesl = []
        ## read the csv files
        datasets = pd.read_csv(root + '/' + label_file)
        raw_names = datasets.iloc[:, 1].values
        raw_labels = datasets.iloc[:, 3].values
        flags = datasets.iloc[:, 4].values
        avs = datasets.iloc[:, 6].values - datasets.iloc[:, 5].values


        filter_class, filter_list = go_class(raw_labels, flags)
        multi_label = go_multi_labels(raw_labels, filter_class, flags)
        train_list, test_list = go_train_test_set(multi_label, filter_list)

        feats = pd.read_csv(root + '/' + data_file)
        raw_feats = feats.iloc[:, 2].values

        write_into_csv(raw_names, raw_labels, flags, filter_class, train_list, test_list, avs, raw_feats)



        '''
        mapping_class = get_num(raw_labels, flags)
        use_list = calculate_ratio(mapping_class, raw_labels, flags)

        train_list, test_list = divide_dataset(use_list, raw_labels, flags, mapping_class)


        label_to_id = get_label_to_id(raw_labels)

        feats = pd.read_csv(root + '/' + data_file)
        raw_feats = feats.iloc[:, 2].values

        self.class_num = len(label_to_id)

        ## split training set and testing set
        self.train_list = train_list
        self.test_list = test_list
        '''

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
                        for i in range(len(counts)): counts[i] /= 16
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

                        for i in range(len(counts)): counts[i] /= total

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
            return feature, target, confusion
        else:
            feature, target = self.test_data[index], self.test_label[index]
            return feature, target

    def __len__(self):
        if self.train:
            return len(self.train_list)
        else:
            return len(self.test_list)

if __name__ == '__main__':
    root = '/home/xkw5132/wuxian/noise_learning/label_fea'
    data_file = 'data_fea_ist.csv'
    label_file = 'avclass_label_ist.csv'
    trainset = PE_dataset(root=root, data_file=data_file, label_file=label_file, train=True)
