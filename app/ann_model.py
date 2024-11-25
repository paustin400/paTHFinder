import tensorflow as tf  # Import TensorFlow as tf for general use.
from tensorflow.keras.models import Sequential  # Ensure model imports correctly.
from tensorflow.keras.layers import Dense  # Import layers for the ANN.

def build_ann_model(input_shape):
    """
    Build a simple ANN model using TensorFlow.
    Parameters:
    - input_shape: Number of features in the input data.

    Returns:
    - A compiled Sequential model.
    """
    # Initialize the Sequential model.
    model = Sequential()

    # Add layers to the model.
    model.add(Dense(64, input_dim=input_shape, activation='relu'))  # Input layer
    model.add(Dense(32, activation='relu'))  # Hidden layer
    model.add(Dense(1, activation='sigmoid'))  # Output layer: Route quality score (0-1)

    # Compile the model with optimizer, loss function, and metric.
    model.compile(optimizer='adam', 
                  loss='binary_crossentropy', 
                  metrics=['accuracy'])

    return model  # Return the compiled model.

def train_ann_model(X, y):
    """
    Train the ANN model with the route data.

    Parameters:
    - X: Input features (e.g., routes data).
    - y: Target values (e.g., route quality labels).

    Returns:
    - Trained model.
    """
    # Build the model based on the input shape.
    model = build_ann_model(X.shape[1])

    # Train the model with the provided data.
    model.fit(X, y, 
              epochs=50, 
              batch_size=8, 
              validation_split=0.2, 
              verbose=1)

    return model  # Return the trained model.