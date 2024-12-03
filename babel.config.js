module.exports = {
  presets: [
    'module:metro-react-native-babel-preset', // Essential for React Native
    '@babel/preset-react', // If you're using React components
  ],
  plugins: [
    '@babel/plugin-proposal-class-properties', // Optional, for class properties
    '@babel/plugin-proposal-private-methods', // Optional, for private methods
    '@babel/plugin-proposal-private-property-in-object', // Optional, for private properties
  ],
};