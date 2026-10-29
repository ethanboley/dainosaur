import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque
from dinosaur import DinoGame

# 1. THE BRAIN: Neural Network
# This is where the AI "thinks". It takes the game state and predicts which action
# (Nothing, Up, Down) will lead to the highest reward.
class DQN(nn.Module):
    def __init__(self, input_size, output_size):
        super(DQN, self).__init__()
        # We use a simple 3-layer architecture
        self.fc = nn.Sequential(
            nn.Linear(input_size, 128), # Input layer -> Hidden layer 1
            nn.ReLU(),                  # Activation function (adds non-linearity)
            nn.Linear(128, 64),         # Hidden layer 1 -> Hidden layer 2
            nn.ReLU(),
            nn.Linear(64, output_size)  # Hidden layer 2 -> Output layer (the 3 actions)
        )

    def forward(self, x):
        return self.fc(x)

# 2. THE MEMORY: Replay Buffer
# The bot learns from past experiences. We store (state, action, reward, next_state, done)
# and later "replay" a random batch of these to train the brain.
class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

# 3. THE BOT: The Agent
class Bot:
    def __init__(self):
        self.state_size = 7 # Dino Y, Dino Vel, Obs Dist, Obs Width, Obs Y, Obs Type, Speed
        self.action_size = 3 # 0: Nothing, 1: Up, 2: Down
        
        self.memory = ReplayMemory(100000)
        self.gamma = 0.99    # Discount factor (how much we care about future rewards)
        self.epsilon = 1.0   # Exploration rate (starts at 100% random actions)
        self.epsilon_min = 0.01 # Keep a small amount of exploration
        self.epsilon_decay = 0.99985 # SLOWER DECAY: takes thousands of steps to reach min
        self.learning_rate = 0.0005 # Slightly lower for more stable learning
        self.batch_size = 64
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DQN(self.state_size, self.action_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def select_action(self, state):
        if random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return torch.argmax(q_values).item()

    def train(self):
        if len(self.memory) < self.batch_size:
            return

        batch = self.memory.sample(self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        current_q = self.model(states).gather(1, actions.unsqueeze(1))

        with torch.no_grad():
            next_q = self.model(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q

        loss = self.criterion(current_q.squeeze(), target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save(self, filename="dino_bot.pth"):
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'epsilon': self.epsilon
        }, filename)
        print(f"Model saved to {filename}")

    def load(self, filename="dino_bot.pth"):
        try:
            checkpoint = torch.load(filename, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.epsilon = checkpoint['epsilon']
            print(f"Model loaded from {filename}")
        except FileNotFoundError:
            print("No saved model found, starting from scratch.")

# 4. THE TRAINING LOOP
def train_bot():
    game = DinoGame()
    bot = Bot()

    # Startup Menu
    import os
    if os.path.exists("dino_bot.pth"):
        print("\n--- Dinosaur AI Training ---")
        choice = input("Save file 'dino_bot.pth' found. \n[L]oad and continue training \n[S]tart from scratch \nChoice: ").lower()
        if choice == 'l':
            bot.load()
        else:
            print("Starting from scratch...")
    else:
        print("\nNo save file found. Starting from scratch...")

    episodes = 5000 
    save_every = 50
    train_freq = 4 # Only train every 4 steps
    step_count = 0
    
    # Training Speed Control
    render_training = False # Set to True to see every game

    for e in range(episodes):
        state = game.reset()
        show_this_one = (e % save_every == 0)

        while True:
            action = bot.select_action(state)
            next_state, reward, done = game.step(action, render=(render_training or show_this_one))

            bot.memory.push(state, action, reward, next_state, done)
            
            # Optimization: Training only every X steps
            step_count += 1
            if step_count % train_freq == 0:
                bot.train()

            state = next_state

            if done:
                print(f"Episode: {e}/{episodes}, Score: {game.score}, Total Reward: {game.total_reward:.2f}, Epsilon: {bot.epsilon:.4f}")
                break

        if e > 0 and e % save_every == 0:
            bot.save()


if __name__ == "__main__":
    train_bot()
