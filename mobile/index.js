import { AppRegistry, Platform } from "react-native";
import { registerRootComponent } from "expo";
import App from "./app"; // points to main App component
import { name as appName } from "./app.json";

// to ensure the app initializes correctly
registerRootComponent(App);