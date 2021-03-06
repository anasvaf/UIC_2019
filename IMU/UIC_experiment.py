import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from keras.utils import to_categorical
import matplotlib.pyplot as plt
import matplotlib
#local imports
import Classifiers
import UCI_HAR_Dataset as UCI_HAR
from os.path import expanduser
#get actual home path for current user
home = expanduser("~")


#change this to point UCI_HAR data path
ucihar_datapath = home+"/python/data/UCI_HAR_Dataset/"

classes = ["WALKING", "W. UPSTAIRS", "W. DOWNSTAIRS", "SITTING", "STANDING", "LAYING"]

#Load HC features info from UCI-HAR dataset
features_desc_df = pd.read_csv(ucihar_datapath+"/features.txt", sep='\s',engine='python',names=['feat_id','feat_name'])
#print(features_desc_df.head())
#All HC features (561)
feat_names = features_desc_df['feat_name'].values.tolist()
#Only ACC features: excluding GYRO
exp_feat_names = []
for name in feat_names:
	if  not "Gyro" in name:
		exp_feat_names.append(name)
#Time domain features
time_feat_names = []
for name in feat_names:
	if  not "fBody" in name:
		time_feat_names.append(name)

#Only Body component
body_feat_names = []
for name in feat_names:
	if not "ravity" in name:
		body_feat_names.append(name)

#print(feat_names[0]," ",feat_names[1])
print("N. of features: ACC only ",len(exp_feat_names)," - ALL ",len(feat_names), " - TIME only ",len(time_feat_names), " - BODY only ", len(body_feat_names))


#auto features names f1, f2 ..
auto_feats_names = []
for i in range(768):
	auto_feats_names.append("f"+str(i))


