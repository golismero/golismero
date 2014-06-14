module.exports = function ( grunt ) {
  
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-watch');  
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-html2js');
  grunt.loadNpmTasks('grunt-inline');

  
  var taskConfig = {
    /**
     * We read in our `package.json` file so we can access the package name and
     * version. It's already there, so we don't repeat ourselves here.
     */
    pkg: grunt.file.readJSON("package.json"),

     
	  less: {
      build: {
        options: {
          strictMath: true,
          sourceMap: false,
          outputSourceFiles: true
        },
        files: {
          'build/css/main.css': [ 'css/main.less' ]
        }
      },
      minify: {
        options: {
          cleancss: true,
          report: 'min'
        },
        files: {
          'build/css/main.css': [ 'build/css/main.css' ]
        }
      }
    },
    clean: [ 
      'build', 
      'dest'
    ],
    

    /**
     * HTML2JS is a Grunt plugin that takes all of your template files and
     * places them into JavaScript files as strings that are added to
     * AngularJS's template cache. This means that the templates too become
     * part of the initial payload as one JavaScript file. Neat!
     */
    html2js: {
      /**
       * These are the templates from `src/app`.
       */
      app: {
        options: {
			base: 'js/tpl/',
			encoding:'utf8'
        },
        src: [ 'js/**/*.tpl.html' ],
        dest: 'js/templates-app.js'
      }
      
    },
    inline: {
        dist: {
            options:{
                cssmin: true,
                uglify: true
            },
            src: [ 'index.html'],
            dest: ['build/']
        }
    }, 
    delta: {
    
      options: {
        livereload: true
      },

    
      tpls: {
        files: [ 
          'js/**/*.tpl.html'
        ],
        tasks: [ 'html2js' ]
      },

     
      less: {
        files: [ '**/*.less' ],
        tasks: [ 'less:build', 'less:minify' ]
      }

     
    }
  };

  grunt.initConfig( grunt.util._.extend( taskConfig ) );

  /**
   * In order to make it safe to just compile or copy *only* what was changed,
   * we need to ensure we are starting from a clean, fresh build. So we rename
   * the `watch` task to `delta` (that's why the configuration var above is
   * `delta`) and then add a new task called `watch` that does a clean build
   * before watching for changes.
   */
  grunt.renameTask( 'watch', 'delta' );
 
  /**
   * The `build` task gets your app ready to run for development and testing.
   */
  grunt.registerTask( 'build', [
    'clean', 'html2js', 'less:build', 'less:minify', 'inline:dist'
  ]);
};
