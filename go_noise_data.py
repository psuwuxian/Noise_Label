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


def go_class(raw_labels, flags):
    class_to_num = {}
    class_to_list = {}
    num = len(raw_labels)

    for i in range(num):
        if not isinstance(raw_labels[i], str):
            if 'benign' not in class_to_num:
                class_to_num['benign'] = 1
                class_to_list['benign'] = []
            else:
                class_to_num['benign'] += 1
            class_to_list['benign'].append(i)

        else:
            if flags[i] == 2:
                class_to_num['benign'] += 1
                class_to_list['benign'].append(i)
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

    total = 0
    for k, v in class_to_num.items():
        if v <= 100 or k == 'dinwod':
            continue
        else:
            filter_class[k] = v
            filter_list[k] = class_to_list[k]
        #total += v

    for k, v in filter_class.items():
        total += v
    print('total is ', total)

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
                true_label = 'benign'
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
    
    for k, v_list in filter_list.items():
        train_test = []
        for i in v_list:
            if i in multi_label: continue
            train_test.append(i)
        print(len(train_test))
        if k == 'benign':
            test_list.extend(train_test[:100])
            train_list.extend(train_test[100:500])
        else:
            # split-train-test
            if len(train_test) < 500:
                assert len(train_test) > 100
                test_num = 100
            else:
                test_num = int(len(train_test) * 0.2)
            test_list.extend(train_test[:test_num])
            train_list.extend(train_test[test_num:])
    return train_list + multi_label, test_list


def change_to_0(filter_class):
    one_class = {}
    t = 0
    for k, v in filter_class.items():
        one_class[k] = t
        t += 1
    return one_class

def process(feature):
    feat = feature[1:-1]
    digits = feat.split(',')
    matrix = [int(str) for str in digits]
    return np.array(matrix)

