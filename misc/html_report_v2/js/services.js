angular.module('golismero-report-services', [])
.service('browser', ['$window', function($window) {
	var _self = this;
    var userAgent = $window.navigator.userAgent;
    
    var browsers = {chrome: /chrome/i, safari: /safari/i, firefox: /firefox/i, ie: /internet explorer/i};
    angular.forEach(browsers, function(key, value) {

        if (key.test(userAgent) && !_self.value) {
            _self.value = value;
        }
    });

}])
.provider('dataAccess', [ function(){	
	this.data = {};

	this.$get = function(){
		var data = this.data;
		var targetsMap = {};
		var service = {};
		var auditScope = data.audit_scope;
		$.each(this.data.resources, function(key, val){		
			targetsMap[key] = val;
		});
		
		service.getData = function(){
			return data;
		}
		service.getTargetById = function(id){
			if(id){
				var d = targetsMap[id];
				if(d){
				    return d.display_content;
				}
			}
			return "";
		};
		service.getSummary = function(){
			return data.summary;
		}

		var vulnerabilitiesByTarget = [];

		var nameResource = service.getSummary().audit_name.toUpperCase();
		if(service.getSummary().audit_name.length>=3){
			nameResource = nameResource.substring(0,3);
		}
		nameResource +="-";
		var i = 1;
		$.each(this.data.vulnerabilities, function(key, val){		
			//agrego un campo que es el name que le das al id. Sirve para cuando se quiere modificar el id,
			//realmente no se modifica el id si no un nombre que l epones al id
			if(!val.nameIdentity){

				val.nameIdentity = nameResource +i;
				i++;
			}
			if(!val.resource){

				val.resource = service.getTargetById(val.target_id);
			}			
			if(!vulnerabilitiesByTarget[val['resource']]){
				vulnerabilitiesByTarget[val['resource']] = 0;
			}
			vulnerabilitiesByTarget[val['resource']]+=1;
		});

		

		service.getDataVulnsByLevel= function(){
			return data.stats.vulns_by_level;
		}
		service.updateDataVulnsByLevel = function(){
			data.stats.vulns_by_level.High=0;
			data.stats.vulns_by_level.Middle=0;
			data.stats.vulns_by_level.Critical=0;
			data.stats.vulns_by_level.Informational=0;
			data.stats.vulns_by_level.Low=0;
			$.each(data.vulnerabilities, function(key, val){		
				switch(val.level){
					case 0: data.stats.vulns_by_level.Critical++;break;
					case 1: data.stats.vulns_by_level.High++;break;
					case 2: data.stats.vulns_by_level.Middle++;break;
					case 3: data.stats.vulns_by_level.Low++;break;
					case 4: data.stats.vulns_by_level.Informational++;break;
				};
			});
		}

		service.updateDataVulnsByType = function(){
			data.stats.vulns_by_type = {};
			
			$.each(data.vulnerabilities, function(key, val){
				if(!data.stats.vulns_by_type[val.display_name])	{
					data.stats.vulns_by_type[val.display_name] = 0;
				}	
				data.stats.vulns_by_type[val.display_name]++;
			});
		}

		service.getDataChartByType = function(){
			var dataChar = new Array();
			$.each(data.stats.vulns_by_type, function(key, val){		
				var o = new Array();
				o[0] = key;
				o[1] = val;
				dataChar.push(o);
			});
			return dataChar;
		}

		
		service.getDataChartByTarget = function(){
			var dataChar = new Array();
			$(service.getAuditScope()).each(function(index,v){
				var o = new Array();
				o[0] = v;
				o[1] = vulnerabilitiesByTarget[v];
				if(o[1] >0){
					dataChar.push(o);
					}
			});
			return dataChar;
		};
		service.getAuditScope = function(){
			var targetsScope = new Array();
			if(auditScope.domains){
				$.each(auditScope.domains, function(key, value){
					targetsScope.push(value);
				});
			}
			if(auditScope.web_pages){
				$.each(auditScope.web_pages, function(key, value){
					targetsScope.push(value);
				});
			}
			if(auditScope.addresses){
				$.each(auditScope.addresses, function(key, value){
					targetsScope.push(value);
				});
			}
			if(auditScope.roots){
				$.each(auditScope.roots, function(key, value){
					targetsScope.push(value);
				});
			}
			return targetsScope;
		};
		
		service.getDataChartByLevel = function(){
			var dataChar = new Array();

			$.each(data.stats.vulns_by_level, function(key, val){		
				var o = new Array();
				o[0] = key;
				o[1] = val;
				dataChar.push(o);
			});

			return dataChar;
		};
		service.getTargetTechnical = function(){
			return data.vulnerabilities;
		};
		service.getStats = function(){
			return data.stats;
		};
		
		service.initDataTarget = function(vulns){
			
			var targetsMapTemp = {};
			vulnerabilitiesByTarget = [];
			for(val in vulns){
				if(!targetsMapTemp[vulns[val].target_id]){
					targetsMapTemp[vulns[val].target_id] = targetsMap[vulns[val].target_id];
				}
				if(!vulnerabilitiesByTarget[vulns[val]['resource']]){
					vulnerabilitiesByTarget[vulns[val]['resource']] = 0;
				}
				vulnerabilitiesByTarget[vulns[val]['resource']]+=1;
			}
			targetsMap = targetsMapTemp;
		}
		service.getTargets = function(){
			return targetsMap;
		}

		return service;
	}
	this.setData = function(data) {
        this.data = data;
    };
}])
.factory('saveService', [function(){
	var doc_impl = document.implementation;
	var xml_serializer = new XMLSerializer;
	var service = {};
	service.saveHTML = function (copyHead, copyBody, data) {
				
		var body = "<body ng-controller='reportController' ng-class='{contrast: contrast==true}'>";
		for (var i = 0; i < copyBody.length; i++) {
			
			if($(copyBody[i]).attr("id")==="databaseScript"){
				body +="<script type='text/javascript' id='databaseScript'>data="+JSON.stringify(data);
				body+="<";
				body+="/script>";

			}else{
				if(copyBody[i].outerHTML !== undefined){
					body +=copyBody[i].outerHTML+"\n";
				}
			}
			//$(body)[0].appendChild(doc.importNode(copyBody[i], true));
		}
		body +="</body>";
		var head = "<head>";
		for (var i = 0; i < copyHead.length; i++) {
			if(copyHead[i].outerHTML !== undefined){
				head +=copyHead[i].outerHTML+"\n";
			}
		}
		head+="</head>";
		//$(doc).find("#databaseScript")
		var html ="<!DOCTYPE html><html ";
		for (var j=0, attrs=$("html")[0].attributes, l=attrs.length; j<l; j++){
			html +=" "+attrs.item(j).nodeName+"='"+attrs.item(j).nodeValue+"'";		  
		}
		html+=">";
		
		saveAs(new window.Blob([html + head+body+"</html>"], {type: "application/octet-stream;charset=" + document.characterSet}), "report.html");
	};
	return service; 
}])

