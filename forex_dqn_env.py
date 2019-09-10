# this is how I see the initial OBSERVATION PERIOD:
# 1. randomly selects an ACTION between [BUY, SELL, SIT, CLOSE]
# 2. if it decides to BUY (1)...randomly selects anytime to [SIT, CLOSE] <== check profit/loss.  profit: score=+1   loss: score=-1
# 3. if it decides to SELL (1)..randomly selects anytime to [SIT, CLOSE] <== check profit/loss.  profit: score=+1   loss: score=-1
# 4. if it decides to SIT (0)...randomly selects anytime to [SIT "more"] = 0 , BUY=1, SELL=1
# 5. if it decides to CLOSE (profit)...nothing happens. <== nothing happens, no profit at this point: score = 0
import pygame
from pygame.locals import *
import sys

import numpy as np
import pandas as pd

import datetime as dt
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc

from PIL import Image



import matplotlib
matplotlib.use("Agg")

import matplotlib.backends.backend_agg as agg




# WINDOW_WIDTH = 600
# WINDOW_HEIGHT = 675

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
GAME_SPEED = 0  # delay in milliseconds before next level play e.g. 1000 = 1 second
                # 0 - no delay


STARTING_BALANCE = 200000

# ACTION DEFINITIONS
SIT = 0
BUY = 1
SELL = 2
CLOSE = 3

TRADE_ACTIONS = ['SIT','BUY','SELL','CLOSE']

debug=False

