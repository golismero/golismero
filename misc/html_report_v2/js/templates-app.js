angular.module('templates-app', ['confirm.tpl.html', 'custompdf.tpl.html', 'message.tpl.html', 'rowVulnTechnical.tpl.html', 'rowVulnerabilities.tpl.html']);

angular.module("confirm.tpl.html", []).run(["$templateCache", function($templateCache) {
  $templateCache.put("confirm.tpl.html",
    "<div class=\"modal-header\">\n" +
    "    <h3 class=\"modal-title\">Confirm delete vulnerability</h3>\n" +
    "</div>\n" +
    "<div class=\"modal-body\">\n" +
    "    <p>Are you sure you want to delete the vulnerability {{vulnerability.nameIdentity}}?</p>\n" +
    "</div>\n" +
    "<div class=\"modal-footer\">\n" +
    "    <button class=\"btn btn-default\" ng-click=\"accept()\">Yes</button>\n" +
    "    <button class=\"btn btn-primary\" ng-click=\"close()\">No</button>\n" +
    "</div>");
}]);

angular.module("custompdf.tpl.html", []).run(["$templateCache", function($templateCache) {
  $templateCache.put("custompdf.tpl.html",
    "<div class=\"modal-header\">\n" +
    "    <h3 class=\"modal-title\">Generate pdf</h3>\n" +
    "</div>\n" +
    "<div class=\"modal-body\">\n" +
    "	<tabset>\n" +
    "\n" +
    "		<tab heading=\"General\">\n" +
    "		    <div class=\"row\">\n" +
    "		    	<div class=\"col-sm-4\">\n" +
    "		    		<img class=\"img-logo\" ng-if=\"general.image\" ng-src=\"{{general.image}}\" alt=\"\">\n" +
    "					<input upload type=\"file\" name=\"upload\">\n" +
    "		    	</div>\n" +
    "		    	<div class=\"col-sm-8\">\n" +
    "		    		<form class=\"form-horizontal\" role=\"form\">\n" +
    "		    			<div class=\"form-group\">\n" +
    "							<label for=\"name-audit\" class=\"col-sm-3 control-label\">Audit name:</label>\n" +
    "							<div class=\"col-sm-9\">\n" +
    "								<input type=\"text\" class=\"form-control\" id=\"name-audit\" placeholder=\"Audit name\" ng-model=\"general.auditName\">\n" +
    "							</div>\n" +
    "						</div>\n" +
    "						<div class=\"form-group\">\n" +
    "							<label for=\"header\" class=\"col-sm-3 control-label\">Header:</label>\n" +
    "							<div class=\"col-sm-7\">\n" +
    "								<input type=\"text\" class=\"form-control\" id=\"footer\" placeholder=\"Header template\" ng-disabled=\"!general.enabledHeader\" ng-model=\"general.templateHeader\">						\n" +
    "							</div>\n" +
    "							<div class=\"col-sm-2\">\n" +
    "								<input type=\"checkbox\" class=\"\" id=\"header\" placeholder=\"Header template\" ng-model=\"general.enabledHeader\" >\n" +
    "							</div>\n" +
    "						</div>\n" +
    "						<div class=\"form-group\">\n" +
    "							<label for=\"name-audit\" class=\"col-sm-3 control-label\">Footer:</label>\n" +
    "							<div class=\"col-sm-7\">\n" +
    "								<input type=\"text\" class=\"form-control\" id=\"footer\" placeholder=\"Footer template\" ng-disabled=\"!general.enabledFooter\" ng-model=\"general.templateFooter\">						\n" +
    "							</div>\n" +
    "							<div class=\"col-sm-2\">\n" +
    "								<input type=\"checkbox\" class=\"\" id=\"footer\" placeholder=\"Footer template\" ng-model=\"general.enabledFooter\">\n" +
    "							</div>\n" +
    "						</div>\n" +
    "						<div class=\"form-group\">\n" +
    "							<label for=\"name-audit\" class=\"col-sm-3 control-label\">Orientation:</label>\n" +
    "							<div class=\"col-sm-9\">\n" +
    "								<input type=\"radio\" ng-model=\"general.orientation\" value=\"landscape\">Landscape</input>\n" +
    "								<input type=\"radio\" ng-model=\"general.orientation\" value=\"portrait\">Portrait</input>	\n" +
    "							</div>\n" +
    "							\n" +
    "						</div>\n" +
    "		    		</form>\n" +
    "		    	</div>\n" +
    "		    </div>\n" +
    "		    <hr>\n" +
    "		    <div class=\"row\">\n" +
    "		    	<div class=\"col-sm-3\">\n" +
    "		    		<h4>Summary block</h4>\n" +
    "		    		<div><input type=\"checkbox\" id=\"showSummary\" ng-model=\"general.summary.showSummary\">Show summary</input></div>\n" +
    "		    		<div class=\"submenu\"><input type=\"checkbox\" id=\"showTargets\" ng-model=\"general.summary.showTargets\" ng-disabled=\"!general.summary.showSummary\">Show targets</input></div>\n" +
    "					<div class=\"submenu\"><input type=\"checkbox\" id=\"showTimes\" ng-model=\"general.summary.showTimes\" ng-disabled=\"!general.summary.showSummary\">Show times</input></div>\n" +
    "					<div class=\"submenu\"><input type=\"checkbox\" id=\"showTotals\" ng-model=\"general.summary.showTotals\" ng-disabled=\"!general.summary.showSummary\">Show totals</input></div>			\n" +
    "		    	</div>\n" +
    "		    	<div class=\"col-sm-3\">\n" +
    "		    		<h4>Charts block</h4>\n" +
    "		    		<div><input type=\"checkbox\" id=\"showSummary\" ng-model=\"general.charts.showCharts\">Show charts</input></div>\n" +
    "		    		<div class=\"submenu\"><input type=\"checkbox\" id=\"showTargets\" ng-model=\"general.charts.showVulnCriticality\" ng-disabled=\"!general.charts.showCharts\">Show chart vulnerabilities by criticality</input></div>\n" +
    "					<div class=\"submenu\"><input type=\"checkbox\" id=\"showTimes\" ng-model=\"general.charts.showVulnsType\"  ng-disabled=\"!general.charts.showCharts\">Show chart vulnerabilities by type</input></div>\n" +
    "					<div class=\"submenu\"><input type=\"checkbox\" id=\"showTotals\" ng-model=\"general.charts.showVulnsTarget\" ng-disabled=\"!general.charts.showCharts\">Show chart vulnerabilities by target</input></div>		\n" +
    "		    	</div>\n" +
    "		    	<div class=\"col-sm-3\">\n" +
    "		    		<h4>Vulnerabilites block</h4>\n" +
    "		    		<div><input type=\"checkbox\" id=\"showSummary\" ng-model=\"general.vulnerabilities.showVulnerabilities\">Show vulnerabilities</input></div>    			\n" +
    "		    	</div>\n" +
    "		    	<div class=\"col-sm-3\">\n" +
    "		    		<h4>Technical report block</h4>\n" +
    "		    		<div><input type=\"checkbox\" id=\"showSummary\" ng-model=\"general.techReport.showTechnicalReport\">Show technical report</input></div>    			\n" +
    "		    	</div>\n" +
    "		    </div>\n" +
    "    	</tab>\n" +
    "    	<tab heading=\"Styles\" >\n" +
    "    		\n" +
    "			<fieldset class=\"dataStyle\" ng-repeat=\"(key, value) in general.styles\"> \n" +
    "    			<legend>{{key}} <span class=\"description\" tooltip=\"{{value.description}}\"><i class=\"glyphicon glyphicon-info-sign\" ></i></span></legend>\n" +
    "    			<div class=\"contentlegend\">\n" +
    "    				<div class=\"dataStyleRow\">\n" +
    "    					<div>Font-size:</div>\n" +
    "    					<input type=\"number\" ng-model=\"value.fontSize\"/>\n" +
    "    				</div>\n" +
    "    				<div class=\"dataStyleRow\">\n" +
    "    					<div>Bold</div>\n" +
    "    					<input type=\"checkbox\" ng-model=\"value.bold\"/>\n" +
    "    				</div>\n" +
    "    				\n" +
    "    				<div class=\"dataStyleRow\">\n" +
    "    					<div>Align:</div>\n" +
    "    					<select ng-model=\"value.alignment\"> \n" +
    "    						<option value=\"\"></option>\n" +
    "	    					<option value=\"left\">left</option>\n" +
    "	    					<option value=\"right\">right</option>\n" +
    "	    					<option value=\"centered\">centered</option>\n" +
    "	    					<option value=\"justified\">justified</option>\n" +
    "	    				</select>\n" +
    "    				</div>\n" +
    "    				<div class=\"dataStyleRow\">\n" +
    "    					<div>Color:</div>\n" +
    "    					<input type=\"text\" colorpicker ng-model=\"value.color\"/>\n" +
    "    				</div>\n" +
    "    			</div>\n" +
    "    		</fieldset>\n" +
    "    	\n" +
    "    	</tab>\n" +
    "    </tabset>\n" +
    "</div>\n" +
    "<div class=\"modal-footer\">\n" +
    "    <button class=\"btn btn-default\" ng-click=\"generate('open')\">Open</button>\n" +
    "    <button class=\"btn btn-default\" ng-click=\"generate('save')\">Save (recomended for IE)</button>\n" +
    "    <button class=\"btn btn-primary\" ng-click=\"cancel()\">Cancel</button>\n" +
    "</div>");
}]);

