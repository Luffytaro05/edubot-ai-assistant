import torch
import torch.nn as nn
import json
import os

# Simple fallback model for Railway deployment
class SimpleNeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(SimpleNeuralNet, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size)
        self.l2 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        return out

def create_fallback_model():
    """Create a simple fallback model for Railway deployment"""
    try:
        # Load intents to get the number of classes
        with open("intents.json", "r") as f:
            intents = json.load(f)
        
        tags = [intent["tag"] for intent in intents["intents"]]
        num_classes = len(tags)
        
        # Create a simple model
        model = SimpleNeuralNet(input_size=100, hidden_size=16, output_size=num_classes)
        
        # Create dummy data
        data = {
            "model_state": model.state_dict(),
            "input_size": 100,
            "hidden_size": 16,
            "output_size": num_classes,
            "all_words": ["hello", "help", "thanks", "goodbye"] * 25,  # 100 words
            "tags": tags
        }
        
        # Save the model
        torch.save(data, "data.pth")
        print("✅ Created fallback model for Railway deployment")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create fallback model: {e}")
        return False

if __name__ == "__main__":
    create_fallback_model()