def train_test_AutoCNN_IMU(datapath):
	clf = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=32,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k32(name="3CNN_k32")
	X_train, labels_train, list_ch_train = UCI_HAR.read_IMU_data(data_path=datapath, split="train") # train
	X_test, labels_test, list_ch_test = UCI_HAR.read_IMU_data(data_path=datapath, split="test") # test
	assert list_ch_train == list_ch_test, "Mistmatch in channels!"
	X_train, X_test = UCI_HAR.standardize(X_train, X_test)
	print("Data size:", len(X_train), " - ", len(X_train[0]))
	#clf = Classifiers.Hybrid_CNN_MLP(patience=200,name="CNN_3_Layers")
	clf.loadBestWeights()
	auto_features_train = clf.get_layer_output(X_train,"automatic_features")
	auto_features_test = clf.get_layer_output(X_test,"automatic_features")
	print("Features shape: ",auto_features_train.shape)
	#input("pause here. Set inout size on classifier")
	#auto_feats_df = pd.DataFrame(auto_features,columns=auto_feats_names)
	#print(auto_feats_df.head())
	#auto_feats_df.to_csv('auto_train_features_'+clf_name+'.csv.gz',compression='gzip',index=False,header=None)
	#train_X_df = pd.read_csv("auto_train_features_"+cnn+".csv.gz",names=auto_feats_names,header=None,sep=",",engine='python',compression='gzip')
	#train_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
	#test_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
	X_tr, X_vld, lab_tr, lab_vld = train_test_split(auto_features_train, labels_train, test_size=0.1, stratify = labels_train)#, random_state = 123)
	lab_tr[:] = [ y -1 for y in lab_tr ]
	lab_vld[:] = [ y -1 for y in lab_vld ]
	labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
	y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
	y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
	y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
	clf_NN_HC = Classifiers.UCI_AUTOCNN_IMU_HC(patience=200,name="CNN_AUTO_FINAL")
	all_predictions = []
	all_test = []
	for k in range(5):
		clf_NN_HC.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_NN_HC.loadBestWeights()
		predictions = clf_NN_HC.predict(auto_features_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions.extend(predictions_inv)
		all_test.extend(labels_test)
	clf_NN_HC.printClassificationReport(true=all_test,pred=all_predictions,classes=classes,filename="AUTOCNN_IMU_FINAL_classification_report.txt")
	clf_NN_HC.plotConfusionMatrix(true=all_test,pred=all_predictions,classes=classes,showGraph=False,saveFig=True,filename="AUTOCNN_IMU_FINAL_CM.png")
	clf_NN_HC.printAccuracyScore(true=all_test,pred=all_predictions,filename="AUTOCNN_IMU_FINAL_classification_accuracy.txt")

def train_NN_ACC_HC(datapath):
	all_train_X_df = pd.read_csv(datapath+"train/X_train.txt",names=feat_names,header=None,sep="\s+",engine='python')
	train_X_df = all_train_X_df[exp_feat_names]
	train_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
	all_test_X_df = pd.read_csv(datapath+"test/X_test.txt",names=feat_names,header=None,sep="\s+",engine='python')
	test_X_df = all_test_X_df[exp_feat_names]
	test_y_df = pd.read_csv(datapath+"test/y_test.txt",names=['label'],header=None)
	labels_train = train_y_df['label'].values
	labels_test = test_y_df['label'].values
	#UCI_NN_HC
	X_train = train_X_df.values
	X_test = test_X_df.values
	#labels_train = train_y_df.values
	X_tr, X_vld, lab_tr, lab_vld = train_test_split(X_train, labels_train, test_size=0.1, stratify = labels_train)#, random_state = 123)
	lab_tr[:] = [ y -1 for y in lab_tr ]
	lab_vld[:] = [ y -1 for y in lab_vld ]
	labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
	y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
	y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
	y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
	clf_NN_HC = Classifiers.UCI_NN_ACC_HC(patience=200,name="NN_ACC_HC")
	clf_NN_HC.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
	clf_NN_HC.loadBestWeights()
	predictions = clf_NN_HC.predict(X_test,batch_size=1)
	predictions_inv = [ [np.argmax(x)] for x in predictions]
	clf_NN_HC.printClassificationReport(true=labels_test,pred=predictions_inv,classes=classes,filename="NN_ACC_HC_classification_report.txt")
	clf_NN_HC.plotConfusionMatrix(true=labels_test,pred=predictions_inv,classes=classes,showGraph=False,saveFig=True,filename="NN_ACC_HC_CM.png")
	clf_NN_HC.printAccuracyScore(true=labels_test,pred=predictions_inv,filename="NN_ACC_HC_classification_accuracy.txt")

def train_NN_IMU_HC(datapath):
	all_labels_test = []
	all_predictions = []
	for k in range(10):
		all_train_X_df = pd.read_csv(datapath+"train/X_train.txt",names=feat_names,header=None,sep="\s+",engine='python')
		train_X_df = all_train_X_df[feat_names]
		train_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
		all_test_X_df = pd.read_csv(datapath+"test/X_test.txt",names=feat_names,header=None,sep="\s+",engine='python')
		test_X_df = all_test_X_df[feat_names]
		test_y_df = pd.read_csv(datapath+"test/y_test.txt",names=['label'],header=None)
		labels_train = train_y_df['label'].values
		labels_test = test_y_df['label'].values
		#UCI_NN_HC
		X_train = train_X_df.values
		X_test = test_X_df.values
		#labels_train = train_y_df.values
		X_tr, X_vld, lab_tr, lab_vld = train_test_split(X_train, labels_train, test_size=0.1, stratify = labels_train)
		lab_tr[:] = [ y -1 for y in lab_tr ]
		lab_vld[:] = [ y -1 for y in lab_vld ]
		labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
		all_labels_test.extend(labels_test)
		y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
		y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
		y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
		clf_NN_HC = Classifiers.UCI_NN_IMU_HC(patience=200,name="NN_HC")
		clf_NN_HC.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_NN_HC.loadBestWeights()
		predictions = clf_NN_HC.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions.extend(predictions_inv)
	clf_NN_HC = Classifiers.UCI_NN_IMU_HC(patience=200,name="NN_HC")
	clf_NN_HC.printClassificationReport(true=labels_test,pred=predictions_inv,classes=classes,filename="NN_IMU_HC_classification_report.txt")
	clf_NN_HC.plotConfusionMatrix(true=labels_test,pred=predictions_inv,classes=classes,showGraph=False,saveFig=True,filename="NN_IMU_HC_CM.png")
	clf_NN_HC.printAccuracyScore(true=labels_test,pred=predictions_inv,filename="NN_IMU_HC_classification_accuracy.txt")

def train_NN_BODY_HC(datapath):
	all_train_X_df = pd.read_csv(datapath+"train/X_train.txt",names=feat_names,header=None,sep="\s+",engine='python')
	train_X_df = all_train_X_df[body_feat_names]
	train_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
	all_test_X_df = pd.read_csv(datapath+"test/X_test.txt",names=feat_names,header=None,sep="\s+",engine='python')
	test_X_df = all_test_X_df[body_feat_names]
	test_y_df = pd.read_csv(datapath+"test/y_test.txt",names=['label'],header=None)
	labels_train = train_y_df['label'].values
	labels_test = test_y_df['label'].values
	#UCI_NN_HC
	X_train = train_X_df.values
	X_test = test_X_df.values
	#labels_train = train_y_df.values
	X_tr, X_vld, lab_tr, lab_vld = train_test_split(X_train, labels_train, test_size=0.1, stratify = labels_train)#, random_state = 123)
	lab_tr[:] = [ y -1 for y in lab_tr ]
	lab_vld[:] = [ y -1 for y in lab_vld ]
	labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
	y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
	y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
	y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
	clf_NN_HC = Classifiers.UCI_NN_BODY_HC(patience=200,name="NN_BODY_HC")
	clf_NN_HC.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
	clf_NN_HC.loadBestWeights()
	predictions = clf_NN_HC.predict(X_test,batch_size=1)
	predictions_inv = [ [np.argmax(x)] for x in predictions]
	clf_NN_HC.printClassificationReport(true=labels_test,pred=predictions_inv,classes=classes,filename="NN_BODY_HC_classification_report.txt")
	clf_NN_HC.plotConfusionMatrix(true=labels_test,pred=predictions_inv,classes=classes,showGraph=False,saveFig=True,filename="NN_BODY_HC_CM.png")
	clf_NN_HC.printAccuracyScore(true=labels_test,pred=predictions_inv,filename="NN_BODY_HC_classification_accuracy.txt")

def train_NN_TIME_HC(datapath):
	all_train_X_df = pd.read_csv(datapath+"train/X_train.txt",names=feat_names,header=None,sep="\s+",engine='python')
	train_X_df = all_train_X_df[time_feat_names]
	train_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
	all_test_X_df = pd.read_csv(datapath+"test/X_test.txt",names=feat_names,header=None,sep="\s+",engine='python')
	test_X_df = all_test_X_df[time_feat_names]
	test_y_df = pd.read_csv(datapath+"test/y_test.txt",names=['label'],header=None)
	labels_train = train_y_df['label'].values
	labels_test = test_y_df['label'].values
	#UCI_NN_HC
	X_train = train_X_df.values
	X_test = test_X_df.values
	#labels_train = train_y_df.values
	X_tr, X_vld, lab_tr, lab_vld = train_test_split(X_train, labels_train, test_size=0.1, stratify = labels_train)#, random_state = 123)
	lab_tr[:] = [ y -1 for y in lab_tr ]
	lab_vld[:] = [ y -1 for y in lab_vld ]
	labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
	y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
	y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
	y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
	clf_NN_HC = Classifiers.UCI_NN_TIME_HC(patience=200,name="NN_TIME_HC")
	clf_NN_HC.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
	clf_NN_HC.loadBestWeights()
	predictions = clf_NN_HC.predict(X_test,batch_size=1)
	predictions_inv = [ [np.argmax(x)] for x in predictions]
	clf_NN_HC.printClassificationReport(true=labels_test,pred=predictions_inv,classes=classes,filename="NN_TIME_HC_classification_report.txt")
	clf_NN_HC.plotConfusionMatrix(true=labels_test,pred=predictions_inv,classes=classes,showGraph=False,saveFig=True,filename="NN_TIME_HC_CM.png")
	clf_NN_HC.printAccuracyScore(true=labels_test,pred=predictions_inv,filename="NN_TIME_HC_classification_accuracy.txt")
	
def train_CNN_IMU_24filters(datapath):
	#print("Data size:", len(X_train), " - ", len(X_train[0]))
	all_labels_test = []
	all_predictions = []
	### Init 10 fold validation
	for k in range(5):
		X_train, labels_train, list_ch_train = UCI_HAR.read_IMU_data(data_path=datapath, split="train") # train
		X_test, labels_test, list_ch_test = UCI_HAR.read_IMU_data(data_path=datapath, split="test") # test
		assert list_ch_train == list_ch_test, "Mismatch in channels!"
		X_train, X_test = UCI_HAR.standardize(X_train, X_test)
		X_tr, X_vld, lab_tr, lab_vld = train_test_split(X_train, labels_train, test_size=0.1, stratify = labels_train )
		lab_tr[:] = [ y -1 for y in lab_tr ]
		lab_vld[:] = [ y -1 for y in lab_vld ]
		labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
		all_labels_test.extend(labels_test)
		y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
		y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
		y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
		clf_3CNN_k32 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=32,divide_kernel_size=True,num_filters=24)#Classifiers.Hybrid_1CNN_k2(patience=200,name="1CNN_k2")
		clf_3CNN_k32.fit(X_tr,y_tr,X_vld,y_vld,batch_size=512,epochs=150)
		clf_3CNN_k32.loadBestWeights()
		predictions = clf_3CNN_k32.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions.extend(predictions_inv)
	clf_report = Classifiers.ACC_CNN(patience=200,layers=3,kern_size=64,divide_kernel_size=True)
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions,classes=classes,filename="5_fold_3CNN_k32_24f_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions,classes=classes,showGraph=False,saveFig=True,filename="5_fold_3CNN_k32_24f_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions,filename="5_fold_3CNN_k32_24f_classification_accuracy.txt")


