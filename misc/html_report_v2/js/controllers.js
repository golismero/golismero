var app = angular.module('golismero-report', [
	'golismero-report-services',
	'ui.chart',
	'templates-app',
	'xeditable',
	'ui.bootstrap',
	'colorpicker.module'
]);
app.config(['dataAccessProvider', function(dataAccessProvider){
    dataAccessProvider.setData(data);
}]);

app.filter('unique', function() {
    return function(input, key) {
        var unique = {};
        var uniqueList = [];
        for(var i = 0; i < input.length; i++){
            if(typeof unique[input[i][key]] == "undefined"){
                unique[input[i][key]] = "";
                uniqueList.push(input[i]);
            }
        }
        return uniqueList;
    };
});
app.value('charting', {
      pieChartOptions: {
        seriesDefaults: {
		  renderer: jQuery.jqplot.PieRenderer,
		  rendererOptions: {
		    showDataLabels: true,							
		    dataLabelPositionFactor: 1.15,
			diameter:150
		  }
		},
		legend: { show:true, location: 's'},
		grid: {drawBorder:false, shadow: false}
      }
    });
app.directive('upload', [function () {
	return {
	 restrict: 'A',
	 link: function (scope, elem, attrs) {
	  var reader = new FileReader();
	  reader.onload = function (e) {
	            scope.general.image = e.target.result;
	            scope.$apply();
	        }

	        elem.on('change', function() {
	         reader.readAsDataURL(elem[0].files[0]);
	        });
	 }
	};
}]);
app.controller('reportController-chart', ['$scope', 'dataAccess','charting', function($scope, $dataAccess, charting){
	$scope.myChartOpts = charting.pieChartOptions;

	$scope.trimArray = function(array, numElements){
		var result = array.slice(0, numElements);

		if(array.length> numElements){
			var o = new Array();
			o[0] = 'Others';
			o[1] = 0;
			for(var i = numElements; i < array.length; i++){
				o[1]+=array[i][1];
			}
			result.push(o);
		}
		return result;
	}

	$scope.chartByType = [$scope.trimArray($dataAccess.getDataChartByType(), 10)];
	$scope.chartByTarget= [$scope.trimArray($dataAccess.getDataChartByTarget(), 10)];
	$scope.chartByCriticality =[$dataAccess.getDataChartByLevel()];

	$scope.$on("changeLevel", function(event, data){
		$scope.chartByCriticality =[$dataAccess.getDataChartByLevel()];
	});
	$scope.$on("changeVulnerabilityType", function(event, data){
		$scope.chartByType =[$scope.trimArray($dataAccess.getDataChartByType(), 10)];
	});
	$scope.$on("deleteVuln", function(event, data){
		$scope.chartByTarget= [$scope.trimArray($dataAccess.getDataChartByTarget(), 10)];
		$scope.chartByType =[$scope.trimArray($dataAccess.getDataChartByType(), 10)];
		$scope.chartByCriticality =[$dataAccess.getDataChartByLevel()];
	});
	
}])

