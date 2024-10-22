import forex_dqn_env as MyForex # My PyGame Forex Game
import MyAgent # My DQN Based Agent

import numpy as np
import random

import pickle, os

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import skimage as skimage
from skimage import transform, color, exposure
from skimage.transform import rotate
from collections import deque
#
import matplotlib.pyplot as plt

TOTAL_TrainTime = 100000 # Only 100 Thousands epochs  (was Million)
#
# Now the Processed Convolutional Image Array dimensions into the Agent
IMGHEIGHT = 80
IMGWIDTH = 80
IMGHISTORY = 4
SCORELENGTH = 3

TARGET_SCORE_TO_END_GAME = 200000
# =======================================================================
# Process Reduce the 420x 400 Pong Game Screen Image
#
def ProcessGameImage(RawImage):
	GreyImage = skimage.color.rgb2gray(RawImage)
	# Get rid of bottom Score line
	# Now the Pygame seems to have turned the Image sideways so remove X direction
	# CroppedImage = GreyImage[0:800,0:800]
	# plt.imshow(CroppedImage)
	#print("Cropped Image Shape: ",CroppedImage.shape)
	ReducedImage = skimage.transform.resize(GreyImage,(IMGHEIGHT,IMGWIDTH), mode='reflect')

	return ReducedImage
# =====================================================================
# Main Experiment Method
def TrainExperiment():
	TrainTime = 0

	TrainHistory = []

	ScoreCheck = deque()
	NotQuit = True

    # Initialise Game

	#Create our PongGame instance
	TheGame = MyForex.ForexGame()

	#  Create our Agent (including DQN based Brain)
	TheAgent = MyAgent.Agent()

	# Initialise NextAction  Assume Action is scalar:  0:stay, 1:Up, 2:Down
	BestAction = 0

	# Get an Initial State
	[InitialScore,InitialScreenImage]= TheGame.PlayNextMove(BestAction)
	InitialGameImage = ProcessGameImage(InitialScreenImage)
	#
	# Now Initialise the Game State as the Stack of four x intial Images
	GameState = np.stack((InitialGameImage, InitialGameImage, InitialGameImage, InitialGameImage), axis=2)
	# Keras expects shape 1x40x40x4 (old)
	# Keras expects shape 1x80x80x4 (modified)
	GameState = GameState.reshape(1, GameState.shape[0], GameState.shape[1], GameState.shape[2])

    # =================================================================
	#Main Experiment Loop
	#Loop over data
	while (TheGame.current_data_position < len(TheGame.data) and NotQuit):
		# Determine Next Action From the Agent
		BestAction = TheAgent.FindBestAct(GameState)

		#  Now Apply the Recommended Action into the Game
		[ReturnScore,NewScreenImage]= TheGame.PlayNextMove(BestAction)

		# Need to process the returned Screen Image,
		NewGameImage = ProcessGameImage(NewScreenImage)

		# Now reshape Keras expects shape 1x40x40x1 (old)
		# Now reshape Keras expects shape 1x80x80x1 (modified)
		NewGameImage = NewGameImage.reshape(1, NewGameImage.shape[0], NewGameImage.shape[1], 1)

		#Now Add the new Image into the Next GameState stack, using 3 previous capture game images
		NextState = np.append(NewGameImage, GameState[:, :, :, :3], axis=3)

		# Capture the Sample [S, A, R, S'] in Agent Experience Replay Memory
		TheAgent.CaptureSample((GameState,BestAction,ReturnScore,NextState))

		#  Now Request Agent to DQN Train process  Against Experience
		TheAgent.Process()

		# Move State On
		GameState = NextState

		# Move TrainTime Click
		TrainTime = TrainTime + 1

        #Save the model every 5000
		if TrainTime % 5000 == 0:
            # Save the Keras Model
			TheAgent.SaveWeights()

		if TrainTime % 100 == 0:
			print("Train Time: ", TrainTime,"  Game Score: ", "{0:.2f}".format(TheGame.GScore), "   EPSILON: ", "{0:.4f}".format(TheAgent.epsilon))
			TrainHistory.append((TrainTime,TheGame.GScore,TheAgent.epsilon))

			#  Now write the progress to File
			GFile = open('TrainHistory.dat','wb')
			pickle.dump(TrainHistory,GFile)
			GFile.close()

			#  Queue up last SCORELENGTH if Reached Good Performance
			ScoreCheck.append(TheGame.GScore)
			if len(ScoreCheck) > SCORELENGTH:
				ScoreCheck.popleft()
			# Check Average Scores  if greater than 9.75 assume reached peak performance
			SSum= 0.0
			for ScoreItem in ScoreCheck:
				SSum = SSum + ScoreItem
			if SSum/ SCORELENGTH > TARGET_SCORE_TO_END_GAME:
				print("Achieved Good Performance, Saving Best Model")
				TheAgent.SaveBestWeights()
				# Complete the Game Loop
				NotQuit = False

	# ===============================================
	#  Game Completed So Display the Final Scores Grapth
	GFile = open('TrainHistory.dat','rb')
	TrainHistory = pickle.load(GFile)
	GFile.close()

	# Plot the Score vs Game Time profile
	x_val = [x[0] for x in TrainHistory]
	y_val = [x[1] for x in TrainHistory]

	plt.plot(x_val,y_val)
	plt.xlabel("Game Time")
	plt.ylabel("Score")
	plt.show()
	# =======================================================================
def main():
    #
	# Main Method Just Play our Experiment
	TrainExperiment()

	# =======================================================================
if __name__ == "__main__":
    main()
