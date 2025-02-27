#
# This Agent demonstrates use of a Keras centred Q-network estimating the Q[S,A] Function from a few basic Features
#
# This DQN Agent Software is Based upon the following
#  https://github.com/yanpanlau/Keras-FlappyBird/blob/master/qlearn.py
#  requires keras [and hence Tensorflow or Theono backend]
# ==============================================================================
import random, numpy, math
#
from keras import initializers
from keras.models import Sequential
from keras.layers import LSTM
from keras.layers import *
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import *
import tensorflow as tf
#
import json
from collections import deque
#
NBRACTIONS = 4 # Number of Actions.  Action itself is a scalar:  0:stay, 1:Up, 2:Down
#  Now the Processed Convolutional Image Array dimensions into the Agent
IMGHEIGHT = 80
IMGWIDTH = 80
IMGHISTORY = 4
HISTORY_SIZE = 30
# ==========================
# DQN Reinforcement Learning Algorithm  Hyper Parameters
OBSERVEPERIOD = 50		# Period actually start real Training against Experienced Replay Batches
GAMMA = 0.975				# Q Reward Discount Gamma
# BATCH_SIZE = 64
BATCH_SIZE = 32
#  DQN Reinforcement learning performs best by taking a batch of training samples across a wide set of [S,A,R, S'] experieences
ExpReplay_CAPACITY = 5000
# ============================================================================================
class Agent:

	def __init__(self):

		# Set Up Ensure Tensor Flow Backend
		config = tf.ConfigProto()
		config.gpu_options.allow_growth = True
		sess = tf.Session(config=config)
		from keras import backend as K
		K.set_session(sess)
		# =========================

		self.model = self.createModel()

		# Create an Experience Replay Que  from Collections
		self.ExpReplay = deque()

		self.steps = 0
		self.epsilon = 1.0

	# ===================================================================
	def createModel(self):
		print("Creating Convolutional Keras Model")
		#
		# model = Sequential()
		# # Convolutional model to predict function, From a 40x40x4 Imput Image Stack and output Q Prediciton across 3x Actions
		# model.add(Conv2D(32, kernel_size=4, strides=(2, 2),input_shape=(IMGHEIGHT,IMGWIDTH ,IMGHISTORY),padding='same'))  #40*40*4
		# model.add(Activation('relu'))
		# model.add(Conv2D(64, kernel_size=4, strides=(2, 2),padding='same'))
		# model.add(Activation('relu'))
		# model.add(Conv2D(64, kernel_size=3, strides=(1, 1), padding='same'))
		# model.add(Activation('relu'))
		# model.add(Flatten())
		# model.add(Dense(512))
		# model.add(Activation('relu'))
		# model.add(Dense(units=NBRACTIONS, activation='linear'))				# Linear Output Layer as we are estimating a Function Q[S,A]
		#
		# model.compile(loss='mse', optimizer='adam')     # use adam as an alternative optimsier as per comment

# -----------------------------------------------------------------------------------

		model = Sequential()
		model.add(Conv2D(32, kernel_size=4, strides=(2, 2),input_shape=(IMGHEIGHT,IMGWIDTH,IMGHISTORY),padding='same'))  #40*40*4
		model.add(Activation('relu'))
		model.add(Conv2D(32, kernel_size=4, strides=(2, 2),padding='same'))
		model.add(Activation('relu'))
		model.add(Conv2D(64, kernel_size=3, strides=(1, 1), padding='same'))
		model.add(Activation('relu'))
		model.add(Flatten())

		model.add(RepeatVector(8))
		model.add(LSTM(8, activation='relu', return_sequences=True))
		model.add(LSTM(4, activation='relu', return_sequences=False))
		model.summary()
		# model.add(TimeDistributed(Dense(units=NBRACTIONS, activation='linear')))

		# model.add(Dense(units=NBRACTIONS, activation='linear'))
		# model.add(TimeDistributed(Flatten()))
		model.compile(loss='mse', optimizer='adam')





