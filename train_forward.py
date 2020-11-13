import argparse
import os
import time
import math
import json
import torch
import torch.backends.cudnn as cudnn
import torch.nn.functional as F
import torchvision.datasets as dset
import torchvision.transforms as transforms
import numpy as np
from load_corrupted_data import PE_dataset
from PIL import Image
import socket

np.random.seed(1)

parser = argparse.ArgumentParser(description='Trains WideResNet on CIFAR',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# Positional arguments
#parser.add_argument('data_path', type=str, help='Root for the Cifar dataset.')
#parser.add_argument('dataset', type=str, choices=['cifar10', 'cifar100'],
#    help='Choose between CIFAR-10, CIFAR-100.')
# Optimization options


parser.add_argument('--root', type=str,default=None)
parser.add_argument('--data_file', type=str, default=None)
parser.add_argument('--label_file', type=str, default=None)


parser.add_argument('--nosgdr', default=False, action='store_true', help='Turn off SGDR.')
parser.add_argument('--epochs', '-e', type=int, default=75, help='Number of epochs to train.')
parser.add_argument('--batch_size', '-b', type=int, default=128, help='Batch size.')


parser.add_argument('--learning_rate', '-lr', type=float, default=0.1, help='The initial learning rate.')
parser.add_argument('--momentum', '-m', type=float, default=0.9, help='Momentum.')
parser.add_argument('--decay', '-d', type=float, default=0.0005, help='Weight decay (L2 penalty).')
parser.add_argument('--test_bs', type=int, default=256)
parser.add_argument('--schedule', type=int, nargs='+', default=[150, 225],
                    help='Decrease learning rate at these epochs. Use when SGDR is off.')
parser.add_argument('--gamma', type=float, default=0.1, help='LR is multiplied by gamma on schedule.')
# Checkpoints
parser.add_argument('--save', '-s', type=str, default='./', help='Folder to save checkpoints.')
parser.add_argument('--load', '-l', type=str, default='', help='Checkpoint path to resume / test.')
parser.add_argument('--test', '-t', action='store_true', help='Test only flag.')
# Architecture
parser.add_argument('--layers', default=40, type=int, help='total number of layers (default: 28)')
parser.add_argument('--widen-factor', default=2, type=int, help='widen factor (default: 10)')
parser.add_argument('--droprate', default=0.3, type=float, help='dropout probability (default: 0.0)')
parser.add_argument('--nonlinearity', type=str, default='relu', help='Nonlinearity (relu, elu, gelu).')
# Acceleration
parser.add_argument('--ngpu', type=int, default=1, help='0 = CPU.')
parser.add_argument('--prefetch', type=int, default=2, help='Pre-fetching threads.')
# i/o
parser.add_argument('--log', type=str, default='./', help='Log folder.')
args = parser.parse_args()


print()
print("This is on machine:", socket.gethostname())
print()
print(args)
print()

# Init logger
if not os.path.isdir(args.log):
    os.makedirs(args.log)
log = open(os.path.join(args.log, args.dataset + '_log.txt'), 'w')
state = {k: v for k, v in args._get_kwargs()}
state['tt'] = 0      # SGDR variable
state['init_learning_rate'] = args.learning_rate
log.write(json.dumps(state) + '\n')

# Init dataset
if not os.path.isdir(args.data_path):
    os.makedirs(args.data_path)


# Init checkpoints
if not os.path.isdir(args.save):
    os.makedirs(args.save)

# Init model, criterion, and optimizer
net = wrn.WideResNet(args.layers, num_classes, args.widen_factor, dropRate=args.droprate)

print(net)


trainset = PE_dataset(args.root, args.data_file, args.label_file, train=True)
testset = PE_dataset(args.root, args.data_file, args.label_file, train=False)

train_loader = torch.utils.data.DataLoader(trainset, batch_size=args.batch_size, shuffle=True, num_workers=2)
test_loader = torch.utils.data.DataLoader(testset, batch_size=args.batch_size, shuffle=False, num_workers=2)


if args.ngpu > 0:
    net.cuda()

torch.manual_seed(1)
if args.ngpu > 0:
    torch.cuda.manual_seed(1)


optimizer = torch.optim.SGD(net.parameters(), state['learning_rate'], momentum=state['momentum'],
                            weight_decay=state['decay'], nesterov=True)
start_epoch = 0


cudnn.benchmark = True  # fire on all cylinders


# train function (forward, backward, update)
def train(no_correction=True, C_hat_transpose=None):
    net.train()     # enter train mode
    loss_avg = 0.0
    for batch_idx, (data, target, confusions) in enumerate(train_loader):
        data, target, confusions = torch.autograd.Variable(data.cuda()), torch.autograd.Variable(target.cuda()), \
                       torch.autograd.Variable(confusions.cuda())

        # forward
        output = net(data)
        # backward
        optimizer.zero_grad()
        if no_correction:
            loss = F.cross_entropy(output, target)
        else:
            pre1 = torch.index_select(confusions, 1, torch.cuda.LongTensor(target.data))

            # n * d | 
            pre2 = torch.dot(F.softmax(output), pre1)
            loss = -(torch.log(pre2).mean())


        loss.backward()
        optimizer.step()

        # exponential moving average
        loss_avg = loss_avg * 0.2 + loss.data[0] * 0.8

        if args.nosgdr is False:    # Use a cyclic learning rate
            dt = math.pi/float(args.epochs)
            state['tt'] += float(dt)/(len(train_loader.dataset)/float(args.batch_size))
            if state['tt'] >= math.pi - 0.05:
                state['tt'] = math.pi - 0.05
            curT = math.pi/2.0 + state['tt']
            new_lr = args.learning_rate * (1.0 + math.sin(curT))/2.0    # lr_min = 0, lr_max = lr
            state['learning_rate'] = new_lr
            for param_group in optimizer.param_groups:
                param_group['lr'] = state['learning_rate']

    state['train_loss'] = loss_avg


# test function (forward only)
def test():
    net.eval()
    loss_avg = 0.0
    correct = 0
    for batch_idx, (data, target) in enumerate(test_loader):
        data, target = torch.autograd.Variable(data.cuda(), volatile=True),\
                       torch.autograd.Variable(target.cuda(), volatile=True)

        # forward
        output = net(data)
        loss = F.cross_entropy(output, target)

        # accuracy
        pred = output.data.max(1)[1]
        correct += pred.eq(target.data).sum()

        # test loss average
        loss_avg += loss.data[0]

    state['test_loss'] = loss_avg / len(test_loader)
    state['test_accuracy'] = correct / len(test_loader.dataset)


for epoch in range(0, args.epochs):
    state['epoch'] = epoch

    begin_epoch = time.time()
    train(no_correction=False, C_hat_transpose=C_hat_transpose)
    print('Epoch', epoch, '| Time Spent:', round(time.time() - begin_epoch, 2))

    test()

    log.write('%s\n' % json.dumps(state))
    log.flush()
    print(state)

log.close()