def train_CNN_ACC_feature_extractor(datapath):
	#print("Data size:", len(X_train), " - ", len(X_train[0]))
	all_labels_test = []
	all_predictions_1CNN_k2 = []
	all_predictions_2CNN_k2 = []
	all_predictions_3CNN_k2 = []
	all_predictions_4CNN_k2 = []
	all_predictions_3CNN_k8 = []
	all_predictions_3CNN_k16 = []
	all_predictions_3CNN_k32 = []
	all_predictions_3CNN_k64 = []
	### Init 10 fold validation
	for k in range(5):
		X_train, labels_train, list_ch_train = UCI_HAR.read_ACC_data(data_path=datapath, split="train") # train
		X_test, labels_test, list_ch_test = UCI_HAR.read_ACC_data(data_path=datapath, split="test") # test
		assert list_ch_train == list_ch_test, "Mismatch in channels!"
		X_train, X_test = UCI_HAR.standardize(X_train, X_test)
		X_tr, X_vld, lab_tr, lab_vld = train_test_split(X_train, labels_train, test_size=0.1, stratify = labels_train )
		lab_tr[:] = [ y -1 for y in lab_tr ]
		lab_vld[:] = [ y -1 for y in lab_vld ]
		labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
		all_labels_test.extend(labels_test)
		y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
		y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
		y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
		#Now doing CNN layers exploration - Layers: 1 - 2 - 3 - 4 and kernel_size = 2
		#1 CNN layer
		clf_1CNN_k2 = Classifiers.ACC_CNN(patience=200,layers=1,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_1CNN_k2(patience=200,name="1CNN_k2")
		clf_1CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_1CNN_k2.loadBestWeights()
		predictions = clf_1CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_1CNN_k2.extend(predictions_inv)
		#2 layers
		clf_2CNN_k2 = Classifiers.ACC_CNN(patience=200,layers=2,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_2CNN_k2(patience=200,name="2CNN_k2")
		clf_2CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_2CNN_k2.loadBestWeights()
		predictions = clf_2CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_2CNN_k2.extend(predictions_inv)
		#3 layers
		clf_3CNN_k2 = Classifiers.ACC_CNN(patience=200,layers=3,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_3CNN_k2(patience=200,name="3CNN_k2")
		clf_3CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k2.loadBestWeights()
		predictions = clf_3CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k2.extend(predictions_inv)
		#4 layers
		clf_4CNN_k2 = Classifiers.ACC_CNN(patience=200,layers=4,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_4CNN_k2(patience=200,name="4CNN_k2")
		clf_4CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_4CNN_k2.loadBestWeights()
		predictions = clf_4CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_4CNN_k2.extend(predictions_inv)
		##kernel size exploration - Kernels: 2 - 8 - 16 - 32 - 64
		#kernel 8
		clf_3CNN_k8 = Classifiers.ACC_CNN(patience=200,layers=3,kern_size=8,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k8(patience=200,name="3CNN_k8")
		clf_3CNN_k8.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k8.loadBestWeights()
		predictions = clf_3CNN_k8.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k8.extend(predictions_inv)
		#kernel 16
		clf_3CNN_k16 = Classifiers.ACC_CNN(patience=200,layers=3,kern_size=16,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k16(patience=200,name="3CNN_k16")
		clf_3CNN_k16.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k16.loadBestWeights()
		predictions = clf_3CNN_k16.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k16.extend(predictions_inv)
		#kernel 32
		clf_3CNN_k32 = Classifiers.ACC_CNN(patience=200,layers=3,kern_size=32,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k32(patience=200,name="3CNN_k32")
		clf_3CNN_k32.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k32.loadBestWeights()
		predictions = clf_3CNN_k32.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k32.extend(predictions_inv)
		#kernel 64
		clf_3CNN_k64 = Classifiers.ACC_CNN(patience=200,layers=3,kern_size=64,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k64(patience=200,name="3CNN_k64")
		clf_3CNN_k64.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k64.loadBestWeights()
		predictions = clf_3CNN_k64.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k64.extend(predictions_inv)

	clf_report = Classifiers.ACC_CNN(patience=200,layers=3,kern_size=64,divide_kernel_size=True)
	print(np.unique(all_labels_test)," - ",np.unique(all_predictions_1CNN_k2))
	#1 layer
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_1CNN_k2,classes=classes,filename="10_fold_1CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_1CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="10_fold_1CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_1CNN_k2,filename="10_fold_1CNN_k2_classification_accuracy.txt")
	# 2 layers
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_2CNN_k2,classes=classes,filename="10_fold_2CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_2CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="10_fold_2CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_2CNN_k2,filename="10_fold_2CNN_k2_classification_accuracy.txt")
	#3 layers
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k2,classes=classes,filename="10_fold_3CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="10_fold_3CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k2,filename="10_fold_3CNN_k2_classification_accuracy.txt")
	#4 layers
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_4CNN_k2,classes=classes,filename="10_fold_4CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_4CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="10_fold_4CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_4CNN_k2,filename="10_fold_4CNN_k2_classification_accuracy.txt")
	#3 layers k 8
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k8,classes=classes,filename="10_fold_3CNN_k8_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k8,classes=classes,showGraph=False,saveFig=True,filename="10_fold_3CNN_k8_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k8,filename="10_fold_3CNN_k8_classification_accuracy.txt")
	#3 layers k 16
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k16,classes=classes,filename="10_fold_3CNN_k16_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k16,classes=classes,showGraph=False,saveFig=True,filename="10_fold_3CNN_k16_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k16,filename="10_fold_3CNN_k16_classification_accuracy.txt")
	#3 layers k 32
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k32,classes=classes,filename="10_fold_3CNN_k32_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k32,classes=classes,showGraph=False,saveFig=True,filename="10_fold_3CNN_k32_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k32,filename="10_fold_3CNN_k32_classification_accuracy.txt")
	#3 layers k 64
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k64,classes=classes,filename="10_fold_3CNN_k64_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k64,classes=classes,showGraph=False,saveFig=True,filename="10_fold_3CNN_k64_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k64,filename="10_fold_3CNN_k64_classification_accuracy.txt")

