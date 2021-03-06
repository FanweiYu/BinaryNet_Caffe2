import numpy as np
import os
import shutil
import utils
import models

from caffe2.python import core, model_helper, net_drawer, workspace, visualize, brew

core.GlobalInit(['caffe2', '--caffe2_log_level=0'])
print("Necessities imported!")

#################
# Prepare data

utils.PrepareDataset()


############################
# Start constructing models

arg_scope = {"order": "NCHW"}
train_model = model_helper.ModelHelper(name="mnist_train", arg_scope=arg_scope)

data, label = models.AddInput(
    train_model, batch_size=64,
    db=os.path.join(utils.data_folder, 'mnist-train-nchw-leveldb'),
    db_type='leveldb')
softmax = models.AddLeNetModel(train_model, data)
models.AddTrainingOperators(train_model, softmax, label)
models.AddBookkeepingOperators(train_model)

# Testing model. We will set the batch size to 100, so that the testing
# pass is 100 iterations (10,000 images in total).
# For the testing model, we need the data input part, the main LeNetModel
# part, and an accuracy part. Note that init_params is set False because
# we will be using the parameters obtained from the train model.
test_model = model_helper.ModelHelper(
    name="mnist_test", arg_scope=arg_scope, init_params=False)
data, label = models.AddInput(
    test_model, batch_size=100,
    db=os.path.join(utils.data_folder, 'mnist-test-nchw-leveldb'),
    db_type='leveldb')
softmax = models.AddLeNetModel(test_model, data)
models.AddAccuracy(test_model, softmax, label)

print(str(train_model.param_init_net.Proto()) + '\n...')

print('Training...')
# The parameter initialization network only needs to be run once.
workspace.RunNetOnce(train_model.param_init_net)
# creating the network
workspace.CreateNet(train_model.net, overwrite=True)
# set the number of iterations and track the accuracy & loss
total_iters = 200
accuracy = np.zeros(total_iters)
loss = np.zeros(total_iters)
# Now, we will manually run the network for 200 iterations. 
for i in range(total_iters):
    workspace.RunNet(train_model.net)
    accuracy[i] = workspace.FetchBlob('accuracy')
    loss[i] = workspace.FetchBlob('loss')
    print('iter {0} loss = {1} '.format(i, loss[i]))
    print('         accuracy = {0} '.format(accuracy[i]))

# run a test pass on the test net
print('Testing...')
test_model.params = train_model.params # TODO : correctly init test model
workspace.RunNetOnce(test_model.param_init_net)
workspace.CreateNet(test_model.net, overwrite=True)
test_accuracy = np.zeros(100)
for i in range(100):
    workspace.RunNet(test_model.net.Proto().name)
    test_accuracy[i] = workspace.FetchBlob('accuracy')

print('average test accuracy = {0}'.format(np.mean(test_accuracy)))


