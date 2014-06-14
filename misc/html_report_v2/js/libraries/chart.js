angular.module('ui.chart', [])
  .directive('uiChart', ['$window', function ($window) {
    return {
      restrict: 'EACM',
      template: '<div></div>',
      replace: true,
      link: function (scope, elem, attrs) {
        var renderChart = function () {
          var data = scope.$eval(attrs.uiChart);
          elem.html('');
          if (!angular.isArray(data)) {
            return;
          }

          var opts = {};
          if (!angular.isUndefined(attrs.chartOptions)) {
            opts = scope.$eval(attrs.chartOptions);
            if (!angular.isObject(opts)) {
              throw 'Invalid ui.chart options attribute';
            }
          }

          elem.jqplot(data, opts);
          if(attrs.resize === "true"){
             elem.css("height", (320+(data[0].length*25))+"px");
          }
         
        };

        scope.$watch(attrs.uiChart, function () {
          renderChart();
        }, true);

        scope.$watch(attrs.chartOptions, function () {
          renderChart();
        });

        angular.element($window).bind('resize', function(){
          renderChart();
        });
      }
    };
  }]);