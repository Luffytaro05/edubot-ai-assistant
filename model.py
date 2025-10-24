import torch
import torch.nn as nn


class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes, dropout_rate=0.3):
        super(NeuralNet, self).__init__()
        # Enhanced architecture with more layers and dropout
        self.l1 = nn.Linear(input_size, hidden_size * 2) 
        self.l2 = nn.Linear(hidden_size * 2, hidden_size) 
        self.l3 = nn.Linear(hidden_size, hidden_size // 2)
        self.l4 = nn.Linear(hidden_size // 2, num_classes)
        
        # Activation functions
        self.relu = nn.ReLU()
        self.leaky_relu = nn.LeakyReLU(0.1)
        self.dropout = nn.Dropout(dropout_rate)
        self.batch_norm1 = nn.BatchNorm1d(hidden_size * 2)
        self.batch_norm2 = nn.BatchNorm1d(hidden_size)
        self.batch_norm3 = nn.BatchNorm1d(hidden_size // 2)
    
    def forward(self, x):
        # First layer with batch normalization and dropout
        out = self.l1(x)
        out = self.batch_norm1(out)
        out = self.leaky_relu(out)
        out = self.dropout(out)
        
        # Second layer
        out = self.l2(out)
        out = self.batch_norm2(out)
        out = self.leaky_relu(out)
        out = self.dropout(out)
        
        # Third layer
        out = self.l3(out)
        out = self.batch_norm3(out)
        out = self.leaky_relu(out)
        out = self.dropout(out)
        
        # Output layer
        out = self.l4(out)
        # no activation and no softmax at the end
        return out


class HybridChatModel:
    """
    Enhanced hybrid model that combines neural network predictions with vector search
    """
    def __init__(self, neural_net, vector_store, tags, confidence_threshold=0.75):
        self.neural_net = neural_net
        self.vector_store = vector_store
        self.tags = tags
        self.confidence_threshold = confidence_threshold
        self.min_vector_score = 0.6  # Minimum vector search score
        self.context_weight = 0.1   # Weight for context in scoring
    
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
    
    def get_hybrid_response(self, query, input_vector=None, context=None):
        """
        Enhanced hybrid approach with better scoring and fallback mechanisms:
        1. Try neural network prediction
        2. Use vector search with enhanced scoring
        3. Apply context weighting
        4. Use ensemble scoring for better accuracy
        """
        results = {
            'method': 'hybrid',
            'neural_prediction': None,
            'vector_results': [],
            'final_tag': None,
            'confidence': 0.0,
            'response_source': 'unknown',
            'ensemble_score': 0.0
        }
        
        # Neural network prediction
        neural_confidence = 0.0
        neural_tag = None
        if input_vector is not None:
            neural_result = self.predict_intent(input_vector)
            results['neural_prediction'] = neural_result
            neural_confidence = neural_result['confidence']
            neural_tag = neural_result['predicted_tag']
        
        # Vector search with enhanced scoring
        vector_results = self.search_similar_patterns(query, top_k=5)
        results['vector_results'] = vector_results
        
        vector_confidence = 0.0
        vector_tag = None
        if vector_results and vector_results[0]['score'] >= self.min_vector_score:
            best_match = vector_results[0]
            vector_confidence = best_match['score']
            vector_tag = best_match['metadata'].get('tag')
        
        # Context weighting
        context_boost = 0.0
        if context and vector_tag == context:
            context_boost = self.context_weight
        
        # Ensemble scoring - combine neural and vector predictions
        if neural_confidence > 0 and vector_confidence > 0:
            # Both methods have results - use weighted combination
            ensemble_score = (neural_confidence * 0.6) + (vector_confidence * 0.4) + context_boost
            
            if neural_confidence >= self.confidence_threshold:
                # Neural network is confident - use it
                results['final_tag'] = neural_tag
                results['confidence'] = neural_confidence
                results['response_source'] = 'neural_network'
            elif vector_confidence >= self.min_vector_score:
                # Vector search is reliable - use it
                results['final_tag'] = vector_tag
                results['confidence'] = vector_confidence
                results['response_source'] = 'vector_search'
            else:
                # Use ensemble score
                results['final_tag'] = neural_tag if neural_confidence > vector_confidence else vector_tag
                results['confidence'] = ensemble_score
                results['response_source'] = 'ensemble'
        elif neural_confidence > 0:
            # Only neural network result
            results['final_tag'] = neural_tag
            results['confidence'] = neural_confidence
            results['response_source'] = 'neural_network'
        elif vector_confidence > 0:
            # Only vector search result
            results['final_tag'] = vector_tag
            results['confidence'] = vector_confidence + context_boost
            results['response_source'] = 'vector_search'
        
        results['ensemble_score'] = ensemble_score if 'ensemble_score' in locals() else max(neural_confidence, vector_confidence)
        
        return results