# -----------------------------------------------------------------------------------
		print("Finished building the Keras model")
		return model
	# ========================================================================================================
	def LoadBestModel(self):
		self.model.load_weights("BestForexModelWeights.h5")
		self.model.compile(loss='mse',optimizer='adam')
		self.epsilon = 0.0
	# ============================================================================================================
	# Return the Best Action  from a Q[S,A] search.  Depending upon an Epsilon Explore/ Exploitation decay ratio
	def FindBestAct(self, s):
		if (random.random() < self.epsilon or self.steps < OBSERVEPERIOD):
			return random.randint(0, NBRACTIONS-1)						# Explore
		else:
			# Determine Best Action for Current State s
			qvalue = self.model.predict(s)
			print('qvalue:',qvalue)
			BestA = numpy.argmax(qvalue)
			return BestA					# Exploit best Action Prediction

	# ========================================================================================================
	# Apply the Best Action  from a Q[S,A] search.
	def ReturnBestAct(self, s):
		# Determine Best Action for Current State s
		qvalue = 	self.model.predict(s)
		BestA = numpy.argmax(qvalue)

		return BestA					# Exploit best Action Prediction

	# ============================================
	def CaptureSample(self, sample):  # in (s, a, r, s_) format
		#  Append the sample to the Experience Replay Queue
		self.ExpReplay.append(sample)
		if len(self.ExpReplay) > ExpReplay_CAPACITY:
			self.ExpReplay.popleft()

		# Update the Epoch Step count  t manage the local Epsilon Explore vs Exploit
		self.steps += 1
		# ===================================
		# Epsilon decay Function  - Very slow as convolutional network
		self.epsilon = 1.0
		if(self.steps>OBSERVEPERIOD):
			self.epsilon = 0.75
			if(self.steps>2500):
				self.epsilon = 0.5
			if(self.steps>5000):
				self.epsilon = 0.25
			if(self.steps>7500):
				self.epsilon = 0.15
			if(self.steps>10000):
				self.epsilon = 0.1
			if(self.steps>12250):
				self.epsilon = 0.05

	# ============================================-----------------------------------------------------------
	# Perform an Agent Training Cycle Update by processing a set of samples from the Experience Replay memory
	def Process(self):
		# Only Perform Processing if in Processing Period
		if(self.steps>OBSERVEPERIOD):
			# Extract a sample from Experience Replay Queue
			minibatch = random.sample(self.ExpReplay,BATCH_SIZE)
			batchLen = len(minibatch)

			inputs = np.zeros((BATCH_SIZE, IMGHEIGHT,IMGWIDTH ,IMGHISTORY))   #BatchSize, 40, 40, 4 (old)    (32x80x80x4) (new)
			targets = np.zeros((inputs.shape[0], NBRACTIONS))  #(32,4)

			Q_sa = 0

			# Now extract the experience relay
			for i in range(0, batchLen-1):
				state_t = minibatch[i][0]	# (1x80x80x4) image
				action_t = minibatch[i][1]	# This is action 0, 1, 2, 3
				reward_t = minibatch[i][2]	# rewards
				state_t1 = minibatch[i][3]	# (1x80x80x4) image

				# Fill up Input set
				inputs[i:i + 1] = state_t	# (1x80x80x4) image


				# Fill Out Targets
				targets[i] = self.model.predict(state_t)
				Q_sa = self.model.predict(state_t1)

				# Review next state  Q Function Update
				if(state_t1 is None):
					targets[i, action_t] = reward_t
				else:
					# Prediction Q Value at next States
					targets[i, action_t] = reward_t + GAMMA * np.max(Q_sa)
			# end of Batch For Loop

			# Now Perform the Batch Fit Training
			self.model.fit(inputs, targets, batch_size=BATCH_SIZE, epochs=1, verbose=0)

		# end of self.steps>OBSERVEPERIOD
	# ============================================================================================================================
	def SaveWeights(self):
		print("Saving Model")
		self.model.save_weights("ForexModelWeights.h5",overwrite=True)
		with open("ForexModel.json", "w") as outfile:
			json.dump(self.model.to_json(), outfile)
	# ============================================================================================================================
	def SaveBestWeights(self):
		print("Saving Best Model")
		self.model.save_weights("BestForexModelWeights.h5",overwrite=True)
		with open("BestForexModel.json", "w") as outfile:
			json.dump(self.model.to_json(), outfile)
	# ==================================================================================
