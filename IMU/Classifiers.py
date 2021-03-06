import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, classification_report, accuracy_score
from keras.models import Sequential, load_model
from keras.callbacks import EarlyStopping, ModelCheckpoint, CSVLogger
from keras import backend as keras_backend
from keras.utils import plot_model
from keras.layers import *
from datetime import datetime
import keras
import seaborn as sn
from os.path import expanduser
#get actual home path for current user
home = expanduser("~")

basepath = home + '/python/data/UCI_HAR_Dataset/keras_logs/'


##Base class
class BaseClassifier:
	def __init__(self,name,patience=25,fontSize=16):
		self.name = name
		font = {'family':'sans-serif', 'size':fontSize}
		matplotlib.rc('font',**font)
		#TensorBoard logger
		RUN_NAME = name + str(datetime.utcnow())
		self.logger = keras.callbacks.TensorBoard( log_dir="logs/"+RUN_NAME+"/", write_graph=True )
		#stop criterion
		self.early_stopping = EarlyStopping(monitor='val_loss',patience=patience)
		self.csv_log_file = basepath+self.name+"_training_log.csv"
		self.csv_logger = CSVLogger(self.csv_log_file)
		#Checkpoint for weights
		#self.bestmodelweights = name+"weights_best_ep_{epoch:02d}_{val_acc:.3f}.hdf5"
		self.bestmodelweights = basepath+ name+"weights_best.hdf5"
		self.checkpoint = ModelCheckpoint(self.bestmodelweights, monitor='val_loss',verbose=1,save_best_only=True, mode='min')
		####Model init specialized in class

	def fit(self,X_tr,y_tr,X_vld,y_vld,batch_size=256,epochs=500,verbose=0):
		self.history = self.model.fit( X_tr, y_tr, validation_data=(X_vld,y_vld), batch_size=batch_size, epochs=epochs, shuffle=False, verbose=2, callbacks = [self.logger, self.early_stopping, self.checkpoint, self.csv_logger] )

	def fit_split_train_test(self,X_tr,y_tr,validation_split=0.1,batch_size=256,epochs=5000,verbose=0):
		self.history = self.model.fit( X_tr, y_tr, validation_split=validation_split,batch_size=batch_size, epochs=epochs, shuffle=False, verbose=2, callbacks = [self.logger, self.early_stopping, self.checkpoint, self.csv_logger] )

	def loadBestWeights(self):
		print(self.checkpoint)
		self.model.load_weights(self.bestmodelweights)
		#self.model.compile( loss='mse', optimizer='adam' )

	def predict(self,X_test,batch_size=32):
		predictions = self.model.predict(X_test,batch_size)
		return predictions

	def save(self):
		self.model.save(basepath+self.name+".h5")

	def load(self):
		self.model = load_model(basepath+self.name+".h5")

	def get_layer_output(self, x, layer_name):
		get_output = keras_backend.function([self.model.layers[0].input], [self.name2layer[layer_name].output])
		output = get_output([x])[0]
		return output

	def plotAccuracy(self,showGraph=True,saveFig=True):
		if not saveFig and not showGraph:
			return
		history_df = pd.read_csv(self.csv_log_file)
		sorted_df = history_df.sort_values('val_acc',ascending=False)
		print(sorted_df.head())
		bst_epoch = 0
		for idx,row in sorted_df.iterrows():
			print("Epoch: ",row['epoch'], " val_acc: ", row['val_acc'])
			checkpoint = row['epoch']
			break
		# Plot training & validation accuracy values
		fig = plt.figure(figsize=(8, 7))
		plt.plot(self.history.history['acc'],linewidth=3.0)
		plt.plot(self.history.history['val_acc'],linewidth=3.0)
		plt.plot((checkpoint,checkpoint),(0.5,1.0),linewidth=2.0,linestyle='--')
		plt.title('Model accuracy')
		plt.ylabel('Accuracy')
		plt.xlabel('Epoch')
		plt.legend(['Train', 'Test','Stop'], loc='upper left')
		if saveFig:
			fig.savefig(basepath+self.name+"_TrainAccuracy.png",dpi=300)
		if showGraph:
			plt.show()


	def plotLoss(self,showGraph=True,saveFig=True):
		if not saveFig and not showGraph:
			return
		history_df = pd.read_csv(self.csv_log_file)
		sorted_df = history_df.sort_values('val_acc',ascending=False)
		print(sorted_df.head())
		bst_epoch = 0
		for idx,row in sorted_df.iterrows():
			print("Epoch: ",row['epoch'], " val_acc: ", row['val_acc'])
			checkpoint = row['epoch']
			break
		# Plot training & validation loss values
		fig = plt.figure(figsize=(8, 7))
		plt.plot(self.history.history['loss'],linewidth=3.0)
		plt.plot(self.history.history['val_loss'],linewidth=3.0)
		plt.plot((checkpoint,checkpoint),(0.5,1.0),linewidth=2.0,linestyle='--')
		plt.title('Model loss')
		plt.ylabel('Loss')
		plt.xlabel('Epoch')
		plt.legend(['Train', 'Test','Stop'], loc='upper left')
		fig.savefig(basepath+self.name+"_TrainLoss.png",dpi=300)
		plt.show()

	def rename(self,name):
		self.name = name
		self.csv_log_file = basepath+self.name+"_training_log.csv"
		self.csv_logger = CSVLogger(self.csv_log_file)
		#Checkpoint for weights
		#self.bestmodelweights = name+"weights_best_ep_{epoch:02d}_{val_acc:.3f}.hdf5"
		self.bestmodelweights = basepath+ name+"weights_best.hdf5"
		self.checkpoint = ModelCheckpoint(self.bestmodelweights, monitor='val_loss',verbose=1,save_best_only=True, mode='min')

	def plotModel(self):
		plot_model(self.model, to_file=self.name+'_model.png')

	def printClassificationReport(self,pred,true,classes,filename=""):
		cr = classification_report(np.array(true), np.array(pred),target_names=classes,digits=4)
		print(cr)
		if not filename == "":
			with open(filename,"w") as out_file:
				out_file.write(cr)

	def printAccuracyScore(self, pred, true,filename=""):
		acc = accuracy_score(np.array(true), np.array(pred))
		print("Accuracy: ",acc)
		if not filename == "":
			with open(filename,"w") as out_file:
				out_file.write(str(acc))

	def plotConfusionMatrix(self,pred,true,classes,saveFig=True,showGraph=False,filename="undefined"):
		cm = confusion_matrix(np.array(true), np.array(pred) )
		fig = plt.figure(figsize=(8, 7))
		cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
		df_cm = pd.DataFrame(cm,index=classes,columns=classes)
		ax = sn.heatmap(df_cm,cmap='Blues',annot=True)
		plt.yticks(rotation=0)
		if showGraph:
			plt.show()
		if saveFig:
			fig.tight_layout()
			if filename == "undefined":
				fig.savefig(self.name+"_CM.png",dpi=300)
			else:
				fig.savefig(filename,dpi=300)

	def reset_states(self):
		self.model.reset_states()

