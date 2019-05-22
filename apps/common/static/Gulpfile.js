var gulp = require('gulp'),
    sass = require('gulp-sass'),
    sourcemaps = require('gulp-sourcemaps'),
    moduleImporter = require('sass-module-importer'),
    webpackStream = require('webpack-stream'),
    webpack2 = require('webpack'),
    browserSync = require('browser-sync').create(),
    named = require('vinyl-named');


gulp.task('browser-sync', function () {
    browserSync.init({
        proxy: "localhost:8000"
    });
});

gulp.task('webpack', function () {
    // process.env.NODE_ENV = 'production';
    let config = require('./webpack.config');
    config.watch = false;

    return gulp.src('js.es6/voting.*.js')
        .pipe(named())
        .pipe(webpackStream(config, webpack2))
        .pipe(gulp.dest('js.generated/'))
        .pipe(browserSync.stream({match: '**/*.js'}));
});

gulp.task('styles', function () {
    gulp.src('sass/**/*.scss')
        .pipe(sourcemaps.init())
        .pipe(sass({importer: moduleImporter()}).on('error', sass.logError))
        .pipe(sourcemaps.write('./maps'))
        .pipe(gulp.dest('./css.generated')) // So that it's on same level as sass for easy images references.
        .pipe(browserSync.stream({match: '**/*.css'}));
});

gulp.task('watch-resources', ['styles', 'browser-sync'], function () {
    gulp.watch(['sass/**/*.scss', '../css/all.css', '../css/custom.css'], ['styles']);
    gulp.watch(['js/**/*.js', 'js.generated/**/*.js', '../templates/**/*.html']).on("change", browserSync.reload);
});

gulp.task('default', ['watch-resources', 'webpack'], function () {
    // gulp.start('webpack');
});