class ForexGame:
    def __init__(self):
        self.GScore = 0

        # Prepare data for environment
        self.data_dir = './data/'
        self.data_file = 'eurusd3.csv'
        self.data = pd.read_csv(self.data_dir + self.data_file)
        self.data.set_index('Date', inplace=True, drop=True)

        self.current_data_position = 0
        self.current_data = []
        self.current_data_ohlc = []

        self.current_data_date = self.data.index[self.current_data_position]
        self.current_data_open = self.data['Open'][self.current_data_position]
        self.current_data_high = self.data['High'][self.current_data_position]
        self.current_data_low = self.data['Low'][self.current_data_position]
        self.current_data_close = self.data['Close'][self.current_data_position]
        self.current_data_volume = self.data['Volume'][self.current_data_position]
        self.current_data_piprange = self.data['PipRange'][self.current_data_position]
        self.current_data_bidratio = self.data['BidRatio'][self.current_data_position]
        self.current_data_rseur = self.data['rsEUR'][self.current_data_position]
        self.current_data_rsUSD = self.data['rsUSD'][self.current_data_position]

        self.open_data_date = 0
        self.open_data_open = 0
        self.open_data_high = 0
        self.open_data_low = 0
        self.open_data_close = 0
        self.open_data_volume = 0
        self.open_data_piprange = 0
        self.open_data_bidratio = 0
        self.open_data_rseur = 0
        self.open_data_rsUSD = 0

        self.balance = STARTING_BALANCE

        self.net_profit = 0

        self.open_action = CLOSE
        self.current_action = SIT

        # Define a new subplot
        self.fig, self.ax = plt.subplots(dpi=166, figsize=(7.5,3))

        plt.axis('off')
        self.ax.set_axis_off()

        self.canvas = agg.FigureCanvasAgg(self.fig)

        self.MAX_DATA_VIEW_WIDTH = 100  # Default: last 50 data loaded for plotting

        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.gameDisplay = pygame.display
        self.gameDisplay.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
        self.gameDisplay.set_caption('FOREX GAME')


    def drawOpenTradeIndicator(self, open_action):  # open_action is either a BUY or SELL
        if open_action == BUY:
            # pygame.draw.rect(self.gameDisplay,(0,255,0),(10,10,50,25))
            pygame.draw.rect(self.gameDisplay,(0,0,0),(10,10,50,25))
        elif open_action == SELL:
            # pygame.draw.rect(self.gameDisplay,(255,0,0),(60,10,50,25))
            pygame.draw.rect(self.gameDisplay,(0,0,0),(60,10,50,25))

    def drawComputedProfitIndicator(self,computed_profit):
        if computed_profit > 0:
            # pygame.draw.polygon(self.gameDisplay,(0,255,0),[(500, 35), (530, 35), (515, 10)])
            pygame.draw.polygon(self.gameDisplay,(0,0,0),[(500, 35), (530, 35), (515, 10)])
        else:
            # pygame.draw.polygon(self.gameDisplay,(255,0,0),[(540, 10), (570, 10), (555, 35)])
            pygame.draw.polygon(self.gameDisplay,(0,0,0),[(540, 10), (570, 10), (555, 35)])

    def TradeAction(self):
        if self.current_action == SIT or self.current_action == CLOSE:
            score = 0
            if self.open_action == BUY and self.current_action == CLOSE:
                # compute score based on open/close pairs
                pip_unit_multiplier = 10000
                pip_difference = (self.current_data_close - self.open_data_close)
                positive_reinforcement = 1 # in order not to discourage it from closing in general

                if pip_difference > 0:
                    # multply pip difference to 10,000 to add to the score to make it bear heavier weights based on profit
                    score = positive_reinforcement + (pip_difference * pip_unit_multiplier)
                else:
                    # else just add decimal-pips to 1 (still a positive score but lower)
                    # score = positive_reinforcement + pip_difference

                    # just return the positive value of the negative pip_diff
                    score = abs(pip_difference)

                print('==== CLOSED TRADE DETECTED ====')
                print('Opened Action:',TRADE_ACTIONS[self.open_action])
                print('Current Action:',TRADE_ACTIONS[self.current_action])
                print('Score:',score)
                print('===============================')
                self.drawComputedProfitIndicator(pip_difference)

                # RESET OPEN ACTION
                self.open_action = CLOSE

                self.open_data_date = 0
                self.open_data_open = 0
                self.open_data_high = 0
                self.open_data_low = 0
                self.open_data_close = 0
                self.open_data_volume = 0
                self.open_data_piprange = 0
                self.open_data_bidratio = 0
                self.open_data_rseur = 0
                self.open_data_rsUSD = 0

            elif self.open_action == SELL and self.current_action == CLOSE:
                # compute score based on open/close pairs
                pip_unit_multiplier = 10000
                pip_difference = (self.open_data_close - self.current_data_close)
                positive_reinforcement = 1 # in order not to discourage it from closing in general

                if pip_difference > 0:
                    # multply pip difference to 10,000 to add to the score to make it bear heavier weights based on profit
                    score = positive_reinforcement + (pip_difference * pip_unit_multiplier)
                else:
                    # else just add decimal-pips to 1 (still a positive score but lower)
                    # score = positive_reinforcement + pip_difference

                    # just return the positive value of the negative pip_diff
                    score = abs(pip_difference)

                print('==== CLOSED TRADE DETECTED ====')
                print('Opened Action:',TRADE_ACTIONS[self.open_action])
                print('Current Action:',TRADE_ACTIONS[self.current_action])
                print('Score:',score)
                print('===============================')
                self.drawComputedProfitIndicator(pip_difference)

                # RESET OPEN ACTION
                self.open_action = CLOSE

                self.open_data_date = 0
                self.open_data_open = 0
                self.open_data_high = 0
                self.open_data_low = 0
                self.open_data_close = 0
                self.open_data_volume = 0
                self.open_data_piprange = 0
                self.open_data_bidratio = 0
                self.open_data_rseur = 0
                self.open_data_rsUSD = 0
            elif self.open_action == CLOSE and self.current_action == CLOSE:
                score = -1
                print('=========== CANNOT CLOSE WHEN NO OPEN TRADE ===========')
                print('Score:',score)
                print('=======================================================')
            elif self.open_action == BUY and self.current_action == SIT:
                score = -0.5
                pip_difference = (self.current_data_close - self.open_data_close) * 10000
                print('========= POTENTIAL PROFIT:',pip_difference,' ===========')
                self.drawComputedProfitIndicator(pip_difference)

            elif self.open_action == SELL and self.current_action == SIT:
                score = -0.5
                pip_difference = (self.open_data_close - self.current_data_close) * 10000
                print('========= POTENTIAL PROFIT:',pip_difference,' ===========')
                self.drawComputedProfitIndicator(pip_difference)
            elif self.open_action == CLOSE and self.current_action == SIT:
                score = -1
                # pip_difference = (self.open_data_close - self.current_data_close) * 10000
                # print('========= POTENTIAL PROFIT:',pip_difference,' ===========')
                # self.drawComputedProfitIndicator(pip_difference)
        else:
            # May it be BUY or SELL
            if self.open_action == CLOSE:
                self.open_action = self.current_action

                self.open_data_date = self.data.index[self.current_data_position]
                self.open_data_open = self.data['Open'][self.current_data_position]
                self.open_data_high = self.data['High'][self.current_data_position]
                self.open_data_low = self.data['Low'][self.current_data_position]
                self.open_data_close = self.data['Close'][self.current_data_position]
                self.open_data_volume = self.data['Volume'][self.current_data_position]
                self.open_data_piprange = self.data['PipRange'][self.current_data_position]
                self.open_data_bidratio = self.data['BidRatio'][self.current_data_position]
                self.open_data_rseur = self.data['rsEUR'][self.current_data_position]
                self.open_data_rsUSD = self.data['rsUSD'][self.current_data_position]

                score = 1
                print('==== OPEN TRADE DETECTED ====')
                print('Opened Action:',TRADE_ACTIONS[self.open_action])
                print('Score:',score)
                print('=============================')

            else:
                if self.open_action == BUY:
                    score = -1
                    pip_difference = (self.current_data_close - self.open_data_close) * 10000
                    # print('=========== COMPUTED PROFIT ===========')
                    # print('Computed Profit:',pip_difference)
                    # print('=======================================')
                    self.drawComputedProfitIndicator(pip_difference)

                elif self.open_action == SELL:
                    score = -1
                    pip_difference = (self.open_data_close - self.current_data_close) * 10000
                    # print('=========== COMPUTED PROFIT ===========')
                    # print('Computed Profit:',pip_difference)
                    # print('=======================================')
                    self.drawComputedProfitIndicator(pip_difference)
                print('==== CANNOT BUY/SELL WHEN TRADE HAS ALREADY OPENED [',TRADE_ACTIONS[self.open_action],'] ====')
                print('Score:',score)
                print('===============================================================')

        return score


    def PlayNextMove(self, action):

        self.current_action = action
        # print('action:',action)
        print('======= GAME TIME:',self.current_data_position, '======= | ACTION:',TRADE_ACTIONS[self.current_action], '| GScore:',self.GScore)
        score = 0

        # print('Loading new data...')
        if self.current_data_position > self.MAX_DATA_VIEW_WIDTH:
            # Graph only data within the view width
            self.ax.cla()
            plt.axis('off')
            self.current_data = []
            self.current_data_ohlc = []
            self.current_data = self.data[['Open','High','Low','Close']][self.current_data_position-self.MAX_DATA_VIEW_WIDTH:self.current_data_position]
        else:
            #Just feed the data if position is still less then the max view width
            self.current_data = self.data[['Open','High','Low','Close']][:self.current_data_position]
        
        

        if self.current_data is not None:
            # update current individual field data
            self.current_data_date = self.data.index[self.current_data_position]
            self.current_data_open = self.data['Open'][self.current_data_position]
            self.current_data_high = self.data['High'][self.current_data_position]
            self.current_data_low = self.data['Low'][self.current_data_position]
            self.current_data_close = self.data['Close'][self.current_data_position]
            self.current_data_volume = self.data['Volume'][self.current_data_position]
            self.current_data_piprange = self.data['PipRange'][self.current_data_position]
            self.current_data_bidratio = self.data['BidRatio'][self.current_data_position]
            self.current_data_rseur = self.data['rsEUR'][self.current_data_position]
            self.current_data_rsUSD = self.data['rsUSD'][self.current_data_position]

            # print('Building OHLC data...')
            self.current_data_ohlc = self.current_data[['Open','High','Low','Close']]
            self.current_data_ohlc.reset_index(inplace=True)
            self.current_data_ohlc['Date'] = self.current_data_ohlc['Date'].map(mdates.datestr2num)

            # print('OHLC data BUILT...')

            # Plot the candlestick chart and put date on x-Axis
            # print('Drawing candlesticks...')
            candlestick_ohlc(self.ax, self.current_data_ohlc.values, width=0.001, colorup='g', colordown='r')

            # print('Candlesticks loaded...')

            # print('Drawing canvas...')
            self.canvas.draw()
            # print('self.canvas.draw() ==> DONE')
            self.renderer = self.canvas.get_renderer()
            # print('self.renderer ==> DONE')
            self.img = self.renderer.tostring_rgb()
            # print('Canvas DRAWN...')

            # print('Refreshing image...')
            self.gameDisplay = pygame.display.get_surface()
            size = self.canvas.get_width_height()
            surf = pygame.image.fromstring(self.img, size, "RGB")
            self.gameDisplay.fill((255,255,255))
            # self.gameDisplay.blit(surf, (0,100))
            self.gameDisplay.blit(surf, (-125,100))

            self.drawOpenTradeIndicator(self.open_action)

            score = self.TradeAction()

            # pygame.display.flip()
            pygame.display.update()
            # print('Image refreshed...')


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                continue




        self.current_data_position += 1

        pygame.time.wait(GAME_SPEED)

        # Now Capture the Screen Image
        ScreenImage = pygame.surfarray.array3d(self.gameDisplay)

		#update the Game Display
        # pygame.display.flip()
        pygame.display.update()

		#return the score and Screen Image Data
        self.GScore += score

        return [score,ScreenImage]

if __name__ == '__main__':
    #Training
    theGame = ForexGame()

    # if the current data position being loaded at the level
    # is still less than the total number of data available, then PLAY! else END GAME
    while theGame.current_data_position < len(theGame.data):
        print('Game Level:', theGame.current_data_position)
        BestAction = 0
        theGame.PlayNextMove(BestAction)

    print('Game has ended. Reached total number of data available.')
    print('Balance:',theGame.balance)