.factory('pdfService', ['dataAccess', function($dataAccess){
	var service = {};

	service.downloadPdf = function(generalInfo, docDefinition){
		//abrir porque funciona en chrome y firefox
		if(generalInfo.action==="open"){
			pdfMake.createPdf(docDefinition).open();
		}else{
			pdfMake.createPdf(docDefinition).download();
		}
		//
	};
	function createHeader(generalInfo){
		var header = {
				    columns:[
				        {
			                width: 80,
	                        image: generalInfo.image
				        },
				        {
				            width: '*',
				            style:"header",
		                    text: [generalInfo.auditName]
				        }
				    ],
				    columnGap: 50
				};
		return header;
	}

	function createSummary(generalInfo){
		var summary = generalInfo.summary.summary;
		var targets = "";
		var auditScope = generalInfo.summary.auditScope;
		if(generalInfo.summary.showTargets){
			for(var i in auditScope){
				targets+=auditScope[i].display_content+"; ";
			}
		}
		var stats = generalInfo.summary.stats;
		
		var summaryjson= {
			        table: {
		                headerRows:1,
		                widths: [ ],		        
		                body: [
		                	[],//header
		                	[]//content
		                ]
		          	}
			    };
		if(generalInfo.summary.showTargets){
			summaryjson.table.widths.push('*');
			summaryjson.table.body[0].push({ text: 'Targets', style:'th' });
			summaryjson.table.body[1].push({text:targets, style:'otherText'});
		}
		if(generalInfo.summary.showTimes){
			summaryjson.table.widths.push('*');
			summaryjson.table.body[0].push({ text: 'Time', style:'th' });
			summaryjson.table.body[1].push([
		                      	{ text: 'Start:', style:'h3' },{text:summary.start_time, style:'otherText'},
		                      	{ text: 'End:', style:'h3' },{text:summary.stop_time, style:'otherText'},
		                      	{ text: 'Total:', style:'h3' },{text:summary.run_time, style:'otherText'}
	                      	]);
		}
		if(generalInfo.summary.showTotals){
			summaryjson.table.widths.push('*');
			summaryjson.table.body[0].push( { text: 'Vulnerabilities summary', style:'th' });
			/*summaryjson.table.body[1].push([
		                      	{ text: 'Total:', style:'h3' },{text:(stats.High + stats.Low + stats.Middle + stats.Critical + stats.Informational)+'', style:'otherText'},
		                      	{
		                      		columns:[
		                      			[{ text: 'Critical:', style:['h3', 'critical'] },{text:stats.Critical.toString(), style:'otherText'}], 
			                    		[{ text: 'High:', style:['h3', 'high'] },{text:stats.High.toString(), style:'otherText'}]
		                      		]
		                      	},
		                      	{
		                      		columns:[
		                      			[{ text: 'Middle:', style:['h3', 'middle'] },{text:stats.Middle.toString(), style:'otherText'}], 
			                    		[{ text: 'Low:', style:['h3', 'low'] },{text:stats.Low.toString(), style:'otherText'}]
		                      		]
		                      	},			                    
			                    { text: 'Informational:', style:['h3', 'informational']},{text:stats.Informational.toString(), style:'otherText'}
		                    ]);
			*/
			summaryjson.table.body[1].push({table: {
		        headerRows: 1,
		        widths: [ '*', 'auto'],

		        body: [
		          [ { text: 'Level:', style:'h3' }, { text: 'Number:', style:'h3' }],
		          [ { text: 'Critical:', style:['h3', 'critical'] }, {text:stats.Critical.toString(), style:'otherText'} ],
		          [ { text: 'High:', style:['h3', 'high'] }, {text:stats.High.toString(), style:'otherText'} ],
		          [ { text: 'Middle:', style:['h3', 'middle'] }, {text:stats.Middle.toString(), style:'otherText'} ],
		          [ { text: 'Low:', style:['h3', 'low'] }, {text:stats.Low.toString(), style:'otherText'} ],
		          [ { text: 'Informational:', style:['h3', 'informational']}, {text:stats.Informational.toString(), style:'otherText'}],
		          [ { text: 'Total:', style:'h3' }, {text:(stats.High + stats.Low + stats.Middle + stats.Critical + stats.Informational)+'', style:'otherText'}],
		        ]
		      }});
		}

		return summaryjson;
	}
	function createCharts(generalInfo, chartLevel, chartType, chartTarget){
		
		var chartsjson= {
			        table: {
		                headerRows:1,
		                widths: [ ],		        
		                body: [
	                  	[],
	                  	[]
		            ]
		          }
			    };
		if(generalInfo.charts.showVulnCriticality){
			chartsjson.table.widths.push("*");
			chartsjson.table.body[0].push({ text: 'Vulnerabilities by criticality', style:'th' });
			chartsjson.table.body[1].push({image:chartLevel, width: 150, aligment:'middle'});
		}
		if(generalInfo.charts.showVulnsType){
			chartsjson.table.widths.push("*");
			chartsjson.table.body[0].push({ text: 'Vulnerabilities by type', style:'th' });
			chartsjson.table.body[1].push({image:chartType, width: 150, aligment:'middle'});
		}
		if(generalInfo.charts.showVulnsTarget){
			chartsjson.table.widths.push("*");
			chartsjson.table.body[0].push({ text: 'Vulnerabilities by target', style:'th' });
			chartsjson.table.body[1].push({image:chartTarget, width: 150, aligment:'middle'});
		}
		return chartsjson;
	}
	function obtainLevel(level){
		switch(parseInt(level)){
			case 0: return {text:"critical", style:['text','critical']};
			case 1: return {text:"high", style:['text','high']};
			case 2: return {text:"middle", style:['text','middle']};
			case 3: return {text:"low", style:['text','low']};
			case 4: return {text:"informational", style:['text','informational']};
		}
	};

	function createVulnerabilitiesTable(generalInfo){
		var vulns = generalInfo.targetTechnical;
		var rows = [[ { text: 'ID', style:'th' }, { text: 'Target', style:'th' }, { text: 'Vulnerability', style:'th' }, { text: 'Criticality', style:'th' } ]];
		for(var i in vulns){
			var obj = [
				{text:vulns[i].nameIdentity, style:'otherText'},
				{text:vulns[i].resource, style:'otherText'},
				{text:vulns[i].display_name, style:'otherText'},
				obtainLevel(vulns[i].level)
			];
			rows.push(obj);
		}
		var table = {
			table:{
				headerRows:1,
				style:'miestilo',
			    widths: [ 'auto', '*', '*', "auto" ],
			    body:rows
			}	
		};
		return table;
	}

	function obtainTarget(id){
		return $dataAccess.getTargetById(id);	    		
	}
	function createTechnicalTable(generalInfo){
		var dataTech = generalInfo.targetTechnical;
		var result = [];
		for(var tech  in dataTech){
			var item = dataTech[tech];
			var table = {
				table:{
					headerRows:1,
				    widths: [ 'auto', '*', '*', "auto" ],
				    body:[
				    	[ { text: 'ID', style:"th" }, { text: 'Target', style:"th" }, { text: 'Vulnerability', style:"th" }, { text: 'Criticality',style:"th" } ],
				    	[{text:item.nameIdentity, style:'otherText'},{text:item.resource, style:'otherText'},{text:item.display_name, style:'otherText'},obtainLevel(item.level)]
				    ]
				}	
			};
			var taxonomy = [{ text: 'Taxonomy:', bold: true }];
			for(var i in item.taxonomy){
				taxonomy.push({text:item.taxonomy[i], style:'otherText'});
			}
			var references = [{ text: 'References:', bold: true }];
			for(var i in item.references){
				references.push({text:item.references[i], style:'otherText'});
			}
			var tableDetail = {
				table:{
					headerRows:0,
					widths:['*'],
					body:[
						[{ text: 'Details', style: 'detail' }],
						[{ text: item.title, style: 'title' }],
						[
							//table de details
							{
								columns:[
									[{ text: 'Target:',style:"h3" },{text:item.resource, style:"text"}, { text: 'Vulnerability:', style:"h3" }, {text:item.display_name +" ("+item.data_subtype+")", style:"text"} , { text: 'Plugin ID:', style:"h3" },{text:item.plugin_id, style:"text"},{ text: 'Impact', style:"h3" },{text:item.impact+"", style:"text"}],
									[{ text: 'Criticality:', style:"h3" },obtainLevel(item.level), { text: 'Plugin name:', style:"h3" },{text:item.plugin_name, style:"text"},{ text: 'Severity:', style:"h3" },{text:item.severity+"", style:"text"}],
									[{ text: 'Risk:', style:"h3" },{text:item.risk+"", style:"text"}]
								]
							}
						],
						[
							{
								columns:[
									taxonomy
								]
							}
							
						],
						[
							{
								columns:[
									[{ text: 'Description:', style:"h3" }, {text:item.description, style:"text"}]
								]
							}
							
						],
						[
							{
								columns:[
									[{ text: 'Solution:', style:"h3" }, {text:item.solution, style:"text"}]
								]
							}
							
						],
						[
							{
								columns:[
									references
								]
							}
							
						],
					]
				}
			}
			result.push(table);
			result.push(tableDetail);
			result.push(" ");
		}
		return result;
	}

	service.createPdf = function(generalInfo,chartLevel, chartType, chartTarget){
		var dd = {			
			pageOrientation: generalInfo.orientation,	    
			content: [			    
				createHeader(generalInfo),
				' ',
			],

		  	styles:generalInfo.styles
		};
	
		if(generalInfo.enabledHeader){
			dd.header = function(currentPage, pageCount) {
				var result = generalInfo.templateHeader.replace("%currentPage%", currentPage).replace("%totalPages%", pageCount);
				return { text: result,  style:'headerPage' };
			}
		}
		if(generalInfo.enabledFooter){
			dd.footer = function(currentPage, pageCount) {
				var result = generalInfo.templateFooter.replace("%currentPage%", currentPage).replace("%totalPages%", pageCount);
				return { text: result,  style:'footerPage' };
			}
		}
		if(generalInfo.summary.showSummary){
			dd.content.push(createSummary(generalInfo));
			dd.content.push(' ');
		}
		if(generalInfo.charts.showCharts){
			dd.content.push(createCharts(generalInfo, chartLevel, chartType, chartTarget ));
			dd.content.push(' ');
		}
		if(generalInfo.vulnerabilities.showVulnerabilities){
			dd.content.push({text:"Vulnerabilities", style:"h2"});
			dd.content.push(createVulnerabilitiesTable(generalInfo))
			dd.content.push(' ');
		}
		if(generalInfo.techReport.showTechnicalReport){
			dd.content.push({text:"Technical report", style:"h2"});
			var technicalTable = createTechnicalTable(generalInfo);
			for(var i in technicalTable){
				dd.content.push(technicalTable[i]);
			}
		}
		
		
		service.downloadPdf(generalInfo, dd);
	};

	return service;
}]);