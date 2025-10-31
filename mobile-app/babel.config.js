module.exports = {
  presets: ['babel-preset-expo'],
  plugins: [
    [
      'module-resolver',
      {
        root: ['./src'],
        extensions: ['.ios.js', '.android.js', '.js', '.ts', '.tsx', '.json'],
        alias: {
          '@screens': './src/screens',
          '@components': './src/components',
          '@services': './src/services',
          '@context': './src/context',
          '@types': './src/types',
          '@navigation': './src/navigation',
          '@utils': './src/utils'
        }
      }
    ]
  ]
};
