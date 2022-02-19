import pandas as pd
from ast import literal_eval
import csv
import numpy as np

def process(feature):
    feat = feature[1:-1]
    digits = feat.split(',')
    matrix = [int(str) for str in digits]
    return np.array(matrix)


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
        if v <= 30:
            continue
        else:
            filter_class[k] = v
            filter_list[k] = class_to_list[k]

    for k, v in filter_class.items():
        total += v
    print('total is ', total)

    return filter_class, filter_list

def change_to_0(filter_class):
    one_class = {}
    t = 0
    for k, v in filter_class.items():
        one_class[k] = t
        t += 1
    return one_class

def write_into_csv(raw_name, raw_labels, flags, filter_class, av_class, raw_feats):

    num = len(raw_labels)
    features = []
    labels_list = []

    filter_list = []

    for i in range(num):
        feat = process(raw_feats[i])
        if not isinstance(raw_labels[i], str):
            label = 'benign'
        else:
            if flags[i] == 2:
                label = 'benign'
            else:
                labels = literal_eval(raw_labels[i])
                label = labels[0][0]
        if label in filter_class:
            features.append(feat)
            label = filter_class[label]
            labels_list.append(label)
            filter_list.append(i)

    confusions = []

    fileHeader = ["multi_annotator"]
    csvFile = open('multi_annotator', 'w')
    writer = csv.writer(csvFile)
    writer.writerow(fileHeader)


    for i in range(num):
        if i in filter_list:
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
            writer.writerow([noise_label])
            confusions.append(confusion[filter_class[true_label]])

    csvFile.close()
    confusions = np.vstack(confusions)
    features = np.vstack(features)
    labels = np.array(labels_list)

    np.savez('clean_full_data', **{'data':features, 'label':labels, "confusions":confusions})

    with open('instance_name', 'w') as f:
        csv_write = csv.writer(f)
        fileHeader = ['instance_name']
        csv_write.writerow(fileHeader)

        for i in range(num):
            if i in filter_list:
                csv_write.writerow([raw_names[i]])

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

    feats = pd.read_csv(root + '/' + data_file)
    raw_feats = feats.iloc[:, 2].values

    filter_class, filter_list = go_class(raw_labels, flags)
    filter_class = change_to_0(filter_class)
    filter_class['virlock'] = 3
    filter_class['benign'] = 0
    write_into_csv(raw_names, raw_labels, flags, filter_class, avs, raw_feats)
