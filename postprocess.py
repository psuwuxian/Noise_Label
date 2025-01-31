import numpy as np

def build_mapping():
    direct_mapping = {}
    jump = [4, 8, 13, 15]
    cnt = 0
    for i in range(16):
        if i in jump: continue
        direct_mapping[i] = cnt
        cnt += 1
    return direct_mapping


def load_data(noise_path, clean_path, num_class):
    data = np.load(noise_path)
    X_train, y_train = data['train_data'], data['train_label']
    X_test, y_test = data['test_data'], data['test_label']
    data = np.load(clean_path)
    X_clean_train, y_clean_train = data['train_data'], data['train_label']
    jump = [4, 8, 13, 15]

    mapping = build_mapping()

    new_train_idx = []
    new_test_idx = []

    for class_id in range(num_class):
        if class_id in jump:
            continue
        test_idx = np.where(y_test == class_id)[0]
        test_num = len(test_idx)
        train_idx = np.where(y_train == class_id)[0]
        train_num = len(train_idx)

        clean_num = np.sum(y_clean_train[train_idx] == class_id)
        noise_num = train_num - clean_num
        noise_ratio = 1 - clean_num * 1.0 / train_num
        print('Class%d noise_ratio: %.2f test_num: %d total_num: %d clean_num: %d' %(class_id, noise_ratio, len(test_idx), train_num, clean_num))
        print(np.unique(y_clean_train[train_idx]))

        # force the noisy ratio down
        if noise_ratio > 0.5:
           noise_num = clean_num * 3
           id = 0
           for p_id in train_idx:
               if y_train[p_id] == y_clean_train[p_id]:
                  new_train_idx.append(p_id)
               else:
                  id += 1
                  if id <= noise_num:
                     new_train_idx.append(p_id)
        elif class_id == 1:
            ret = 800 - noise_num
            id = 0
            for p_id in train_idx:
                if y_train[p_id] != y_clean_train[p_id]:
                    new_train_idx.append(p_id)
                else:
                    id += 1
                    if id <= ret:
                        new_train_idx.append(p_id)
        # force the noisy ratio up
        elif class_id in [2, 5, 6, 9]:
            total = test_num * 4
            ret = total - noise_num
            id = 0
            for p_id in train_idx:
                if y_train[p_id] != y_clean_train[p_id]:
                    new_train_idx.append(p_id)
                else:
                    id += 1
                    if id <= ret:
                        new_train_idx.append(p_id)
        else:
            new_train_idx.extend(train_idx)
        new_test_idx.extend(test_idx[:100])


    final_X_train = X_train[new_train_idx]
    final_y_train = y_train[new_train_idx]

    final_y_train = [mapping[i] for i in final_y_train]
    final_y_train = np.array(final_y_train)

    final_y_clean_train = y_clean_train[new_train_idx]

    final_y_clean_train = [mapping[i] for i in final_y_clean_train]
    final_y_clean_train = np.array(final_y_clean_train)

    final_x_test = X_test[new_test_idx]
    final_y_test = y_test[new_test_idx]
    final_y_test = [mapping[i] for i in final_y_test]

    total = np.vstack((final_X_train, final_x_test))
    mean, std = np.mean(total, 0), np.std(total, 0)
    final_X_train = (final_X_train - mean) /  (std + 1e-8)
    final_x_test = (final_x_test - mean) / (std + 1e-8)

    final_X_train = final_X_train.astype('float32')
    final_x_test = final_x_test.astype('float32')

    np.savez('malware_noise.npz', X_train=final_X_train, y_train=final_y_train, X_test=final_x_test, y_test=final_y_test)
    np.savez('malware_true.npz', X_train=final_X_train, y_train=final_y_clean_train, X_test=final_x_test, y_test=final_y_test)

if __name__ == '__main__':
    load_data('noise_data.npz', 'clean_data.npz', num_class=16)