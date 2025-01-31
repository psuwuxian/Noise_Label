import numpy as np
import pandas as pd
from ast import literal_eval
import csv

def go_class(raw_labels, flags):
    class_to_num, class_to_list = {}, {}
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

    filter_class, filter_list = {}, {}
    for k, v in class_to_num.items():
        if v <= 100 or k == 'dinwod':
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


def class_to_id(filter_class):
    mapping_class = {}
    t = 0
    for k, v in filter_class.items():
        mapping_class[k] = t
        t += 1
    mapping_class['benign'] = 0
    mapping_class['virlock'] = 1
    return mapping_class

def process(feature):
    # format '[xx, xx, ... xx]'
    feat = feature[1:-1]
    digits = feat.split(',')
    matrix = [int(str) for str in digits]
    return np.array(matrix)

def write_into_csv(raw_name, raw_labels, flags, filter_class, train_list, test_list, av_class, raw_feats):
    num = len(raw_labels)
    num_class = len(filter_class)

    train_features, test_features = [], []
    train_true_label_list, test_true_label_list = [], []
    train_noise_label_list = []
    # process for clean-dataset
    for i in range(num):
        if i in train_list or i in test_list:
            if not isinstance(raw_feats[i], str):
                print(raw_feats[i])
            feat = process(raw_feats[i])
            if not isinstance(raw_labels[i], str):
                label = 'benign'
            else:
                if flags[i] == 2:
                    label = 'benign'
                else:
                    labels = literal_eval(raw_labels[i])
                    label = labels[0][0]
            label = filter_class[label]
            if i in train_list:
                train_features.append(feat)
                train_true_label_list.append(label)
            else:
                test_features.append(feat)
                test_true_label_list.append(label)
    # process for noise-dataset
    for i in range(num):
        if i in train_list:
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
                    # assign second label to noisy label
                    if len(noise_label_list) >= 2:
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
            train_noise_label_list.append(filter_class[noise_label])

    output_folder = './constructed_noisy_set'
    # Write into confusion matrix
    fileHeader = ["multi_annotator"]
    csvFile_train = open(output_folder+ '/multi_annotator_train', 'w')
    writer_train = csv.writer(csvFile_train)
    writer_train.writerow(fileHeader)
    csvFile_test = open(output_folder + '/multi_annotator_test', 'w')
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
                writer_train.writerow(data)
            elif i in test_list:
                writer_test.writerow(data)
    csvFile_train.close()
    csvFile_test.close()

    train_confusions = []
    test_confusions = []

    for i in range(num):
        if i in train_list or i in test_list:
            confusion = np.zeros((num_class, num_class), dtype=float)
            for j in range(num_class):
                confusion[j][j] = 1.0
            if isinstance(raw_labels[i], str):
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
                true_label = noise_label[0][0] if flags[i] == 1 else 'benign'

                if len(noise_label) > 1:
                   total = 0
                   for label in noise_label:
                        total += label[1]
                   for label in noise_label:
                        c_label = label[0]
                        confusion[filter_class[true_label]][filter_class[c_label]] = label[1] * 1.0 / total
            else:
                true_label = 'benign'
            if i in train_list:
                train_confusions.append(confusion[filter_class[true_label]])
            elif i in test_list:
                test_confusions.append(confusion[filter_class[true_label]])

    train_confusions,  test_confusions = np.vstack(train_confusions), np.vstack(test_confusions)
    train_features, test_features = np.vstack(train_features), np.vstack(test_features)

    train_true_label_list, test_true_label_list, train_noise_label_list = np.array(train_true_label_list), \
                                                                          np.array(test_true_label_list), np.array(train_noise_label_list)
    # assert check
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

    ## Save Train/Test data
    np.savez('clean_data', **{'train_data': train_features, 'train_label': train_true_label_list, \
                              'test_data': test_features, 'test_label': test_true_label_list})

    np.savez('noise_data', **{'train_data': train_features, 'train_label': train_noise_label_list, \
                              'test_data': test_features, 'test_label': test_true_label_list, \
                              'train_confusions': train_confusions, 'test_confusions': test_confusions})

    # Write into CSV file
    fileHeader = ["class_name", 'label']
    csvFile = open('class_name', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)

    for k, v in filter_class.items():
        data = [k, v]
        writer.writerow(data)
    csvFile.close()

    fileHeader = ['instance_name']
    train_csvFile = open(output_folder + '/instance_name_train', 'w')
    test_csvFile = open(output_folder + '/instance_name_test', 'w')
    train_writer = csv.writer(train_csvFile)
    train_writer.writerow(fileHeader)
    test_writer = csv.writer(test_csvFile)
    test_writer.writerow(fileHeader)

    for i in range(num):
        if i in train_list:
            train_writer.writerow([raw_name[i]])
        elif i in test_list:
            test_writer.writerow([raw_name[i]])
    train_csvFile.close()
    test_csvFile.close()

if __name__ == '__main__':
    root = '/home/xkw5132/wuxian/PE_malware_dataset'
    data_file = 'data_ist.csv'
    label_file = 'label_ist.csv'
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

    filter_class = class_to_id(filter_class)
    write_into_csv(raw_names, raw_labels, flags, filter_class, train_list, test_list, avs, raw_feats)