angular.module("message.tpl.html", []).run(["$templateCache", function($templateCache) {
  $templateCache.put("message.tpl.html",
    "<div class=\"modal-header\">\n" +
    "    <h3 class=\"modal-title\">Information</h3>\n" +
    "</div>\n" +
    "<div class=\"modal-body\">\n" +
    "\n" +
    "    <p ng-show=\"message !== '' \">{{message}}</p>\n" +
    "    <p ng-show=\"message==='' \">To save the custom report press <img src=\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADMAAAAWCAYAAABtwKSvAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAK5SURBVFhH3ZdbVuJAEIbZE0uSxBf3YCCvswdNuCzAxxm84DMXBUSCdwHlJsoK/kl1mjadNDnpMU/T5/zn71S6qvrrBA7k8B+N3OfnJx4eHjLVarXi5ZNHlr2pZ+7x8RHr9RpfX1/YbDY/9sVigU6nw7ebPKj3x8dHqrpJvlwuWc8cUdEJUTArbzabfLvJg3qnqZfGqSeDoSeTpXRgVPn/IgFDj5oCWbkuTNq6SS5g6MOTpXRgVPmkUW0f+Xw+pH3URuq1JAFDH6CYLm1exETNC8W9GkzewKx5cg6XDowq36uZfn0bl+E43499GYqFJGDoG0hWA7ZZxTA2H6JqmqgOt3MbDSkvUAxmeYKD/AFOlvyaD3VvqutvuhGNL9Cw/UMUe5ElYObzeUQNlMwKbtn8FpVSaG6W0IjNZenARHODuv5Tr9wq7u2WgJnNZnFdlPhrtlulC0WeLx0YVX64t+FDKddEJGDe398TNEC5WMZgOzeKOI+tkcVgGED8AAL9QpfDqPK3GpQNOa94rlxHEjBvb2+YTqc7vA+36KLPrm/gGhbOEtdPtZ5MUh3Zz1AkIMPFjeK+gKFATGeWfCoKGW5fmasLk1p9F0begNuP3xMwk8kE4/E45KewCg567LoLx3LQZfEenIKF023cn9elvMB1YOS+vncdFPIFON143UmP3+tF4r4LGArIqjMYApDnBBA0CsNE82MwO4a69xh1i578ts9W1M+PW/VQ7FsC5vX1FS8vL7L/PuSv0x6Or0PxqyP/dILX7PCPIs93HRhVPvnV0R7v/63C8fXO9QLm+fmZBbNyXZi0dZNcgnl6esrMdWDS1EvjAob+JFEwK9eFSVs3yRnM/f097u7uWGEK/tSHwyFarRbfbvKgnNFolKpuknuex3rm6Odzu91mZFmIatEPvzQjq95BzwX+AncTqgYgu3pPAAAAAElFTkSuQmCC\"/> on the new tab to save the report</p>\n" +
    "</div>\n" +
    "<div class=\"modal-footer\">\n" +
    "    <button class=\"btn btn-default\" ng-click=\"accept()\">Accept</button>\n" +
    "</div>");
}]);

