import React, { useState, useEffect, useRef } from 'react';
import { View, Button, Image, Text, StyleSheet, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { Camera } from 'expo-camera';
import * as ImageManipulator from 'expo-image-manipulator';
import * as FileSystem from "expo-file-system";
import axios from 'axios';

const App = () => {
  const [hasPermission, setHasPermission] = useState(null);
  const [imageUri, setImageUri] = useState(null);
  const [nutritionInfo, setNutritionInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isCameraVisible, setIsCameraVisible] = useState(false);
  const cameraRef = useRef(null);

  const BASE_URL = 'http://192.168.1.3:5000';

  // Request permission for camera access
  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
      if (status !== 'granted') {
        Alert.alert(
          "Permission Required",
          "Camera access is needed to capture food images. Please enable it in your device settings."
        );
      }
    })();
  }, []);

  // Capture image function
  const captureImage = async () => {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync();
        const resizedPhoto = await ImageManipulator.manipulateAsync(
          photo.uri,
          [{ resize: { width: 640 } }],
          { compress: 0.7, format: ImageManipulator.SaveFormat.JPEG }
        );
  
        setImageUri(resizedPhoto.uri);
        await recognizeFood(resizedPhoto.uri);
        setIsCameraVisible(false);
      } catch (error) {
        console.error("Error capturing image: ", error);
        Alert.alert("Error", "An error occurred while capturing the image.");
      }
    } else {
      Alert.alert("Camera Error", "Camera is not available.");
    }
  };

  // Send captured image to server for food recognition
  const recognizeFood = async (uri) => {
    setLoading(true);
    const apiUrl = `${BASE_URL}/api/capture`;

    try {
      console.log("Converting image to Base64...");
      const base64Image = await convertImageToBase64(uri);
      console.log("Image converted to Base64 successfully. Sending request to API...");

      const response = await axios.post(apiUrl, { image: base64Image }, { timeout: 20000 });
      console.log("API response received:", response.data);

      if (response.data && response.data.food_name && response.data.nutrition_info) {
        const { food_name, nutrition_info } = response.data;
        setNutritionInfo({ food_name, nutrition_info });
      } else {
        Alert.alert("Error", "Food not recognized. Please try again.");
        setNutritionInfo(null);
      }
    } catch (error) {
      setLoading(false);
      console.error("Error in recognizeFood:", error);
      Alert.alert("Error", error.response ? error.response.data.message : "Failed to recognize food. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Convert image URI to base64 format
  const convertImageToBase64 = async (uri) => {
    try {
      const base64 = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
      return base64;
    } catch (error) {
      console.log("Error converting image to Base64", error);
      throw new Error("Failed to convert image to Base64");
    }
  };

  if (hasPermission === null) {
    return <View />;  // Waiting for permission
  }
  if (hasPermission === false) {
    return <Text>No access to camera</Text>;  // No camera access
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>NutraScan</Text>
      {isCameraVisible && hasPermission && (
        <Camera
          style={styles.camera}
          type={Camera.Type.back}
          ref={cameraRef}
        >
          <View style={styles.captureButtonContainer}>
            <Button title="Capture" onPress={captureImage} color="#28a745" />
          </View>
        </Camera>
      )}
      <Button
        title={isCameraVisible ? "Close Camera" : "Open Camera"}
        onPress={() => setIsCameraVisible(!isCameraVisible)}
        color="#007bff"
      />
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#0000ff" style={styles.loading} />
          <Text style={styles.loadingText}>Processing your image...</Text>
        </View>
      )}
      {imageUri && <Image source={{ uri: imageUri }} style={styles.image} />}
      {nutritionInfo && (
        <View style={styles.nutritionContainer}>
          <Text style={styles.nutritionTitle}>Nutrition Information:</Text>
          <Text style={styles.foodName}>Food Name: {nutritionInfo.food_name}</Text>
          {Object.entries(nutritionInfo.nutrition_info).map(([key, value]) => (
            <Text key={key} style={styles.nutritionText}>{key}: {value}</Text>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f2f2f2',
  },
  camera: {
    width: 300,
    height: 300,
    marginBottom: 20,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
  },
  captureButtonContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  image: {
    width: 300,
    height: 300,
    marginTop: 10,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: '#ccc',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3.84,
    elevation: 5,
  },
  nutritionContainer: {
    marginTop: 20,
    padding: 15,
    backgroundColor: '#fff',
    borderRadius: 10,
    width: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },
  nutritionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  foodName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 5,
    color: '#555',
  },
  nutritionText: {
    fontSize: 14,
    color: '#555',
  },
  loading: {
    marginTop: 20,
  },
  loadingContainer: {
    alignItems: 'center',
    marginTop: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#555',
  },
});

export default App;
