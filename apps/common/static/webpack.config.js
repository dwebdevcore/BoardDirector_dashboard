const webpack = require('webpack');

module.exports = {
    entry: {
        'voting.entry': ['./js.es6/voting.entry.js'],
        'voting-vote.entry': ['./js.es6/voting-vote.entry.js'],
    },
    output: {
        path: __dirname + '/js.generated',
        filename: "[name].js"
    },
    watch: true,
    devtool: 'source-map',
    module: {
        loaders: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: 'babel-loader'
            }
        ]
    },
    externals: {
        'vue': 'Vue',
        'vue-router': 'VueRouter',
        'jquery': 'jQuery',
        'moment': 'moment',
        'vue2-selectize': 'Selectize',
    },
    plugins: [
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('production')
        }),
        // Tradeoff - compiled sources are stored in git so it shouldn't change whole file on each commit.
        // File name hashing should be on Django side.
        // No special build process is needed this way.
        new webpack.optimize.UglifyJsPlugin({
            beautify: true,
            mangle: false,
            compress: true,
            comments: false,
            sourceMap: true
        })
    ]
};