#Classifier using Human Crafted Features (Accelerometer only)
class UCI_NN_ACC_HC(BaseClassifier):
	def __init__(self,patience,name,fontSize=16):
		self.name = name + "_HUMAN_CRAFTED_ACC"
		super().__init__(name,patience,fontSize)
		self.model = Sequential()
		self.model.add( Dense(64,input_dim=348,activation='relu', name="layer_1") )
		self.model.add( Dense(6,activation='linear',  name="output_layer"))
		self.model.compile( loss='mse',metrics=['mse','acc'], optimizer='adam' )
		self.model.summary()

#Classifier using Human Crafted Features (Accelerometer and gyroscope)
class UCI_NN_IMU_HC(BaseClassifier):
	def __init__(self,patience,name,fontSize=16):
		self.name = name + "_HUMAN_CRAFTED_IMU"
		super().__init__(name,patience,fontSize)
		self.model = Sequential()
		self.model.add( Dense(64,input_dim=561,activation='relu', name="layer_1") )
		self.model.add( Dense(6,activation='linear',  name="output_layer"))
		self.model.compile( loss='mse',metrics=['mse','acc'], optimizer='adam' )
		self.model.summary()

#Classifier using Human Crafted Features (Acc+Gyro Time domain only)
class UCI_NN_TIME_HC(BaseClassifier):
	def __init__(self,patience,name,fontSize=16):
		self.name = name + "_HUMAN_CRAFTED_TIME"
		super().__init__(name,patience,fontSize)
		self.model = Sequential()
		self.model.add( Dense(64,input_dim=272,activation='relu', name="layer_1") )
		self.model.add( Dense(6,activation='linear',  name="output_layer"))
		self.model.compile( loss='mse',metrics=['mse','acc'], optimizer='adam' )
		self.model.summary()