app.controller('reportController', ['$scope', 'dataAccess', 'pdfService', '$filter', '$modal', '$timeout','$window','browser','saveService' , function($scope, $dataAccess, $pdfService, $filter, $modal, $timeout,$window, browser,saveService){

	$scope.logoGolismero = "data:image/png;base64,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";
	$scope.vulnerabilities = $dataAccess.getTargetTechnical();

	targetsTemp =$dataAccess.getAuditScope();
	targetsTemp.unshift('');
	$scope.targets = targetsTemp;
	$scope.targetsResume =$dataAccess.getTargets();

	var arrayVulnerabilities =  $dataAccess.getTargetTechnical().slice(0);//clonamos el array para luego manipularlo
	arrayVulnerabilities.unshift({display_name:''});
    $scope.vulnerabilitiesSelect = arrayVulnerabilities;

    $scope.search = {target_id:'', display_name:''};
    $scope.summary = $dataAccess.getSummary();	
	$scope.vulnsByLevel = $dataAccess.getDataVulnsByLevel();
	$scope.dir = "+";
    $scope.field="level";
    $scope.order = $scope.dir+$scope.field;
    $scope.dataTechnical = $dataAccess.getTargetTechnical();

    $scope.levels = [{value:4, label:'Informational'},
					{value:3, label:'Low'},
					{value:2, label:'Middle'},
					{value:1, label:'High'},
					{value:0, label:'Critical'}];

    $scope.obtainLevel = function(level){
		switch(level){
			case 0: return "critical";
			case 1: return "high";
			case 2: return "middle";
			case 3: return "low";
			case 4: return "informational";
		}
	}

	$scope.saveHTML = function(){
		
		if(browser.value==="safari"){
			var messageInstance = $modal.open({
				templateUrl: 'message.tpl.html',
				controller: MessageController,
				resolve: {
					message: function () {
						return ""
					}
				}
			});

			messageInstance.result.then(function () {
				saveService.saveHTML($window.copyhead, $window.copybody, $dataAccess.getData());
			}, function () {
				//dimiss function
			});
		
		}else{
			saveService.saveHTML($window.copyhead, $window.copybody, $dataAccess.getData());
		}
		
	}
    $scope.sortBy = function(field){
    	if(field == $scope.field){
			if($scope.dir == '+'){
    			$scope.dir = '-';
    		}else{
    			$scope.dir = '+';
    		}
    	}
    	$scope.field= field;
    	$scope.order = $scope.dir+$scope.field;
    }

    $scope.goTo = function(item){
    	$('body,html').stop(true,true).animate({
			scrollTop: $("[data-anchor='technical-"+item+"']").first().offset().top -80
		},1000);
    };

    $scope.obtainTarget = function(id){
		return $dataAccess.getTargetById(id);	    		
	}	

	

	
	$scope.updateLevels = function(item){
		$dataAccess.updateDataVulnsByLevel();
		$scope.$broadcast("changeLevel");
	}

	$scope.updateVulnerabilityType = function(item){
		$dataAccess.updateDataVulnsByType();
		$scope.$broadcast("changeVulnerabilityType");
	}

	

	$scope.deleteItem = function(index, item){

		var modalInstance = $modal.open({
			templateUrl: 'confirm.tpl.html',
			controller: ConfirmDeleteController,
			resolve: {
				vulnerability: function () {
					return item;
				}
			}
		});

		modalInstance.result.then(function (deleteVulnerability) {
			if(deleteVulnerability){
				for(var i= 0; i <$scope.vulnerabilities.length; i++){
					if($scope.vulnerabilities[i].identity==item.identity){
						$scope.vulnerabilities.splice(i, 1);
						break;
					}
				}		
				$scope.updateLevels();
				$scope.updateVulnerabilityType();
				$dataAccess.initDataTarget($scope.vulnerabilities);
				$scope.targetsResume =$dataAccess.getTargets();
				$scope.$broadcast("deleteVuln");
			}
		}, function () {
			//dimiss function
		});

		
	}

	$scope.downloadPdf = function(){

		var modalInstance = $modal.open({
			templateUrl: 'custompdf.tpl.html',
			controller: PdfCustomController,
			size:'lg',
			resolve: {
				data: function(){
					return {
						imgLogo: $scope.logoGolismero,
						auditName: $dataAccess.getSummary().audit_name
					}
				}
			}
		});

		modalInstance.result.then(function (generalInfo) {
			if(generalInfo){
				generalInfo.targetTechnical = $filter('orderBy')($dataAccess.getTargetTechnical(), $scope.order);
				generalInfo.summary.auditScope = $scope.targetsResume;
				generalInfo.summary.summary = $scope.summary;
				generalInfo.summary.stats = $scope.vulnsByLevel;
				$pdfService.createPdf(generalInfo, $("#chartByCriticality").jqplotToImageStr({}),$("#chartByType").jqplotToImageStr({}),$("#chartByTarget").jqplotToImageStr({}));
				
				
			}
		}, function () {
			//dimiss function
		});		
	}


	//controllers modals
	var MessageController = ['$scope','$modalInstance','message',function($scope, $modalInstance, message){
		$scope.message = message;

		$scope.accept = function(){
			$modalInstance.close(true);
		}
		
	}];

	var ConfirmDeleteController = ['$scope','$modalInstance','vulnerability',function($scope, $modalInstance, vulnerability){
		$scope.vulnerability = vulnerability;

		$scope.accept = function(){
			$modalInstance.close(true);
		}
		$scope.close = function(){
			$modalInstance.close(false);
		}
	}];

	//controllers modals
	var PdfCustomController = ['$scope','$modalInstance','data', function($scope, $modalInstance, data){
		
		$scope.general = {
			templateFooter :"%currentPage% of %totalPages%",
			templateHeader: "GoLismero Project - Report",
			enabledHeader:true,
			enabledFooter : true,
			auditName : "Audit name: " + data.auditName,
			image: data.imgLogo,
			orientation: 'portrait',
			summary:{
				showSummary:true,
				showTargets:true,
				showTimes:true,
				showTotals:true
			},
			charts:{
				showCharts:true,
				showVulnCriticality:true,
				showVulnsType:true,
				showVulnsTarget:true
			},
			vulnerabilities:{
				showVulnerabilities:true
			},
			techReport:{
				showTechnicalReport:true
			},
			styles:{
				high:{
			    	color:'#b00700',
			     	description:"Style that sets the text of criticality 'High'"
			    },
			    middle:{
			    	color:'#d7ac00',
			     	description:"Style that sets the text of criticality 'Middle'"
			    },
			    low:{
			    	color:'#019127',
			     	description:"Style that sets the text of criticality 'Low'"
			    },
			    informational:{
			    	color:'#0080ff',
			     	description:"Style that sets the text of criticality 'Informational'"
			    },
			    header: {
			      fontSize: 22,
			      bold: true,
			      margin:[0, 17, 0, 0],
			      description:"Style that sets the title of report"
			    },
			    h2: {
			      fontSize: 18,
			      bold: true,
			      description:"Style that sets the text of the titles of the sections"
			    },
			    h3:{
					fontSize: 12,
					bold:true,
			     	description:"Style that sets the text of the titles within sections"
			    },
			    th:{
					fontSize:10,
					bold:true,
			     	description:"Style that sets the text of headers of tables"
			    },
			    detail: {
			      fontSize: 16,
			      bold: true,
			      description:"Style that sets the text of title of details panel"
			    },			    
			    title:{
			    	fontSize: 14,
			      	bold: true,
			     	description:"Style that sets the text of the vulnerability name of details panel"
			    },
			    critical:{
			    	color:'#b40a9d',
			     	description:"Style that sets the text of criticality 'Critical'"
			    },			   
			    otherText:{
			    	fontSize:10,
			     	description:"Style that sets the other texts (not titles, headers, etc)"
			    },			    
			    headerPage : {
			    	alignment:'right',
			    	margin:10,
			    	description:"Style that sets the text of header"
			    },
			    footerPage: {
			    	alignment:"right",
			    	margin:10,
			    	description:"Style that sets the text of footer"			    	
			    }
			}
		}

		
		

		$scope.generate = function(action){
			$scope.general.action = action;
			var messageInstance = $modal.open({
				templateUrl: 'message.tpl.html',
				controller: MessageController,
				resolve: {
					message: function () {
						return "The process is slow and can block the browser. Please wait for it to finish.";
					}
				}
			});

			messageInstance.result.then(function () {
				$modalInstance.close($scope.general);
			}, function () {
				//dimiss function
			});
		}
		$scope.cancel = function(){
			$modalInstance.dismiss();
		}
	}];

	$timeout(function(){$scope.loaded = true;});
}])
;