def train_CNN_IMU_feature_extractor(datapath):
	#print("Data size:", len(X_train), " - ", len(X_train[0]))
	all_labels_test = []
	all_predictions_1CNN_k2 = []
	all_predictions_2CNN_k2 = []
	all_predictions_3CNN_k2 = []
	all_predictions_4CNN_k2 = []
	all_predictions_3CNN_k8 = []
	all_predictions_3CNN_k16 = []
	all_predictions_3CNN_k32 = []
	all_predictions_3CNN_k64 = []
	all_predictions_4CNN_k16 = []
	all_predictions_4CNN_k32 = []
	all_predictions_4CNN_k64 = []
	### Init 10 fold validation
	for k in range(5):
		X_train, labels_train, list_ch_train = UCI_HAR.read_IMU_data(data_path=datapath, split="train") # train
		X_test, labels_test, list_ch_test = UCI_HAR.read_IMU_data(data_path=datapath, split="test") # test
		assert list_ch_train == list_ch_test, "Mismatch in channels!"
		X_train, X_test = UCI_HAR.standardize(X_train, X_test)
		X_tr, X_vld, lab_tr, lab_vld = train_test_split(X_train, labels_train, test_size=0.1, stratify = labels_train)#, random_state = 123)
		lab_tr[:] = [ y -1 for y in lab_tr ]
		lab_vld[:] = [ y -1 for y in lab_vld ]
		labels_test[:] = [ y -1 for y in labels_test ] #labels [1-6] -> [0-5]
		all_labels_test.extend(labels_test)
		y_tr = to_categorical(lab_tr,num_classes=6)#one_hot(lab_tr)
		y_vld = to_categorical(lab_vld,num_classes=6)#one_hot(lab_vld)
		y_test = to_categorical(labels_test,num_classes=6)#one_hot(labels_test)
		#Now doing CNN layers exploration - Layers: 1 - 2 - 3 - 4 and kernel_size = 2
		#1 CNN layer
		clf_1CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=1,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_1CNN_k2(patience=200,name="1CNN_k2")
		clf_1CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_1CNN_k2.loadBestWeights()
		predictions = clf_1CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_1CNN_k2.extend(predictions_inv)
		#2 layers
		clf_2CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=2,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_2CNN_k2(patience=200,name="2CNN_k2")
		clf_2CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_2CNN_k2.loadBestWeights()
		predictions = clf_2CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_2CNN_k2.extend(predictions_inv)
		#3 layers
		clf_3CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_3CNN_k2(patience=200,name="3CNN_k2")
		clf_3CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k2.loadBestWeights()
		predictions = clf_3CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k2.extend(predictions_inv)
		#4 layers
		clf_4CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=4,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_4CNN_k2(patience=200,name="4CNN_k2")
		clf_4CNN_k2.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_4CNN_k2.loadBestWeights()
		predictions = clf_4CNN_k2.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_4CNN_k2.extend(predictions_inv)
		##kernel size exploration - Kernels: 2 - 8 - 16 - 32 - 64
		#kernel 8
		clf_3CNN_k8 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=8,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k8(patience=200,name="3CNN_k8")
		clf_3CNN_k8.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k8.loadBestWeights()
		predictions = clf_3CNN_k8.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k8.extend(predictions_inv)
		#kernel 16
		clf_3CNN_k16 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=16,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k16(patience=200,name="3CNN_k16")
		clf_3CNN_k16.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k16.loadBestWeights()
		predictions = clf_3CNN_k16.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k16.extend(predictions_inv)
		#kernel 32
		clf_3CNN_k32 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=32,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k32(patience=200,name="3CNN_k32")
		clf_3CNN_k32.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k32.loadBestWeights()
		predictions = clf_3CNN_k32.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k32.extend(predictions_inv)
		#kernel 64
		clf_3CNN_k64 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=64,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k64(patience=200,name="3CNN_k64")
		clf_3CNN_k64.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_3CNN_k64.loadBestWeights()
		predictions = clf_3CNN_k64.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_3CNN_k64.extend(predictions_inv)
		#4 layers different k
		##kernel size exploration - Kernels: 2 - 8 - 16 - 32 - 64
		#kernel 16
		clf_4CNN_k16 = Classifiers.IMU_CNN(patience=200,layers=4,kern_size=16,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k8(patience=200,name="3CNN_k8")
		clf_4CNN_k16.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_4CNN_k16.loadBestWeights()
		predictions = clf_4CNN_k16.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_4CNN_k16.extend(predictions_inv)
		#kernel 32
		clf_4CNN_k32 = Classifiers.IMU_CNN(patience=200,layers=4,kern_size=32,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k32(patience=200,name="3CNN_k32")
		clf_4CNN_k32.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_4CNN_k32.loadBestWeights()
		predictions = clf_4CNN_k32.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_4CNN_k32.extend(predictions_inv)
		#kernel 64
		clf_4CNN_k64 = Classifiers.IMU_CNN(patience=200,layers=4,kern_size=64,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k64(patience=200,name="3CNN_k64")
		clf_4CNN_k64.fit(X_tr,y_tr,X_vld,y_vld,batch_size=1024,epochs=150)
		clf_4CNN_k64.loadBestWeights()
		predictions = clf_4CNN_k64.predict(X_test,batch_size=1)
		predictions_inv = [ [np.argmax(x)] for x in predictions]
		all_predictions_4CNN_k64.extend(predictions_inv)


	clf_report = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=64,divide_kernel_size=True)
	print(np.unique(all_labels_test)," - ",np.unique(all_predictions_1CNN_k2))
	#1 layer
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_1CNN_k2,classes=classes,filename="IMU_10_fold_1CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_1CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_1CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_1CNN_k2,filename="IMU_10_fold_1CNN_k2_classification_accuracy.txt")
	# 2 layers
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_2CNN_k2,classes=classes,filename="IMU_10_fold_2CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_2CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_2CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_2CNN_k2,filename="IMU_10_fold_2CNN_k2_classification_accuracy.txt")
	#3 layers
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k2,classes=classes,filename="IMU_10_fold_3CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_3CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k2,filename="IMU_10_fold_3CNN_k2_classification_accuracy.txt")
	#4 layers
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_4CNN_k2,classes=classes,filename="IMU_10_fold_4CNN_k2_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_4CNN_k2,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_4CNN_k2_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_4CNN_k2,filename="IMU_10_fold_4CNN_k2_classification_accuracy.txt")
	#3 layers k 8
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k8,classes=classes,filename="IMU_10_fold_3CNN_k8_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k8,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_3CNN_k8_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k8,filename="IMU_10_fold_3CNN_k8_classification_accuracy.txt")
	#3 layers k 16
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k16,classes=classes,filename="IMU_10_fold_3CNN_k16_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k16,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_3CNN_k16_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k16,filename="IMU_10_fold_3CNN_k16_classification_accuracy.txt")
	#3 layers k 32
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k32,classes=classes,filename="IMU_10_fold_3CNN_k32_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k32,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_3CNN_k32_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k32,filename="IMU_10_fold_3CNN_k32_classification_accuracy.txt")
	#3 layers k 64
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_3CNN_k64,classes=classes,filename="IMU_10_fold_3CNN_k64_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_3CNN_k64,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_3CNN_k64_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_3CNN_k64,filename="IMU_10_fold_3CNN_k64_classification_accuracy.txt")
	#4 layers k 16
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_4CNN_k16,classes=classes,filename="IMU_10_fold_4CNN_k16_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_4CNN_k16,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_4CNN_k16_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_4CNN_k16,filename="IMU_10_fold_4CNN_k16_classification_accuracy.txt")
	#3 layers k 32
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_4CNN_k32,classes=classes,filename="IMU_10_fold_4CNN_k32_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_4CNN_k32,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_4CNN_k32_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_4CNN_k32,filename="IMU_10_fold_4CNN_k32_classification_accuracy.txt")
	#3 layers k 64
	clf_report.printClassificationReport(true=all_labels_test,pred=all_predictions_4CNN_k64,classes=classes,filename="IMU_10_fold_4CNN_k64_classification_report.txt")
	clf_report.plotConfusionMatrix(true=all_labels_test,pred=all_predictions_4CNN_k64,classes=classes,showGraph=False,saveFig=True,filename="IMU_10_fold_4CNN_k64_CM.png")
	clf_report.printAccuracyScore(true=all_labels_test,pred=all_predictions_4CNN_k64,filename="IMU_10_fold_4CNN_k64_classification_accuracy.txt")


def export_CNN_features(datapath,clf,clf_name):
	X_train, labels_train, list_ch_train = UCI_HAR.read_IMU_data(data_path=datapath, split="train") # train
	X_test, labels_test, list_ch_test = UCI_HAR.read_IMU_data(data_path=datapath, split="test") # test
	assert list_ch_train == list_ch_test, "Mistmatch in channels!"
	X_train, X_test = UCI_HAR.standardize(X_train, X_test)
	print("Data size:", len(X_train), " - ", len(X_train[0]))
	#clf = Classifiers.Hybrid_CNN_MLP(patience=200,name="CNN_3_Layers")
	clf.loadBestWeights()
	auto_features = clf.get_layer_output(X_train,"automatic_features")
	print("Features shape: ",auto_features.shape)
	auto_feats_df = pd.DataFrame(auto_features,columns=auto_feats_names)
	print(auto_feats_df.head())
	auto_feats_df.to_csv('auto_train_features_'+clf_name+'.csv.gz',compression='gzip',index=False,header=None)

def plot_hc_features_PCA(datapath,fontsize):
	font = {'family':'sans-serif', 'size':int(fontsize)}
	matplotlib.rc('font',**font)
	train_X_df = pd.read_csv(datapath+"train/X_train.txt",names=feat_names,header=None,sep="\s+",engine='python')
	train_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
	train_y = train_y_df['label'].values
	pca = PCA(n_components=3, svd_solver='arpack')
	X = train_X_df.values
	reduced_X = pca.fit_transform(X)
	reduced_df = pd.DataFrame(reduced_X,columns=['x','y','z'])
	print(reduced_df.head())
	print(train_y_df.head())
	all_df = pd.merge(reduced_df, train_y_df, on=reduced_df.index, how='inner')
	print(all_df.head())
	print(all_df.tail())
	wal_df = all_df.loc[all_df['label'] == 1]
	wup_df = all_df.loc[all_df['label'] == 2]
	wdo_df = all_df.loc[all_df['label'] == 3]
	sit_df = all_df.loc[all_df['label'] == 4]
	sta_df = all_df.loc[all_df['label'] == 5]
	lay_df = all_df.loc[all_df['label'] == 6]
	wal_df = wal_df[['x','y','z']]
	wup_df = wup_df[['x','y','z']]
	wdo_df = wdo_df[['x','y','z']]
	sit_df = sit_df[['x','y','z']]
	sta_df = sta_df[['x','y','z']]
	lay_df = lay_df[['x','y','z']]
	#fig, (ax0,ax1,ax2) = plt.subplots(nrows=3, figsize=(14, 7))
	fig, (ax0,ax1) = plt.subplots(nrows=2, figsize=(8,5))
	ax0.scatter(sit_df['x'].values,sit_df['y'].values,c="tab:blue",label="Sit",s=4)
	ax0.scatter(sta_df['x'].values,sta_df['y'].values,c="tab:orange",label="Stand",s=4)
	ax0.scatter(wup_df['x'].values,wup_df['y'].values,c="tab:purple",label="W. Upstairs",s=4)
	ax0.scatter(wdo_df['x'].values,wdo_df['y'].values,c="tab:cyan",label="W. Downtairs",s=4)
	#ax0.scatter(lay_df['x'].values,lay_df['y'].values,c="tab:red",label="Lay")
	ax0.scatter(wal_df['x'].values,wal_df['y'].values,c="tab:green",label="Walk",s=4)
	#1st-3rd PCA components
	ax1.scatter(sit_df['x'].values,sit_df['z'].values,c="tab:blue",label="Sit",s=4)
	ax1.scatter(sta_df['x'].values,sta_df['z'].values,c="tab:orange",label="Stand",s=4)
	ax1.scatter(wup_df['x'].values,wup_df['z'].values,c="tab:purple",label="W. Upstairs",s=4)
	ax1.scatter(wdo_df['x'].values,wdo_df['z'].values,c="tab:cyan",label="W. Downtairs",s=4)
	#ax1.scatter(lay_df['x'].values,lay_df['z'].values,c="tab:red",label="Lay")
	ax1.scatter(wal_df['x'].values,wal_df['z'].values,c="tab:green",label="Walk",s=4)
	#plt.title('PCA Human Crafted Features')
	#plt.legend(loc=1)
	#ax0.set_title('PCA components 1 and 2')
	#ax1.set_title('PCA components 1 and 3')
	ax0.set_xlabel("Component 1")
	ax0.set_ylabel("Component 2")
	ax1.set_xlabel("Component 1")
	ax1.set_ylabel("Component 3")
	ax0.legend(loc=1)
	ax1.legend(loc=1)
	fig.tight_layout()
	fig.savefig("PCA_HC_Features_IMU.png",dpi=300)

def plot_features_PCA(datapath,name,fontsize):
	font = {'family':'sans-serif', 'size':int(fontsize)}
	matplotlib.rc('font',**font)
	cnn = name
	train_X_df = pd.read_csv("auto_train_features_"+cnn+".csv.gz",names=auto_feats_names,header=None,sep=",",engine='python',compression='gzip')
	train_y_df = pd.read_csv(datapath+"train/y_train.txt",names=['label'],header=None)
	pca = PCA(n_components=3, svd_solver='arpack')
	X = train_X_df.values
	reduced_X = pca.fit_transform(X)
	reduced_df = pd.DataFrame(reduced_X,columns=['x','y','z'])
	print(reduced_df.head())
	print(train_y_df.head())
	all_df = pd.merge(reduced_df, train_y_df, on=reduced_df.index, how='inner')
	print(all_df.head())
	print(all_df.tail())
	wal_df = all_df.loc[all_df['label'] == 1]
	wup_df = all_df.loc[all_df['label'] == 2]
	wdo_df = all_df.loc[all_df['label'] == 3]
	sit_df = all_df.loc[all_df['label'] == 4]
	sta_df = all_df.loc[all_df['label'] == 5]
	lay_df = all_df.loc[all_df['label'] == 6]
	wal_df = wal_df[['x','y','z']]
	wup_df = wup_df[['x','y','z']]
	wdo_df = wdo_df[['x','y','z']]
	sit_df = sit_df[['x','y','z']]
	sta_df = sta_df[['x','y','z']]
	lay_df = lay_df[['x','y','z']]
	#fig, (ax0,ax1,ax2) = plt.subplots(nrows=3, figsize=(14, 7))
	fig, (ax0,ax1) = plt.subplots(nrows=2)#, figsize=(8,5))
	#plt.title('PCA Auto Features '+cnn)
	ax0.scatter(sit_df['x'].values,sit_df['y'].values,c="tab:blue",label="Sit",s=4)
	ax0.scatter(sta_df['x'].values,sta_df['y'].values,c="tab:orange",label="Stand",s=4)
	ax0.scatter(wup_df['x'].values,wup_df['y'].values,c="tab:purple",label="W. Upstairs",s=4)
	ax0.scatter(wdo_df['x'].values,wdo_df['y'].values,c="tab:cyan",label="W. Downtairs",s=4)
	#ax0.scatter(lay_df['x'].values,lay_df['y'].values,c="tab:red",label="Lay")
	ax0.scatter(wal_df['x'].values,wal_df['y'].values,c="tab:green",label="Walk",s=4)
	#1st-3rd PCA components
	ax1.scatter(sit_df['x'].values,sit_df['z'].values,c="tab:blue",label="Sit",s=4)
	ax1.scatter(sta_df['x'].values,sta_df['z'].values,c="tab:orange",label="Stand",s=4)
	ax1.scatter(wup_df['x'].values,wup_df['z'].values,c="tab:purple",label="W. Upstairs",s=4)
	ax1.scatter(wdo_df['x'].values,wdo_df['z'].values,c="tab:cyan",label="W. Downtairs",s=4)
	#ax1.scatter(lay_df['x'].values,lay_df['z'].values,c="tab:red",label="Lay")
	ax1.scatter(wal_df['x'].values,wal_df['z'].values,c="tab:green",label="Walk",s=4)
	#plt.title('PCA CNN Auto Features')
	#plt.legend(loc=1)
	#ax0.set_title('PCA components 1 and 2 '+cnn)
	#ax1.set_title('PCA components 1 and 3 '+cnn)
	ax0.set_xlabel("Component 1")
	ax0.set_ylabel("Component 2")
	ax1.set_xlabel("Component 1")
	ax1.set_ylabel("Component 3")
	ax0.legend(loc=1)
	ax1.legend(loc=1)
	fig.tight_layout()
	fig.savefig("PCA_Auto_" + name + ".png",dpi=300)

#Simple CLI interface
def mainMenu():
	print("1. Train CNN feature extractor\n2. Extract CNN Auto Features\n3. Plot Auto features PCA\n4. Plot Human Crafted Features PCA\n5. Train Test HC Features\n6. Train 3CNN 24 filters\n7. Train test AutoCNN MLP\n\n Press any other key to exit")
	sel = input("")
	if sel == "1":
		train_CNN_IMU_feature_extractor(ucihar_datapath)
		#train_CNN_ACC_feature_extractor(ucihar_datapath)
		return False
	if sel == "2":
		'''clf_1CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=1,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_1CNN_k2(name="1CNN_k2")
		export_CNN_features(ucihar_datapath,clf_1CNN_k2,"1CNN_k2_IMU")
		clf_2CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=2,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_2CNN_k2(name="2CNN_k2")
		export_CNN_features(ucihar_datapath,clf_2CNN_k2,"2CNN_k2_IMU")
		clf_3CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_3CNN_k2(name="3CNN_k2")
		export_CNN_features(ucihar_datapath,clf_3CNN_k2,"3CNN_k2_IMU")
		clf_4CNN_k2 = Classifiers.IMU_CNN(patience=200,layers=4,kern_size=2,divide_kernel_size=False)#Classifiers.Hybrid_4CNN_k2(name="4CNN_k2")
		export_CNN_features(ucihar_datapath,clf_4CNN_k2,"4CNN_k2_IMU")
		#gen featurs kernel size
		clf_3CNN_k8 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=8,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k8(name="3CNN_k8")
		export_CNN_features(ucihar_datapath,clf_3CNN_k8,"3CNN_k8_IMU")
		clf_3CNN_k16 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=16,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k16(name="3CNN_k16")
		export_CNN_features(ucihar_datapath,clf_3CNN_k16,"3CNN_k16_IMU")'''
		clf_3CNN_k32 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=32,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k32(name="3CNN_k32")
		export_CNN_features(ucihar_datapath,clf_3CNN_k32,"3CNN_k32_IMU")
		#clf_3CNN_k64 = Classifiers.IMU_CNN(patience=200,layers=3,kern_size=64,divide_kernel_size=True)#Classifiers.Hybrid_3CNN_k64(name="3CNN_k64")
		#export_CNN_features(ucihar_datapath,clf_3CNN_k64,"3CNN_k64_IMU")
		return False
	if sel == "3":
		fontsize = input("Font size(13 suggested): ")
		#plot_features_PCA(ucihar_datapath,name="1CNN_k2_IMU",fontsize=fontsize)
		#plot_features_PCA(ucihar_datapath,name="2CNN_k2_IMU",fontsize=fontsize)
		#plot_features_PCA(ucihar_datapath,name="3CNN_k2_IMU",fontsize=fontsize)
		#plot_features_PCA(ucihar_datapath,name="4CNN_k2_IMU",fontsize=fontsize)
		#plot_features_PCA(ucihar_datapath,name="3CNN_k8_IMU",fontsize=fontsize)
		#plot_features_PCA(ucihar_datapath,name="3CNN_k16_IMU",fontsize=fontsize)
		plot_features_PCA(ucihar_datapath,name="3CNN_k32_IMU",fontsize=fontsize)
		#plot_features_PCA(ucihar_datapath,name="3CNN_k64_IMU",fontsize=fontsize)
		return False
	if sel == "4":
		fontsize = input("Font size(13 suggested): ")
		plot_hc_features_PCA(ucihar_datapath,fontsize)
		return False
	if sel == "5":
		train_NN_IMU_HC(ucihar_datapath)
		train_NN_ACC_HC(ucihar_datapath)
		#train_NN_TIME_HC(ucihar_datapath)
		#train_NN_BODY_HC(ucihar_datapath)
		return False
	elif sel == "6":
		train_CNN_IMU_24filters(ucihar_datapath)
		return False
	elif sel == "7":
		train_test_AutoCNN_IMU(ucihar_datapath)
		return False
	else:
		return True

#main CLI application loop
while True:
	if mainMenu():
		break
