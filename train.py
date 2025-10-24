import numpy as np
import random
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from nltk_utils import bag_of_words, tokenize, stem, enhanced_bag_of_words
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

# Training data with enhanced bag of words
X_train = []
y_train = []
for (pattern_sentence, tag) in xy:
    # Use enhanced bag of words if available, otherwise fallback to standard
    try:
        bag = enhanced_bag_of_words(pattern_sentence, all_words)
    except:
        bag = bag_of_words(pattern_sentence, all_words)
    X_train.append(bag)
    label = tags.index(tag)
    y_train.append(label)

X_train = np.array(X_train)
y_train = np.array(y_train)

# Enhanced hyperparameters for better training
num_epochs = 2000  # Increased epochs for better convergence
batch_size = 16     # Increased batch size for stability
learning_rate = 0.0005  # Reduced learning rate for better convergence
input_size = len(X_train[0])
hidden_size = 16    # Increased hidden size for better capacity
output_size = len(tags)
dropout_rate = 0.3  # Dropout for regularization

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
model = NeuralNet(input_size, hidden_size, output_size, dropout_rate).to(device)

# Enhanced loss function (label smoothing may not be available in older PyTorch versions)
try:
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
except TypeError:
    # Fallback for older PyTorch versions
    criterion = nn.CrossEntropyLoss()

# Enhanced optimizer with weight decay
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

# Learning rate scheduler
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=100
)

print("\nTraining neural network...")
# Enhanced training loop with validation
best_loss = float('inf')
patience_counter = 0
patience = 200

for epoch in range(num_epochs):
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for (words, labels) in train_loader:
        words = words.to(device)
        labels = labels.to(dtype=torch.long).to(device)

        # Forward
        outputs = model(words)
        loss = criterion(outputs, labels)

        # Backward and optimizer step
        optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1

    # Calculate average loss
    avg_loss = total_loss / num_batches
    
    # Update learning rate scheduler
    scheduler.step(avg_loss)
    
    # Early stopping
    if avg_loss < best_loss:
        best_loss = avg_loss
        patience_counter = 0
    else:
        patience_counter += 1
    
    if patience_counter >= patience:
        print(f"Early stopping at epoch {epoch+1}")
        break

    if (epoch + 1) % 100 == 0:
        current_lr = optimizer.param_groups[0]['lr']
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.4f}, LR: {current_lr:.6f}')

print(f'Final Loss: {best_loss:.4f}')

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