angular.module("rowVulnTechnical.tpl.html", []).run(["$templateCache", function($templateCache) {
  $templateCache.put("rowVulnTechnical.tpl.html",
    "<tr data-anchor=\"technical-{{item.identity}}\" class=\"headData expanded\" ng-init=\"show=true\">\n" +
    "	<td  ng-click=\"show= !show\" class=\"tdRowTechCollapse\"><span class=\"glyphicon glyphicon-plus \" ng-show=\"show==false\"></span> <span class=\"glyphicon glyphicon-minus expanded\" ng-show=\"show == true\"></span></td>\n" +
    "	<td  class=\"tdRowTechIdentity\" ><span editable-text=\"item.nameIdentity\" buttons=\"no\">{{item.nameIdentity}}</span></td>\n" +
    "	<td  class=\"tdRowTechTarget\"><span class=\"large\">{{item.resource}}</span></td>\n" +
    "	<td  class=\"tdRowTechVuln hidden-xs\" ><span editable-text=\"item.display_name\" onaftersave=\"updateVulnerabilityType(item)\" buttons=\"no\">{{item.display_name}}</span></td>\n" +
    "	<td  class=\"tdRowTechLevel\" ><div editable-select=\"item.level\" e-ng-options=\"s.value as s.label for s in levels\" buttons=\"no\"  onaftersave=\"updateLevels(item)\"><span class=\"bold {{obtainLevel(item.level)}}Vulnerability\">{{obtainLevel(item.level)}}</span></div></td>\n" +
    "</tr>\n" +
    "<tr class=\"openVulnerabilitiesRow\" ng-show=\"show\"><td colspan=\"5\">\n" +
    "<div class=\"row \">\n" +
    "	<div class=\"col-sm-12\">\n" +
    "		<h4 editable-text=\"item.title\" buttons=\"no\">{{item.title}}</h4>\n" +
    "		<div class=\"well\">\n" +
    "			<div class=\"row\">\n" +
    "				<div class=\"col-sm-12\">\n" +
    "					<div class=\"item-form\"><span class=\"bold\">Target:</span>{{item.resource}}</div>\n" +
    "				</div>\n" +
    "			</div>\n" +
    "			<div class=\"row\">				\n" +
    "				<div class=\"col-sm-4\">\n" +
    "					<div class=\"item-form\"><span class=\"bold\">Vulnerability:</span><span class=\"editable editable-click\" editable-text=\"item.display_name\" buttons=\"no\" onaftersave=\"updateVulnerabilityType(item)\">{{item.display_name}}</span>&nbsp;(<span editable-text=\"item.data_subtype\" buttons=\"no\">{{item.data_subtype}}</span>) </div>\n" +
    "				</div>\n" +
    "				<div class=\"col-sm-4\">\n" +
    "					<div class=\"item-form\"><span class=\"bold \">Criticality:</span><span class=\"{{obtainLevel(item.level)}}Vulnerability bold editable editable-click\" editable-select=\"item.level\" e-ng-options=\"s.value as s.label for s in levels\" buttons=\"no\"  onaftersave=\"updateLevels(item)\">{{obtainLevel(item.level)}}</span> </div>\n" +
    "				</div>\n" +
    "			</div>\n" +
    "			<div class=\"row\">\n" +
    "				<div class=\"col-sm-4\">\n" +
    "					<div class=\"item-form\"><span class=\"bold\">Plugin ID:</span><span editable-text=\"item.plugin_id\" buttons=\"no\">{{item.plugin_id}}</span></div> \n" +
    "				</div>\n" +
    "				<div class=\"col-sm-4\">\n" +
    "					<div class=\"item-form\"><span class=\"bold\">Plugin name:</span><span editable-text=\"item.plugin_name\" buttons=\"no\">{{item.plugin_name}}</span></div>\n" +
    "				</div>	\n" +
    "				<div class=\"col-sm-4\">\n" +
    "				</div>			\n" +
    "			</div>\n" +
    "			<div class=\"row\">\n" +
    "				<div class=\"col-sm-4\">\n" +
    "					<div class=\"item-form\"><span class=\"bold\">Impact:</span><span editable-text=\"item.impact\" buttons=\"no\">{{item.impact}}</span> </div>\n" +
    "				</div>\n" +
    "				<div class=\"col-sm-4\">\n" +
    "					<div class=\"item-form\"><span class=\"bold\">Severity:</span><span editable-text=\"item.severity\" buttons=\"no\">{{item.severity}}</span></div>\n" +
    "				</div>	\n" +
    "				<div class=\"col-sm-4\">\n" +
    "					<div class=\"item-form\"><span class=\"bold\">Risk:</span><span editable-text=\"item.risk\" buttons=\"no\">{{item.risk}}</span></div>\n" +
    "				</div>			\n" +
    "			</div>\n" +
    "			\n" +
    "		</div>\n" +
    "		\n" +
    "		<div class=\"well\" ng-if=\"item.taxonomy\">\n" +
    "			<span class=\"bold\">Taxonomy:</span>\n" +
    "			<div ng-repeat=\"tax in item.taxonomy\">{{tax}}</div>\n" +
    "			\n" +
    "		</div>\n" +
    "		<div class=\"well\" ng-if=\"item.description\">\n" +
    "				<span class=\"bold\">Description:</span> <pre editable-textarea=\"item.description\" buttons=\"no\" e-rows=\"14\" e-cols=\"40\">{{item.description}}</pre>\n" +
    "			</div>\n" +
    "		<div class=\"well\" ng-if=\"item.solution\">\n" +
    "			<span class=\"bold\">Solution:</span> <pre editable-textarea=\"item.solution\" buttons=\"no\" e-rows=\"17\" e-cols=\"40\">{{item.solution}}</pre>\n" +
    "		</div>\n" +
    "		<div class=\"well\" ng-if=\"item.references\">	\n" +
    "			<span class=\"bold\">References:</span>\n" +
    "			<div ng-repeat=\"item in item.references\"><a href=\"{{item}}\" target=\"_blank\">{{item}}</a></div>\n" +
    "   		</div>\n" +
    "   	</div>\n" +
    "   </div>\n" +
    " </td></tr>\n" +
    "");
}]);

angular.module("rowVulnerabilities.tpl.html", []).run(["$templateCache", function($templateCache) {
  $templateCache.put("rowVulnerabilities.tpl.html",
    "<td editable-text=\"item.nameIdentity\" buttons=\"no\"><span>{{item.nameIdentity}}</span></td>\n" +
    "<td><span class=\"large\" tooltip=\"{{item.resource}}\" tooltip-placement=\"bottom\">{{item.resource }}</span></td>		\n" +
    "<td ><span editable-text=\"item.display_name\" onaftersave=\"updateVulnerabilityType(item)\" buttons=\"no\"> {{item.display_name}}</span></td>\n" +
    "<td class=\"editable editable-click\"><span class=\"bold {{obtainLevel(item.level)}}Vulnerability\" editable-select=\"item.level\" buttons=\"no\" e-ng-options=\"s.value as s.label for s in levels\" onaftersave=\"updateLevels(item)\">{{obtainLevel(item.level)}}</span></td>\n" +
    "<td><div ng-click=\"deleteItem($index, item)\" class=\"trash\"></div></td>\n" +
    "<td class=\"moreInfo\" ng-click=\"goTo(item.identity)\"><span>Details</span></td>\n" +
    "");
}]);