#Classifier using Human Crafted Features (ACC Body only, no GRAVITY)
class UCI_NN_BODY_HC(BaseClassifier):
	def __init__(self,patience,name,fontSize=16):
		self.name = name + "_HUMAN_CRAFTED_BODY"
		super().__init__(name,patience,fontSize)
		self.model = Sequential()
		self.model.add( Dense(64,input_dim=501,activation='relu', name="layer_1") )
		self.model.add( Dense(6,activation='linear',  name="output_layer"))
		self.model.compile( loss='mse',metrics=['mse','acc'], optimizer='adam' )
		self.model.summary()

#Classifier using AutoCNN and same structure as HCF
class UCI_AUTOCNN_IMU_HC(BaseClassifier):
	def __init__(self,patience,name,fontSize=16):
		self.name = name + "_HUMAN_CRAFTED_BODY"
		super().__init__(name,patience,fontSize)
		self.model = Sequential()
		self.model.add( Dense(64,input_dim=501,activation='relu', name="layer_1") )
		self.model.add( Dense(6,activation='linear',  name="output_layer"))
		self.model.compile( loss='mse',metrics=['mse','acc'], optimizer='adam' )
		self.model.summary()


#CNN based classifiers

#CNN using ACC only (BODY+GRAVITY input: 128x6)
class ACC_CNN(BaseClassifier):
	def __init__(self,patience,layers=3,kern_size=2,divide_kernel_size=False,fontSize=16):
		self.name = str(layers)+"-CNN_k"+str(kern_size)
		super().__init__(self.name,patience,fontSize)
		self.model = Sequential()
		filters = 12
		self.model.add( Conv1D(filters,input_shape=(128,6),kernel_size=kern_size,padding='same',activation='relu', name="layer_1") )
		self.model.add(MaxPooling1D())
		for i in range(2,layers+1):
			filters = filters*2
			if divide_kernel_size:
				kern_size = int(kern_size / 2)
			layer_name = "layer_"+str(i)
			self.model.add( Conv1D(filters,kernel_size=kern_size,padding='same',activation='relu', name=layer_name) )
			self.model.add(MaxPooling1D())
		#Automatic features
		self.model.add(Flatten(name="automatic_features"))
		#for multilabel DO NOT use softmax use sigmoid
		self.model.add( Dense(64,activation='relu', name="layer_dense") )
		self.model.add( Dense(6,activation='softmax',  name="output_layer"))
		self.model.compile( loss='mse',metrics=['mse','acc'], optimizer='adam' )
		self.model.summary()
		self.name2layer = {}
		for layer in self.model.layers:
			self.name2layer[layer.name] = layer

#CNN using ACC and GYRO (ACC_GRAVITY+ACC_BODY+GYRO input: 128x9)
class IMU_CNN(BaseClassifier):
	def __init__(self,patience,layers=3,kern_size=2,divide_kernel_size=False,fontSize=16,num_filters=12):
		self.name = str(layers)+"-CNN_k"+str(kern_size)+"_IMU"
		super().__init__(self.name,patience,fontSize)
		self.model = Sequential()
		filters = num_filters
		self.model.add( Conv1D(filters,input_shape=(128,9),kernel_size=kern_size,padding='same',activation='relu', name="layer_1") )
		self.model.add(MaxPooling1D())
		for i in range(2,layers+1):
			filters = filters*2
			if divide_kernel_size:
				kern_size = int(kern_size / 2)
			layer_name = "layer_"+str(i)
			self.model.add( Conv1D(filters,kernel_size=kern_size,padding='same',activation='relu', name=layer_name) )
			self.model.add(MaxPooling1D())
		#Automatic features
		self.model.add(Flatten(name="automatic_features"))
		#for multilabel DO NOT use softmax use sigmoid
		self.model.add( Dense(64,activation='relu', name="layer_dense") )
		self.model.add( Dense(6,activation='softmax',  name="output_layer"))
		self.model.compile( loss='mse',metrics=['mse','acc'], optimizer='adam' )
		self.model.summary()
		self.name2layer = {}
		for layer in self.model.layers:
			self.name2layer[layer.name] = layer
