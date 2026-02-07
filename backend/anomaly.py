import cv2
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os
from scipy.stats import entropy

def extract_features(before, after):
    """Extract multiple features from satellite images"""
    # Calculate difference
    diff = cv2.absdiff(before, after)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    
    # Feature 1: Mean intensity change
    mean_change = np.mean(gray)
    
    # Feature 2: Standard deviation (variability)
    std_change = np.std(gray)
    
    # Feature 3: Maximum change
    max_change = np.max(gray)
    
    # Feature 4: Edge detection (Laplacian variance)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    edge_variance = laplacian.var()
    
    # Feature 5: Percentage of pixels with significant change
    threshold = 30
    significant_pixels = np.sum(gray > threshold) / gray.size * 100
    
    return {
        'mean_change': float(mean_change),
        'std_change': float(std_change),
        'max_change': float(max_change),
        'edge_variance': float(edge_variance),
        'significant_pixels': float(significant_pixels)
    }

def extract_enhanced_features(before, after):
    """
    IMPROVEMENT 3: Enhanced feature engineering
    Extract comprehensive features including texture, frequency domain, and histogram analysis
    """
    # Get base features
    base_features = extract_features(before, after)
    
    # Calculate difference images
    diff = cv2.absdiff(before, after)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    
    # Convert to grayscale for analysis
    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
    
    # ENHANCEMENT 1: Texture features using gradient magnitude
    sobelx = cv2.Sobel(gray_diff, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray_diff, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
    texture_complexity = np.mean(gradient_magnitude)
    
    # ENHANCEMENT 2: Frequency domain analysis
    # Compare spectral energy between images
    f_before = np.fft.fft2(before_gray)
    f_after = np.fft.fft2(after_gray)
    
    # Calculate energy in frequency domain
    energy_before = np.sum(np.abs(f_before)**2)
    energy_after = np.sum(np.abs(f_after)**2)
    spectral_energy_change = abs(float(energy_after - energy_before)) / (energy_before + 1e-10)
    
    # ENHANCEMENT 3: Histogram analysis
    hist_before = cv2.calcHist([before_gray], [0], None, [256], [0, 256])
    hist_after = cv2.calcHist([after_gray], [0], None, [256], [0, 256])
    
    # Normalize histograms
    hist_before = hist_before.flatten() / hist_before.sum()
    hist_after = hist_after.flatten() / hist_after.sum()
    
    # Calculate histogram distance (Bhattacharyya distance)
    histogram_distance = -np.log(np.sum(np.sqrt(hist_before * hist_after)) + 1e-10)
    
    # ENHANCEMENT 4: Spatial autocorrelation (simplified Moran's I concept)
    # Measure spatial clustering of changes
    kernel = np.ones((5, 5), np.float32) / 25
    spatial_smoothed = cv2.filter2D(gray_diff.astype(np.float32), -1, kernel)
    spatial_variance = np.var(spatial_smoothed)
    
    # ENHANCEMENT 5: Entropy change
    entropy_before = entropy(hist_before + 1e-10)
    entropy_after = entropy(hist_after + 1e-10)
    entropy_change = abs(float(entropy_after - entropy_before))
    
    # Combine all features
    enhanced_features = {
        **base_features,
        'texture_complexity': float(texture_complexity),
        'spectral_energy_change': float(spectral_energy_change),
        'histogram_distance': float(histogram_distance),
        'spatial_variance': float(spatial_variance),
        'entropy_change': float(entropy_change)
    }
    
    return enhanced_features

def get_or_train_model(model_path='models/anomaly_detector.pkl'):
    """
    IMPROVEMENT 1: Pre-trained model management
    Load pre-trained model or create and train a new one
    """
    if os.path.exists(model_path):
        try:
            model = joblib.load(model_path)
            print(f"✅ Loaded pre-trained model from {model_path}")
            return model
        except Exception as e:
            print(f"⚠️ Error loading model: {e}. Training new model...")
    
    # If model doesn't exist, train a new one
    print("🔄 Training new anomaly detection model...")
    
    # Create baseline "normal" data based on domain knowledge
    # These represent typical low-change scenarios in ocean monitoring
    normal_baseline = [
        # Low change scenarios
        [10, 5, 30, 100, 5, 50, 0.01, 0.1, 500, 0.05],
        [12, 6, 32, 110, 6, 55, 0.012, 0.11, 520, 0.055],
        [15, 8, 35, 120, 8, 60, 0.015, 0.12, 540, 0.06],
        [11, 5.5, 31, 105, 5.5, 52, 0.011, 0.105, 510, 0.052],
        [13, 7, 33, 115, 7, 58, 0.013, 0.115, 530, 0.058],
        
        # Medium change scenarios (daily variations)
        [18, 10, 40, 150, 10, 70, 0.02, 0.15, 600, 0.08],
        [20, 12, 45, 160, 12, 75, 0.022, 0.16, 620, 0.09],
        [22, 14, 48, 170, 14, 80, 0.024, 0.17, 640, 0.10],
    ]
    
    model = IsolationForest(
        contamination=0.2,  # Expect 20% of data to be anomalies
        random_state=42,
        n_estimators=100,  # More trees for better performance
        max_samples='auto'
    )
    
    model.fit(normal_baseline)
    
    # Save the model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, model_path)
    print(f"✅ Model trained and saved to {model_path}")
    
    return model

def calculate_confidence_score(features, anomaly_prediction, decision_score):
    """
    IMPROVEMENT 4: Better confidence scoring
    Calculate true confidence score based on multiple factors
    
    Args:
        features: Dictionary of extracted features
        anomaly_prediction: -1 for anomaly, 1 for normal
        decision_score: Isolation Forest decision function score
    
    Returns:
        Confidence score between 0-100
    """
    # Base score from mean change (legacy compatibility)
    base_score = features['mean_change']
    
    # Factor 1: Decision function score (more negative = more anomalous)
    # Normalize to 0-100 scale
    # Typical range: -0.5 to 0.5
    normalized_decision = abs(decision_score) * 100
    decision_confidence = min(100, normalized_decision)
    
    # Factor 2: Feature magnitude
    # Higher feature values indicate stronger anomaly
    feature_magnitude = (
        features['mean_change'] * 0.3 +
        features['std_change'] * 0.2 +
        features['max_change'] * 0.1 +
        features['significant_pixels'] * 0.4
    )
    
    # Factor 3: Feature consistency
    # Multiple high features = higher confidence
    high_feature_count = sum([
        features['mean_change'] > 20,
        features['std_change'] > 10,
        features['max_change'] > 50,
        features['significant_pixels'] > 15,
        features.get('texture_complexity', 0) > 60,
        features.get('histogram_distance', 0) > 0.2
    ])
    
    consistency_bonus = high_feature_count * 5  # Up to 30 points
    
    # Combine factors
    if anomaly_prediction == -1:  # Anomaly detected
        confidence = min(100, (
            decision_confidence * 0.4 +
            feature_magnitude * 0.4 +
            consistency_bonus +
            20  # Base confidence for anomaly detection
        ))
    else:  # Normal
        # Lower confidence for normal classifications
        confidence = min(100, base_score * 0.6)
    
    return round(float(confidence), 2)

def detect_anomaly(before, after, use_enhanced_features=True):
    """
    Detect anomalies using computer vision + machine learning
    
    IMPROVEMENTS IMPLEMENTED:
    - Pre-trained model loading (Improvement 1)
    - Enhanced feature extraction (Improvement 3)
    - Better confidence scoring (Improvement 4)
    """
    # Validate images
    if before is None or after is None:
        raise ValueError("Invalid images provided")
    
    # Ensure images are same size
    if before.shape != after.shape:
        after = cv2.resize(after, (before.shape[1], before.shape[0]))
    
    # Extract features (enhanced or basic)
    if use_enhanced_features:
        features = extract_enhanced_features(before, after)
    else:
        features = extract_features(before, after)
    
    # Create feature vector for ML
    if use_enhanced_features:
        feature_vector = [
            features['mean_change'],
            features['std_change'],
            features['max_change'],
            features['edge_variance'],
            features['significant_pixels'],
            features['texture_complexity'],
            features['spectral_energy_change'],
            features['histogram_distance'],
            features['spatial_variance'],
            features['entropy_change']
        ]
    else:
        feature_vector = [
            features['mean_change'],
            features['std_change'],
            features['max_change'],
            features['edge_variance'],
            features['significant_pixels']
        ]
    
    # Load pre-trained model
    model = get_or_train_model()
    
    # Predict if current observation is anomaly
    prediction = model.predict([feature_vector])[0]
    
    # Get decision function score for confidence calculation
    decision_score = model.decision_function([feature_vector])[0]
    
    # Calculate improved confidence score
    confidence = calculate_confidence_score(features, prediction, decision_score)
    
    # Determine risk level based on ML prediction and features
    if prediction == -1:  # ML detected anomaly
        if confidence > 70 or features['significant_pixels'] > 20:
            anomaly_level = "HIGH"
        elif confidence > 40 or features['significant_pixels'] > 10:
            anomaly_level = "MEDIUM"
        else:
            anomaly_level = "MEDIUM"
    else:  # Normal
        if features['mean_change'] > 30:  # Still check thresholds
            anomaly_level = "MEDIUM"
        else:
            anomaly_level = "LOW"
    
    return anomaly_level, confidence, features

def analyze_specific_indicators(before, after):
    """
    Analyze specific coastal risk indicators
    """
    indicators = []
    
    # Convert to different color spaces for analysis
    before_hsv = cv2.cvtColor(before, cv2.COLOR_BGR2HSV)
    after_hsv = cv2.cvtColor(after, cv2.COLOR_BGR2HSV)
    
    # 1. Check for water color changes (algal blooms, pollution)
    # Green/yellow hues indicate possible algal blooms
    before_green = cv2.inRange(before_hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
    after_green = cv2.inRange(after_hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
    
    # Use float conversion to avoid overflow
    green_increase = (float(np.sum(after_green)) - float(np.sum(before_green))) / float(before_green.size) * 100
    
    if green_increase > 5:
        indicators.append("Possible algal bloom detected")
    
    # 2. Surface reflectance changes
    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
    
    reflectance_change = np.mean(after_gray) - np.mean(before_gray)
    
    if abs(reflectance_change) > 15:
        indicators.append("Surface reflectance anomaly")
    
    # 3. Temperature proxy (using IR-like channel simulation)
    # In real implementation, would use actual thermal bands
    before_red = before[:, :, 2]
    after_red = after[:, :, 2]
    
    temp_change = np.mean(after_red) - np.mean(before_red)
    
    if temp_change > 10:
        indicators.append("Sea Surface Temperature deviation (simulated)")
    
    return indicators if indicators else ["No specific indicators detected"]