import numpy as np

def load_data(noise_path, clean_path, num_class):
    data = np.load(noise_path)
    X_train, y_train = data['X_train'], data['y_train']
    X_test, y_test = data['X_test'], data['y_test']
    data = np.load(clean_path)
    X_clean_train, y_clean_train = data['X_train'], data['y_train']

    total = 0
    total_test = 0

    ratio = np.sum(y_train == y_clean_train) / y_clean_train.shape[0]
    print('total ratio is %f' %( 1- ratio))
    for class_id in range(num_class):
        test_idx = np.where(y_test == class_id)[0]
        total_test += len(test_idx)

        train_idx = np.where(y_train == class_id)[0]
        train_num = len(train_idx)
        total += train_num

        new = len(np.where(y_clean_train == class_id)[0])
        clean_num = np.sum(y_clean_train[train_idx] == class_id)
        noise_ratio = 1 - clean_num * 1.0 / train_num
        possible_class = np.unique(y_clean_train[train_idx])
        for idx in possible_class:
            num = len(np.where(y_clean_train[train_idx] == idx)[0])
            print('idx is %d num is %.3f' %(idx, num / train_num))

        print('class_id: %d noise_ratio: %f test_num: %d total_num: %d clean_num: %d' %(class_id, noise_ratio, len(test_idx), train_num, new))

if __name__ == '__main__':
    load_data('malware_noise.npz', 'malware_true.npz', 12)