function initToTop(){
	    		$(".totop").hide();
				if($(this).scrollTop() > 80){
					//mostrar barra vertical lateral
					$("#lateralNavbar").show();
				}else{
					//ocultar barra
					$("#lateralNavbar").hide();
				}
				$(function(){
					$(window).scroll(function(){
						if($(this).scrollTop() > 80){
							//mostrar barra vertical lateral
							$("#lateralNavbar").show();
						}else{
							//ocultar barra
							$("#lateralNavbar").hide();
						}
						if ($(this).scrollTop()>600)
						{
							$('.totop').slideDown();
						}
						else
						{
							$('.totop').slideUp();
						}
						});

						$('.totop a').on("click touchstart", function (e) {
						e.preventDefault();
						$('body,html').animate({scrollTop: 0}, 500);
					});

				});
	    	}
	    
	    	function initLateralMenu(){
	    		$("#lateralNavbar").on("click touchstart", function(){
	    			if($(this).hasClass("showLateralMenu")){
	    				//desplegada
	    				hideLateralMenu();
	    			}else{
	    				showLateralMenu();
	    			}
	    		});
	    		hideLateralMenu = function(){
	    			$( "#lateralNavbar" ).animate({
					    width: "20px"
					 }, {
					    duration: 500,
					   complete: function() {
					     $(this).removeClass("showLateralMenu");
					    }
					  });
	    		};
	    		showLateralMenu = function(){
	    			$( "#lateralNavbar" ).animate({
					    width: "50px"
					 }, {
					    duration: 500,
					   complete: function() {
					     $(this).addClass("showLateralMenu");
					    }
					  });
	    		}
	    		
	    	}
	    	function initAnchor(){
				//clic en un enlace de la lista
				$('.anchor').on('click touchstart',function(e){
					e.preventDefault();					
					var strAnchor=$(this).attr('href');
					if($(this).data("href")){
						strAnchor=$(this).data("href");
					}
					$('body,html').stop(true,true).animate({
						scrollTop: $("[data-anchor='"+strAnchor+"']").first().offset().top -80
					},1000);
				});

	    	}
	    	
	    	$(document).ready(function(){
	    		initToTop();								
				initLateralMenu();
				initAnchor();
				//colocar mismo alto todos los quickInfo
				var maxHeigth=0;
				$(".quickInfo").each(function(){
					if($(this).outerHeight(false) > maxHeigth){
						maxHeigth= $(this).outerHeight(false);
					}
				});
				if(maxHeigth>290){
					maxHeigth = 290;
				}
				$(".quickInfo").each(function(){					
					$(this).css("height", maxHeigth+"px");
				});
			});