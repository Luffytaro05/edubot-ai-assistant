import numpy as np
import random
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from nltk_utils import bag_of_words, tokenize, stem
from model import NeuralNet
from vector_store import VectorStore

# Load intents
with open('intents.json', 'r') as f:
    intents = json.load(f)

all_words = []
tags = []
xy = []

# Initialize vector store
vector_store = VectorStore()

print("Processing intents for vector storage...")

# Process intents for both neural network and vector storage
for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    
    # Store patterns in vector database
    for pattern in intent['patterns']:
        # Store in vector database with metadata
        metadata = {
            'tag': tag,
            'intent_type': 'pattern',
            'responses': intent['responses']
        }
        vector_store.store_text(pattern, metadata)
        
        # Traditional tokenization for neural network
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w, tag))
    
    # Also store responses for potential retrieval
    for response in intent['responses']:
        metadata = {
            'tag': tag,
            'intent_type': 'response',
            'patterns': intent['patterns']
        }
        vector_store.store_text(response, metadata)

# Stem and lower each word, remove punctuation
ignore_words = ['?', '!', '.', ',']
all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words))
tags = sorted(set(tags))

# Training data
X_train = []
y_train = []
for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)
    X_train.append(bag)
    label = tags.index(tag)
    y_train.append(label)

X_train = np.array(X_train)
y_train = np.array(y_train)

# Hyperparameters
num_epochs = 1000
batch_size = 8
learning_rate = 0.001
input_size = len(X_train[0])
hidden_size = 8
output_size = len(tags)

print(f"Training data loaded:")
print(f" - {len(X_train)} samples")
print(f" - {input_size} input size")
print(f" - {output_size} output size")
print(f" - Vector database initialized with {vector_store.get_stats()['total_vectors']} vectors")

class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples

dataset = ChatDataset()
train_loader = DataLoader(dataset=dataset,
                          batch_size=batch_size,
                          shuffle=True,
                          num_workers=0)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size, hidden_size, output_size).to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

print("\nTraining neural network...")
# Training loop
for epoch in range(num_epochs):
    for (words, labels) in train_loader:
        words = words.to(device)
        labels = labels.to(dtype=torch.long).to(device)

        # Forward
        outputs = model(words)
        loss = criterion(outputs, labels)

        # Backward and optimizer step
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if (epoch + 1) % 100 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

print(f'Final Loss: {loss.item():.4f}')

# Save model and metadata
data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

FILE = "data.pth"
torch.save(data, FILE)

# Save vector store
vector_store.save_index("vector_index")

print(f'Training complete. Neural network saved to {FILE}')
print(f'Vector database saved with {vector_store.get_stats()["total_vectors"]} vectors')
print("Vector database statistics:", vector_store.get_stats())