def write_into_csv(raw_name, raw_labels, flags, filter_class, train_list, test_list, av_class, raw_feats):
    fileHeader = ["feature", "label"]
    ## write into true_label
    csvFile = open('true_label_train', 'w')
    csvFile_test = open('true_label_test', 'w')
    writer = csv.writer(csvFile)
    writer_test = csv.writer(csvFile_test)
    writer.writerow(fileHeader)
    writer_test.writerow(fileHeader)

    num = len(raw_labels)

    true_train_class = {}
    true_test_class = {}

    ## features
    train_features = []
    test_features = []
    train_true_label_list = []
    test_true_label_list = []
    train_noise_label_list = []

    ## filtering the class:
    for i in range(num):
        if not isinstance(raw_feats[i], str):
            print('enter ....')
            if i in train_list:
                train_list.remove(i)
            elif i in test_list:
                test_list.remove(i)

    ins_label = {}

    for i in range(num):
        data = []
        if i in train_list or i in test_list:
            data.append(raw_feats[i])
            if not isinstance(raw_feats[i], str):
                print(raw_feats[i])
            ## feat = literal_eval(raw_feats[i])
            feat = process(raw_feats[i])

            if not isinstance(raw_labels[i], str):
                label = 'benign'
            else:
                if flags[i] == 2:
                    label = 'benign'
                else:
                    labels = literal_eval(raw_labels[i])
                    label = labels[0][0]

            if i in train_list:
                ins_label[i] = label
                if label not in true_train_class:
                    true_train_class[label] = []
                else:
                    true_train_class[label].append(i)
            else:
                if label not in true_test_class:
                    true_test_class[label] = []
                else:
                    true_test_class[label].append(i)

            label = filter_class[label]
            data.append(label)
            if i in train_list:
                train_features.append(feat)
                train_true_label_list.append(label)
                writer.writerow(data)
            else:
                test_features.append(feat)
                test_true_label_list.append(label)
                writer_test.writerow(data)
    csvFile.close()
    csvFile_test.close()

    noise_train_class = {}

    csvFile = open('noise_label_train', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    shodi_samples = 0

    for i in range(num):
        data = []
        if i in train_list:

            data.append(raw_feats[i])
            if not isinstance(raw_labels[i], str):
                noise_label = 'benign'
            else:
                noise_label_list = []
                if flags[i] == 1:
                    labels = literal_eval(raw_labels[i])
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label_list.append(label[0])
                    if len(noise_label_list) >= 2:
                        if noise_label_list[0] == 'shodi':
                            shodi_samples += 1
                            if shodi_samples <= 100:
                                noise_label = 'shodi'
                            else:
                                noise_label = noise_label_list[1]
                        else:
                            noise_label = noise_label_list[1]
                    else:
                        noise_label = noise_label_list[0]
                else:
                    labels = literal_eval(raw_labels[i])
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label_list.append(label[0])
                    if len(noise_label_list) >= 1:
                        noise_label = noise_label_list[0]
                    else:
                        noise_label = 'benign'

            if noise_label not in noise_train_class:
                noise_train_class[noise_label] = []
            else:
                noise_train_class[noise_label].append(i)
            data.append(filter_class[noise_label])
            train_noise_label_list.append(filter_class[noise_label])
            writer.writerow(data)
    csvFile.close()

    ## write into confusion matrix
    fileHeader = ["multi_annotator"]
    csvFile = open('multi_annotator_train', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    csvFile_test = open('multi_annotator_test', 'w')
    writer_test = csv.writer(csvFile_test)
    writer_test.writerow(fileHeader)


    for i in range(num):
        data = []
        if i in train_list or i in test_list:
            if not isinstance(raw_labels[i], str):
                noise_label = [('benign', -1)]
            else:
                noise_label = []
                if flags[i] == 1:
                    labels = literal_eval(raw_labels[i])
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label.append(label)
                else:
                    labels = literal_eval(raw_labels[i])
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label.append(label)
                    noise_label.append(('benign', av_class[i]))

            assert len(noise_label) <= 3
            data.append(noise_label)

            if i in train_list:
                writer.writerow(data)
            elif i in test_list:
                writer_test.writerow(data)

    csvFile.close()
    csvFile_test.close()

    train_confusions = []
    test_confusions = []

    for i in range(num):
        if i in train_list or i in test_list:
            confusion = np.zeros((30, 30), dtype=float)
            for j in range(30):
                confusion[j][j] = 1.0

            if not isinstance(raw_labels[i], str):
                noise_label = [('benign', -1)]
                true_label = 'benign'
            else:
                noise_label = []
                if flags[i] == 1:
                    labels = literal_eval(raw_labels[i])
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label.append(label)
                else:
                    labels = literal_eval(raw_labels[i])
                    for label in labels:
                        if label[0] not in filter_class:
                            continue
                        noise_label.append(label)
                    noise_label.append(('benign', av_class[i]))

                if flags[i] == 1:
                    true_label = noise_label[0][0]
                else:
                    true_label = 'benign'

                if len(noise_label) > 1:
                   total = 0
                   for label in noise_label:
                        total += label[1]
                   for label in noise_label:
                        c_label = label[0]
                        confusion[filter_class[true_label]][filter_class[c_label]] = label[1] * 1.0 / total

            if i in train_list:
                train_confusions.append(confusion[filter_class[true_label]])
            elif i in test_list:
                test_confusions.append(confusion[filter_class[true_label]])


    ## list to numpy
    train_confusions = np.vstack(train_confusions)
    test_confusions = np.vstack(test_confusions)
    train_features = np.vstack(train_features)
    test_features = np.vstack(test_features)


    train_true_label_list = np.array(train_true_label_list)
    test_true_label_list = np.array(test_true_label_list)
    train_noise_label_list = np.array(train_noise_label_list)

    for i in range(len(train_true_label_list)):
        true_label = train_true_label_list[i]
        fake_label = train_noise_label_list[i]
        if true_label != fake_label:
            assert train_confusions[i][true_label] > 0
            assert train_confusions[i][fake_label] > 0

    train_features = train_features.astype(np.int32)
    test_features = test_features.astype(np.int32)
    train_true_label_list = train_true_label_list.astype(np.int8)
    test_true_label_list = test_true_label_list.astype(np.int8)
    train_noise_label_list = train_noise_label_list.astype(np.int8)

    ## np.save
    np.savez('clean_data', **{'train_data': train_features, 'train_label': train_true_label_list, \
                              'test_data': test_features, 'test_label': test_true_label_list})

    np.savez('noise_data', **{'train_data': train_features, 'train_label': train_noise_label_list, \
                              'test_data': test_features, 'test_label': test_true_label_list, \
                              'train_confusions': train_confusions, 'test_confusions': test_confusions})

    fileHeader = ["class_name", 'label']
    csvFile = open('class_name', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    for k, v in filter_class.items():
        if k == 'benign': k = 'benign'
        data = [k, v]
        writer.writerow(data)
    csvFile.close()

    fileHeader = ['instance_name']
    csvFile = open('instance_name_train', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    test_str = []
    for i in range(num):
        if i in train_list:
            writer.writerow([raw_name[i]])
        if i in test_list:
            test_str.append(raw_name[i])
    csvFile.close()

    with open('instance_name_test', 'w') as f:
        csv_write = csv.writer(f)
        csv_write.writerow(fileHeader)
        for t_str in test_str:
            csv_write.writerow([t_str])

    csvFile_test.close()

if __name__ == '__main__':
    root = '/home/xkw5132/wuxian/PE_malware_dataset'
    data_file = 'data_ist.csv'
    label_file = 'label_ist.csv'
    #trainset = PE_dataset(root=root, data_file=data_file, label_file=label_file, train=True)
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

    filter_class = change_to_0(filter_class)
    filter_class['benign'] = 0
    filter_class['virlock'] = 1
    write_into_csv(raw_names, raw_labels, flags, filter_class, train_list, test_list, avs, raw_feats)
