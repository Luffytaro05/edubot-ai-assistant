import torch
import torch.nn as nn


class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size) 
        self.l2 = nn.Linear(hidden_size, hidden_size) 
        self.l3 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        out = self.relu(out)
        out = self.l3(out)
        # no activation and no softmax at the end
        return out


class HybridChatModel:
    """
    Hybrid model that combines neural network predictions with vector search
    """
    def __init__(self, neural_net, vector_store, tags, confidence_threshold=0.75):
        self.neural_net = neural_net
        self.vector_store = vector_store
        self.tags = tags
        self.confidence_threshold = confidence_threshold
    
    def predict_intent(self, input_vector):
        """Predict intent using neural network"""
        with torch.no_grad():
            output = self.neural_net(input_vector)
            probs = torch.softmax(output, dim=1)
            confidence, predicted = torch.max(probs, dim=1)
            
            return {
                'predicted_tag': self.tags[predicted.item()],
                'confidence': confidence.item(),
                'all_probs': probs[0].tolist()
            }
    
    def search_similar_patterns(self, query, tag=None, top_k=3):
        """Search for similar patterns using vector database"""
        if tag:
            return self.vector_store.search_by_tag(query, tag, top_k)
        else:
            return self.vector_store.search_similar(query, top_k)
    
    def get_hybrid_response(self, query, input_vector=None):
        """
        Get response using hybrid approach:
        1. Try neural network prediction
        2. If confidence is low, use vector search
        3. Combine results for better accuracy
        """
        results = {
            'method': 'hybrid',
            'neural_prediction': None,
            'vector_results': [],
            'final_tag': None,
            'confidence': 0.0,
            'response_source': 'unknown'
        }
        
        # Neural network prediction
        if input_vector is not None:
            neural_result = self.predict_intent(input_vector)
            results['neural_prediction'] = neural_result
            
            # If neural network is confident, use its prediction
            if neural_result['confidence'] >= self.confidence_threshold:
                results['final_tag'] = neural_result['predicted_tag']
                results['confidence'] = neural_result['confidence']
                results['response_source'] = 'neural_network'
                return results
        
        # Vector search as fallback or primary method
        vector_results = self.search_similar_patterns(query, top_k=5)
        results['vector_results'] = vector_results
        
        if vector_results:
            # Use the best vector match
            best_match = vector_results[0]
            results['final_tag'] = best_match['metadata'].get('tag')
            results['confidence'] = best_match['score']
            results['response_source'] = 'vector_search'
            
            # If we have neural prediction, compare and choose the best
            if results['neural_prediction']:
                neural_conf = results['neural_prediction']['confidence']
                vector_conf = best_match['score']
                
                # Use neural network if its confidence is higher
                if neural_conf > vector_conf:
                    results['final_tag'] = results['neural_prediction']['predicted_tag']
                    results['confidence'] = neural_conf
                    results['response_source'] = 'neural_network_preferred'
        
        return results