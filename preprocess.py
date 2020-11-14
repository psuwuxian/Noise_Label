import pandas as pd
import numpy as np



def delete_some(datasets, feats, raw_feats):

    num = len(raw_feats)
    filt_list = []
    for i in range(num):
        if not isinstance(raw_feats[i], str):
            filt_list.append(i)

    ## remove the datasets
    x = datasets.drop(filt_list, axis=0)
    y = feats.drop(filt_list, axis=0)


    x.to_csv(root + '/label_ist.csv', index=0)
    y.to_csv(root + '/data_ist.csv', index=0)



if __name__ == '__main__':
    root = '/home/xkw5132/wuxian/noise_learning/pre'
    data_file = 'data_fea_ist.csv'
    label_file = 'avclass_label_ist.csv'

    datasets = pd.read_csv(root + '/' + label_file)
    feats = pd.read_csv(root + '/' + data_file)

    raw_feats = feats.iloc[:, 2].values
    delete_some(datasets, feats, raw_feats)

