const config = {
  entry: './src/index.tsx',
  module: {
    rules: [
      {
        test: /\.(ts|js)x?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-env',
              '@babel/preset-react',
              '@babel/preset-typescript',
            ],
          },
        },
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.html$/i,
        loader: 'html-loader',
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.css'],
  },
  output: {
    path: __dirname + '/build',
    filename: 'textLabelingTool.js',
    library: 'textLabelingTool',
  },
  devServer: {
    writeToDisk: true,
    hot: false,
    inline: false,
  },
  mode: 'development'
};

module.exports = config;
